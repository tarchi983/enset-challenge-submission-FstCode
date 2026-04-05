'''from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Crew, Process
from agents import darija_expert_agent, cultural_coach_agent
from tasks import create_tasks

app = Flask(__name__, static_folder='static')
CORS(app)


def run_darija_chat(user_question: str) -> str:
    answer_task, tip_task = create_tasks(user_question)
    crew = Crew(
        agents=[darija_expert_agent, cultural_coach_agent],
        tasks=[answer_task, tip_task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    return str(result)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        response = run_darija_chat(user_message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)'''


import os
import json
import time
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from crewai import Crew, Process
from agents import darija_expert_agent, cultural_coach_agent, quiz_agent, summary_agent
from tasks import create_chat_tasks, create_quiz_task, create_summary_task
from functools import wraps


# ─── Retry Helper for Rate Limits ─────────────────────────────────────────────
def run_crew_with_retry(crew, max_retries=2, base_delay=0.5):
    """Execute crew.kickoff() with minimal retry for rate limits (optimized)."""
    for attempt in range(max_retries):
        try:
            return crew.kickoff()
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    # Much shorter waits since we reduced token usage dramatically
                    wait_time = base_delay * (attempt + 1)
                    print(f"Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            raise  # Re-raise if not a rate limit error or max retries reached

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

USERS_FILE = "auth/users.json"


# ─── Helpers ──────────────────────────────────────────────────────────────────
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Auth Routes ──────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    users = load_users()
    user = next((u for u in users["users"]
                 if u["email"].lower() == email and u["password"] == password), None)

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    session["user"] = {"id": user["id"], "name": user["name"], "email": user["email"]}
    return jsonify({"message": "Login successful", "name": user["name"]})


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    users = load_users()
    if any(u["email"].lower() == email for u in users["users"]):
        return jsonify({"error": "Email already registered"}), 409

    new_user = {
        "id": len(users["users"]) + 1,
        "name": name,
        "email": email,
        "password": password
    }
    users["users"].append(new_user)
    save_users(users)

    session["user"] = {"id": new_user["id"], "name": name, "email": email}
    return jsonify({"message": "Registered successfully", "name": name})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/me")
def me():
    if "user" in session:
        return jsonify(session["user"])
    return jsonify({"error": "Not logged in"}), 401


# ─── Chat Route (Guest Access) ────────────────────────────────────────────────
@app.route("/api/guest", methods=["POST"])
def guest_access():
    """Allow guest access without authentication"""
    # Simply allow guest to proceed to menu
    session["user"] = {"id": "guest", "name": "Guest", "email": "guest@darija.ai"}
    return jsonify({"message": "Guest access granted"})


# ─── Chat Route (Authenticated Users) ──────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    try:
        answer_task, tip_task = create_chat_tasks(message)
        crew = Crew(
            agents=[darija_expert_agent, cultural_coach_agent],
            tasks=[answer_task, tip_task],
            process=Process.sequential,
            verbose=False,
        )
        result = run_crew_with_retry(crew)
        return jsonify({"response": str(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Quiz Route ───────────────────────────────────────────────────────────────
@app.route("/api/quiz", methods=["POST"])
@login_required
def quiz():
    data = request.get_json()
    topic = data.get("topic", "general Darija expressions")

    try:
        task = create_quiz_task(topic)
        crew = Crew(
            agents=[quiz_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        result = str(run_crew_with_retry(crew)).strip()

        # Clean and parse JSON
        if "```" in result:
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        result = result.strip()

        quiz_data = json.loads(result)
        return jsonify(quiz_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Summary Route ────────────────────────────────────────────────────────────
@app.route("/api/summary", methods=["POST"])
@login_required
def summary():
    data = request.get_json()
    history = data.get("history", "")
    if not history:
        return jsonify({"error": "No conversation history provided"}), 400

    try:
        task = create_summary_task(history)
        crew = Crew(
            agents=[summary_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        result = run_crew_with_retry(crew)
        return jsonify({"summary": str(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Page Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def landing():
    return app.send_static_file("index.html")

@app.route("/login")
def login_page():
    return app.send_static_file("login.html")

@app.route("/menu")
def menu_page():
    return app.send_static_file("menu.html")

@app.route("/chat")
def chat_page():
    return app.send_static_file("chat.html")

@app.route("/quiz")
def quiz_page():
    return app.send_static_file("quiz.html")

@app.route("/summary")
def summary_page():
    return app.send_static_file("summary.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)