import os
import json
import time
import re
import bleach
import dns.resolver
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from crewai import Crew, Process
from agents import darija_expert_agent, cultural_coach_agent, quiz_agent, summary_agent
from tasks import create_chat_tasks, create_quiz_task, create_summary_task
from functools import wraps
from pymongo import MongoClient
from bson import ObjectId
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# ─── MongoDB Setup ────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://oussamatr05_db_user:Tqk0S2K0iPLpmaLK@cluster0.gzldmqv.mongodb.net/?appName=Cluster0")

mongo_available = False
client = None
users_collection = None
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['darija_ai_db']
    users_collection = db['users']
    client.admin.command('ping')
    mongo_available = True
    print("[OK] Connected to MongoDB Atlas successfully")
except Exception as e:
    print(f"[ERROR] MongoDB Connection Error: {e}")
    print("  -> Falling back to local auth/users.json")

# ─── Step Counter ─────────────────────────────────────────────────────────────
_step_counter = 0
def log_step(message):
    global _step_counter
    _step_counter += 1
    print(f"\n  >> STEP {_step_counter}: {message}")

# ─── Retry Helper ─────────────────────────────────────────────────────────────
def run_crew_with_retry(crew, max_retries=2, base_delay=0.5):
    for attempt in range(max_retries):
        try:
            return crew.kickoff()
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (attempt + 1)
                    print(f"Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            raise

# ─── Local JSON Helpers (fallback) ───────────────────────────────────────────
USERS_FILE = "auth/users.json"

def load_users_json():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users_json(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── Auth Decorator ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ─── Sanitization Helper ─────────────────────────────────────────────────────
def sanitize(value):
    """Strip HTML tags, escape dangerous content, prevent XSS & injection."""
    if not isinstance(value, str):
        return ""
    # Use bleach to strip all HTML tags
    cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)
    # Remove common SQL injection patterns
    sql_patterns = [
        r"(--|;|\/\*|\*\/|xp_|DROP\s+TABLE|SELECT\s+\*|INSERT\s+INTO|DELETE\s+FROM|UNION\s+SELECT)",
    ]
    for pattern in sql_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

# ─── Disposable Email Domain Blocklist ───────────────────────────────────────
DISPOSABLE_DOMAINS = {
    "10minutemail.com", "10minutemail.net", "10minutemail.org",
    "tempmail.com", "tempmail.net", "tempmail.org", "temp-mail.org",
    "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
    "guerrillamail.de", "guerrillamail.biz", "guerrillamail.info",
    "mailinator.com", "mailinator.net", "mailinator.org",
    "throwam.com", "throwaway.email", "throwam.com",
    "yopmail.com", "yopmail.fr", "yopmail.net",
    "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "guerrillamail.us", "spam4.me",
    "trashmail.com", "trashmail.me", "trashmail.net",
    "trashmail.at", "trashmail.io", "trashmail.org",
    "dispostable.com", "mailnull.com", "spamgourmet.com",
    "spamgourmet.net", "spamgourmet.org",
    "maildrop.cc", "harakirimail.com", "spamfree24.org",
    "spamfree24.de", "spamfree24.eu", "spamfree24.info",
    "spamfree24.net", "mintemail.com", "filzmail.com",
    "spammotel.com", "mt2014.com", "mt2015.com",
    "fakemail.fr", "fakemail.net", "tempemail.net",
    "tempinbox.com", "tempinbox.net",
    "fakeinbox.com", "fakeinbox.net",
    "mailexpire.com", "mailexpire.net",
    "spamcorpse.com", "deadaddress.com",
    "discard.email", "discardmail.com", "discardmail.de",
    "emailondeck.com", "jetable.fr", "jetable.net",
    "jetable.org", "anoxa.de", "noclickemail.com",
    "spamherelots.com", "spamhereplease.com",
    "mailnew.com", "mailnew.net", "thankyou2010.com",
    "thanksnospam.com", "thankyou2010.com",
    "tmailinator.com", "mailtemp.info", "inboxproxy.com",
    "wegwerfmail.de", "wegwerfmail.net", "wegwerfmail.org",
    "sogetthis.com", "suremail.info", "spambox.us",
    "spambox.info", "spamfree.eu", "spam.la",
    "receiveee.com", "getonemail.com", "net-c.com",
    "netc.eu", "speed.1s.fr", "anonymstermail.com",
    "anonymail.dk", "mailseal.de",
    "nowmymail.com", "hide.biz", "e4ward.com",
    "baxomale.ht.cx", "courrieltemporaire.com",
    "despam.it", "discardmail.de", "dodgeit.com",
    "dontreg.com", "dontsendmespam.de", "dump-email.info",
    "example.com", "fakeemailaddress.com", "filzmail.de",
    "gishpuppy.com", "gotmail.net", "guerillamail.biz",
    "h8s.org", "hmamail.com", "hulapla.de", "ieatspam.eu",
    "ieatspam.info", "jetable.com", "junk.to", "kasmail.com",
    "klassmaster.com", "klassmaster.net", "kurzepost.de",
    "lhsdv.com", "lifebyfood.com", "link2mail.net",
    "lol.ovpn.to", "lookugly.com", "lortemail.dk",
    "mailin8r.com", "mailme.lv", "mailme24.com",
    "mailmetrash.com", "mailmoat.com", "mailnew.com",
    "mailscrap.com", "mailsiphon.com", "mailzilla.org",
    "mbx.cc", "mega.zik.dj", "meltmail.com",
    "mierdamail.com", "migumail.com", "moncourrier.fr",
    "monemail.fr", "monmail.fr", "nobulk.com",
    "noclickemail.com", "nogmailspam.info", "nomail.pw",
    "nospam.ze.tc", "nospamfor.us", "nospamthanks.info",
    "nus.edu.sg", "objectmail.com", "onewaymail.com",
    "ownmail.net", "parlimentgardens.net", "pasta69.win",
    "pookmail.com", "privy-mail.com", "proxymail.eu",
    "quickinbox.com", "rcpt.at", "rppkn.com",
    "rtrtr.com", "s0ny.net", "safe-mail.net",
    "safersignup.de", "sandelf.de", "saynotospams.com",
    "sendspamhere.com", "sharklasers.com", "shiftmail.com",
    "shitmail.de", "sibmail.com", "skeefmail.com",
    "slopsbox.com", "smellfear.com", "snkmail.com",
    "sofimail.com", "spam.su", "spamavert.com",
    "spamcon.org", "spamcowboy.com", "spamcowboy.net",
    "spamcowboy.org", "spamdecoy.net", "spamer.in",
    "spamfree.eu", "spamgoes.in", "spaminator.de",
    "spamkill.info", "spaml.com", "spaml.de",
    "spamminister.com", "spamspot.com", "spamstack.net",
    "spamthisplease.com", "ssoia.com", "supergreatmail.com",
    "supermailer.jp", "superstachel.de", "suremail.info",
    "svk.jp", "sweetxxx.de", "tafmail.com",
    "tagyourself.com", "talkinator.com", "teewars.org",
    "telecomix.pl", "tempalias.com", "tempe-mail.com",
    "tempemailaddress.com", "temporaryforwarding.com",
    "temporaryinbox.com", "tempthe.net",
    "thankyou2010.com", "thecloudindex.com",
    "tmail.com", "tmailinator.com", "toiea.com",
    "uggsrock.com", "upliftnow.com", "uplipht.com",
    "uroid.com", "usefulmailing.com", "venompen.com",
    "viditag.com", "viewcastmedia.com", "vomoto.com",
    "warnme.de", "wegas.ru", "whyspam.me",
    "wilemail.com", "willselfdestruct.com", "wuzupmail.net",
    "xagloo.com", "xemaps.com", "xents.com",
    "xmaily.com", "xoxy.net", "yapped.net",
    "yeah.net", "yep.it", "yogamaven.com",
    "yopmail.biz", "yopmail.com", "youmailr.com",
    "z1p.biz", "zebins.com", "zebins.eu",
    "zehnminuten.de", "zehnminutenmail.de",
    "zippymail.info", "zoaxe.com", "zoemail.net",
    "zoemail.org", "zomg.info"
}

# ─── Strong Password Validator ────────────────────────────────────────────────
PASSWORD_RE = {
    "length":  re.compile(r".{8,}"),
    "upper":   re.compile(r"[A-Z]"),
    "lower":   re.compile(r"[a-z]"),
    "digit":   re.compile(r"\d"),
    "symbol":  re.compile(r"[!@#$%^&*()\-_=+\[\]{}|;:',.<>?/\\`~\"]+"),
}

def validate_password_strength(password):
    """Returns (is_valid, list_of_failing_rules)."""
    fails = [name for name, pat in PASSWORD_RE.items() if not pat.search(password)]
    return (len(fails) == 0, fails)

# ─── MX Record Check ──────────────────────────────────────────────────────────
def check_mx_record(domain):
    """Returns True if the domain has at least one MX record."""
    try:
        records = dns.resolver.resolve(domain, 'MX', lifetime=5)
        return len(records) > 0
    except Exception:
        return False

# ────────────────────────────────────────────────────────────────────────────────────
# ─── NEW: Email Validation Endpoint ──────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────────────
@app.route("/api/validate-email", methods=["POST"])
def validate_email():
    """
    Real-time email validation:
      1. Basic format check
      2. Disposable domain check
      3. DNS MX record check
    """
    data = request.get_json()
    raw_email = sanitize(data.get("email", ""))

    # 1. Basic format
    EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    if not EMAIL_RE.match(raw_email):
        return jsonify({"valid": False, "reason": "Invalid email format."}), 200

    domain = raw_email.split("@")[1].lower()

    # 2. Disposable domain check
    if domain in DISPOSABLE_DOMAINS:
        return jsonify({
            "valid": False,
            "reason": f"Disposable/temporary email addresses are not allowed. Please use a real email."
        }), 200

    # 3. MX record check
    log_step(f"Checking MX records for domain: {domain}")
    has_mx = check_mx_record(domain)
    if not has_mx:
        return jsonify({
            "valid": False,
            "reason": f"The domain '{domain}' has no mail server. Please use a real email address."
        }), 200

    return jsonify({"valid": True, "reason": "Email address is valid."}), 200


# ────────────────────────────────────────────────────────────────────────────────────
# ─── NEW: Google OAuth Endpoint ──────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────────────
@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    """
    Verify Google ID token using Google's tokeninfo endpoint (no library cert-fetch needed).
    Frontend sends: { credential: "<google_id_token>" }
    """
    import urllib.request as urlreq
    import urllib.error  as urlerr

    data = request.get_json()
    credential = data.get("credential", "")

    if not credential:
        return jsonify({"error": "No credential provided"}), 400

    if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "YOUR_GOOGLE_CLIENT_ID_HERE":
        return jsonify({"error": "Google OAuth is not configured on this server."}), 503

    try:
        # ── Step 1: Verify via Google's tokeninfo endpoint ─────────────────
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        with urlreq.urlopen(url, timeout=10) as resp:
            id_info = json.loads(resp.read().decode())

        # ── Step 2: Confirm the token was issued for OUR app ───────────────
        token_aud = id_info.get("aud", "")
        if token_aud != GOOGLE_CLIENT_ID:
            log_step(f"Token audience mismatch: got '{token_aud}'")
            return jsonify({"error": "Token not issued for this application."}), 401

        # ── Step 3: Confirm email is verified ──────────────────────────────
        if id_info.get("email_verified") not in (True, "true"):
            return jsonify({"error": "Google email is not verified."}), 401

        google_email = id_info.get("email", "").lower()
        google_name  = id_info.get("name", "Google User")
        google_sub   = id_info.get("sub", "")
        avatar_url   = id_info.get("picture", "")

        if not google_email:
            return jsonify({"error": "Could not retrieve email from Google."}), 400

        log_step(f"Google OAuth login for: {google_email}")

        if mongo_available:
            user = users_collection.find_one({"email": google_email})
            if not user:
                # Auto-create account for new Google users
                new_user = {
                    "name": google_name,
                    "email": google_email,
                    "password": None,
                    "auth_provider": "google",
                    "google_sub": google_sub,
                    "avatar": avatar_url,
                    "created_at": time.time()
                }
                result = users_collection.insert_one(new_user)
                user_id = str(result.inserted_id)
                log_step(f"New Google user created: {google_name}")
            else:
                user_id = str(user["_id"])
                log_step(f"Existing Google user found: {google_name}")
        else:
            # Fallback: local JSON
            users = load_users_json()
            user = next((u for u in users["users"] if u["email"].lower() == google_email), None)
            if not user:
                new_user = {
                    "id": len(users["users"]) + 1,
                    "name": google_name,
                    "email": google_email,
                    "password": None,
                    "auth_provider": "google",
                    "google_sub": google_sub,
                    "avatar": avatar_url
                }
                users["users"].append(new_user)
                save_users_json(users)
                user_id = str(new_user["id"])
            else:
                user_id = str(user["id"])

        session["user"] = {
            "id": user_id,
            "name": google_name,
            "email": google_email,
            "avatar": avatar_url,
            "auth_provider": "google"
        }
        return jsonify({"message": "Google login successful", "name": google_name})

    except urlerr.HTTPError as e:
        body = e.read().decode()
        log_step(f"Google tokeninfo rejection: {e.code} — {body}")
        return jsonify({"error": "Invalid or expired Google token. Please try again."}), 401
    except Exception as e:
        log_step(f"Google auth error: {e}")
        return jsonify({"error": "Google authentication failed. Please try again."}), 500


# ─── Auth Routes (Login / Register / Logout / Me) ────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email    = sanitize(data.get("email", "")).lower()
    password = sanitize(data.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    if mongo_available:
        log_step("User attempting to login via MongoDB")
        user = users_collection.find_one({"email": email, "password": password})
        if not user:
            log_step("Login failed - Invalid credentials")
            return jsonify({"error": "Invalid email or password."}), 401
        session["user"] = {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}
        log_step(f"Login successful: {user['name']}")
        return jsonify({"message": "Login successful", "name": user["name"]})
    else:
        log_step("User attempting to login via local JSON (MongoDB offline)")
        users = load_users_json()
        user = next((u for u in users["users"] if u["email"].lower() == email and u["password"] == password), None)
        if not user:
            return jsonify({"error": "Invalid email or password."}), 401
        session["user"] = {"id": str(user["id"]), "name": user["name"], "email": user["email"]}
        log_step(f"Login successful: {user['name']}")
        return jsonify({"message": "Login successful", "name": user["name"]})


@app.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json()
    name     = sanitize(data.get("name", ""))
    email    = sanitize(data.get("email", "")).lower()
    password = data.get("password", "")  # Don't sanitize password value itself

    # ── Server-side validations ───────────────────────────────────────────────
    if not name or not email or not password:
        return jsonify({"error": "All fields are required."}), 400

    EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email format."}), 400

    domain = email.split("@")[1]
    if domain in DISPOSABLE_DOMAINS:
        return jsonify({"error": "Disposable email addresses are not permitted."}), 400

    # Server-side MX check
    if not check_mx_record(domain):
        return jsonify({"error": f"The email domain '{domain}' has no mail server."}), 400

    # Strong password policy
    is_strong, fails = validate_password_strength(password)
    if not is_strong:
        rule_labels = {
            "length": "at least 8 characters",
            "upper":  "one uppercase letter",
            "lower":  "one lowercase letter",
            "digit":  "one number",
            "symbol": "one special character (!@#$%...)"
        }
        msgs = [rule_labels[r] for r in fails]
        return jsonify({"error": f"Weak password. Must contain: {', '.join(msgs)}."}), 400

    log_step(f"Attempting to register: {email}")

    if mongo_available:
        if users_collection.find_one({"email": email}):
            return jsonify({"error": "Email already registered."}), 409
        new_user = {
            "name": name,
            "email": email,
            "password": password,
            "auth_provider": "manual",
            "created_at": time.time()
        }
        result = users_collection.insert_one(new_user)
        session["user"] = {"id": str(result.inserted_id), "name": name, "email": email}
        log_step(f"Registration successful: {name}")
        return jsonify({"message": "Registered successfully", "name": name})
    else:
        users = load_users_json()
        if any(u["email"].lower() == email for u in users["users"]):
            return jsonify({"error": "Email already registered."}), 409
        new_user = {
            "id": len(users["users"]) + 1,
            "name": name,
            "email": email,
            "password": password,
            "auth_provider": "manual"
        }
        users["users"].append(new_user)
        save_users_json(users)
        session["user"] = {"id": str(new_user["id"]), "name": name, "email": email}
        log_step(f"Registration successful (local): {name}")
        return jsonify({"message": "Registered successfully", "name": name})


@app.route("/api/logout", methods=["POST"])
def logout():
    log_step("User logging out")
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/me")
def me():
    if "user" in session:
        return jsonify(session["user"])
    return jsonify({"error": "Not logged in"}), 401


# ─── Guest Access ─────────────────────────────────────────────────────────────
@app.route("/api/guest", methods=["POST"])
def guest_access():
    session["user"] = {"id": "guest", "name": "Guest", "email": "guest@darija.ai"}
    return jsonify({"message": "Guest access granted"})


# ─── Chat, Quiz, Summary Routes ───────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    log_step("Chat request received")
    data = request.get_json()
    message = sanitize(data.get("message", ""))
    if not message:
        return jsonify({"error": "Empty message"}), 400
    try:
        # ── Direct OpenRouter API call — bypasses CrewAI's 500-1000 token overhead ──
        import openai as _openai
        from agents import lookup_darija
        kb_match = lookup_darija(message)
        kb_note  = f"\nKB fact: {kb_match}" if kb_match else ""

        _client = _openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        completion = _client.chat.completions.create(
            model="google/gemma-4-31b-it",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a friendly Moroccan Darija expert. "
                        "Answer in English, weave in 2-3 Darija words with translations in parentheses. "
                        "If a KB fact is given, use it. End every reply with 'Pro Cultural Tip:' and one sentence."
                        f"\n\nUser question: {message}{kb_note}"
                    )
                }
            ],
            max_tokens=400,
            temperature=0.7,
        )
        response = completion.choices[0].message.content
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/quiz", methods=["POST"])
@login_required
def quiz():
    log_step("Quiz request received")
    data  = request.get_json()
    topic = sanitize(data.get("topic", "general Darija expressions"))
    try:
        # Quiz options are 100% KB-built in create_quiz_task — no LLM needed.
        # Return the pre-built JSON directly for instant response.
        task   = create_quiz_task(topic)
        parsed = json.loads(task.expected_output)
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/summary", methods=["POST"])
@login_required
def summary():
    log_step("Summary request received")
    data    = request.get_json()
    history = sanitize(data.get("history", ""))
    if not history:
        return jsonify({"error": "No history provided"}), 400
    try:
        # ── Direct OpenRouter API call — skips CrewAI overhead for fast response ──
        import openai as _openai
        _client = _openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        completion = _client.chat.completions.create(
            model="google/gemma-4-31b-it",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are an encouraging Moroccan language teacher.\n"
                        "Here is the full conversation the user had:\n\n"
                        f"{history}\n\n"
                        "Write a warm, encouraging summary (200 words max) covering:\n"
                        "1. The Darija words and expressions they encountered\n"
                        "2. The cultural tips they learned\n"
                        "3. A motivational closing message to keep learning"
                    )
                }
            ],
            max_tokens=350,
            temperature=0.6,
        )
        result = completion.choices[0].message.content
        return jsonify({"summary": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Static Page Routes ───────────────────────────────────────────────────────
@app.route("/")
def landing(): return app.send_static_file("index.html")

@app.route("/login")
def login_page(): return app.send_static_file("login.html")

@app.route("/menu")
def menu_page(): return app.send_static_file("menu.html")

@app.route("/chat")
def chat_page(): return app.send_static_file("chat.html")

@app.route("/quiz")
def quiz_page(): return app.send_static_file("quiz.html")

@app.route("/summary")
def summary_page(): return app.send_static_file("summary.html")


if __name__ == "__main__":
    print("\n" + "="*60)
    print(">> STARTING DARIJA AI APPLICATION")
    print("="*60)
    log_step("Flask app initialization starting...")
    log_step("Loading configuration and agents...")
    log_step("Setting up CORS and session management...")
    print("\n" + "="*60)
    port = int(os.environ.get("PORT", 7860))
    print(f"[OK] Server running on: http://localhost:{port}")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)