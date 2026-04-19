"""from crewai import Task
from agents import scraper_agent, linguist_agent, coach_agent

scrape_task = Task(
    description=(
        "Use the Moroccan Web Scraper tool with the URL 'https://www.goud.ma/topics' and 'https://www.loecsen.com/fr/cours-arabe-marocain' and 'https://www.kamus.ma'. "
        "Call the tool ONCE with that exact URL. "
        "From the text returned, pick 3 to 5 Arabic sentences. "
        "Do NOT call any other tool. Do NOT search the web. "
        "If the tool returns an error, report that error as your final answer."
    ),
    expected_output="A numbered list of 3-5 Arabic sentences extracted from the website.",
    agent=scraper_agent,
)

analyze_task = Task(    
    description=(
        "Take the Arabic sentences from the scraper. For each sentence: "
        "1. Translate it literally to English. "
        "2. Explain the cultural context or meaning. "
        "3. Break down key grammar or root words. "
        "Format clearly with bold headers and bullet points."
    ),
    expected_output="A structured linguistic breakdown of each sentence with translation, context, and grammar notes.",
    agent=linguist_agent,
    context=[scrape_task],
)

coach_task = Task(
    description=(
        "Based on the linguistic analysis, write a short role-play dialogue "
        "between a foreigner named John and a Moroccan local named Amine. "
        "Use some of the analyzed phrases naturally in the conversation. "
        "End with a 'Pro Cultural Tip' for John."
    ),
    expected_output="A short dialogue between John and Amine, followed by a Pro Cultural Tip.",
    agent=coach_agent,
    context=[analyze_task],
)"""




from crewai import Task
from agents import (
    darija_expert_agent,
    cultural_coach_agent,
    quiz_agent,
    summary_agent,
    lookup_darija,
    DARIJA_KB,
)


# ─── Chat Task ───────────────────────────────────────────────────────────────
def create_chat_tasks(user_question: str):
    """Single LLM call — answer + cultural tip in one response."""
    kb_match = lookup_darija(user_question)
    kb_block = f"\nKB: {kb_match}\n" if kb_match else ""

    return Task(
        description=(
            f'User asked: "{user_question}"{kb_block}\n'
            "Reply in English. Weave in 2-3 Darija words with brief translations in parentheses. "
            "If KB data is shown above, use it for accuracy. "
            "End with: Pro Cultural Tip: (1-2 sentences about Moroccan culture related to the topic)."
        ),
        expected_output="English answer with Darija words and a Pro Cultural Tip.",
        agent=darija_expert_agent,
    )


# ─── Quiz Task ────────────────────────────────────────────────────────────────
def create_quiz_task(topic: str = "general Darija"):
    """
    Builds a quiz question where ALL answer options come directly from
    the verified KB — the LLM never invents Darija words or meanings.

    Strategy:
      1. Pick 1 correct entry from the KB (filtered by topic when possible).
      2. Pick 3 distractor entries from the KB (different english meanings).
      3. Shuffle all 4 into A/B/C/D slots deterministically.
      4. Ask the LLM ONLY to write the question sentence — it is given
         the exact darija word and the exact 4 options to use.
    """
    import random
    from agents import _ALL_ENTRIES

    # ── Topic-aware filtering ──────────────────────────────────────────────────
    TOPIC_CATEGORY_MAP = {
        "darija greetings":          ["greetings_and_politeness", "greetings_and_social"],
        "moroccan food vocabulary":   ["food_and_drink"],
        "darija numbers":            ["numbers"],
        "moroccan cultural customs":  ["slang_and_street_darija", "everyday_phrases_and_idioms"],
        "general darija expressions": None,  # use all
    }
    topic_key = topic.strip().lower()
    relevant_cats = None
    for key, cats in TOPIC_CATEGORY_MAP.items():
        if key in topic_key or topic_key in key:
            relevant_cats = cats
            break

    # Filter entries with valid darija + english fields only
    valid_entries = [
        e for e in _ALL_ENTRIES
        if isinstance(e.get("darija"), str) and isinstance(e.get("english"), str)
        and len(e["darija"]) > 0 and len(e["english"]) > 0
    ]

    if relevant_cats:
        pool = [e for e in valid_entries if e.get("_category") in relevant_cats]
        if len(pool) < 4:
            pool = valid_entries
    else:
        pool = valid_entries

    if len(pool) < 4:
        pool = valid_entries  # ultimate fallback

    # ── Pick correct answer + 3 unique distractors ────────────────────────────
    correct = random.choice(pool)
    distractors_pool = [e for e in pool if e["english"] != correct["english"]]
    distractors = random.sample(distractors_pool, min(3, len(distractors_pool)))
    if len(distractors) < 3:
        extra_pool = [
            e for e in valid_entries
            if e["english"] != correct["english"] and e not in distractors
        ]
        distractors += random.sample(extra_pool, 3 - len(distractors))

    # ── Build the shuffled options list ──────────────────────────────────────
    all_choices = [correct] + distractors
    random.shuffle(all_choices)
    letters = ["A", "B", "C", "D"]
    correct_letter = letters[all_choices.index(correct)]

    # Build the fixed option strings
    options_strs = [
        f'{letters[i]}) {all_choices[i]["english"]}'
        for i in range(4)
    ]
    opts_json = '["' + '", "'.join(options_strs) + '"]'

    correct_darija = correct["darija"].replace('"', '\\"')
    correct_english = correct["english"].replace('"', '\\"')
    question_text = f'What does the Darija word "{correct_darija}" mean in English?'

    # Build the expected output JSON directly (no LLM needed for structure)
    fixed_json = (
        '{"question": "' + question_text.replace('"', '\\"') + '", '
        '"options": ' + opts_json + ', '
        '"answer": "' + correct_letter + '"}'
    )

    return Task(
        description=(
            f"Create a Darija quiz question about: {topic}.\n\n"
            f"The Darija word/phrase is: \"{correct_darija}\"\n"
            f"Its correct English meaning is: \"{correct_english}\"\n"
            f"The correct answer letter is: {correct_letter}\n\n"
            "The four answer choices are FIXED (do NOT change them):\n"
            + "\n".join(f"  {options_strs[i]}" for i in range(4))
            + "\n\n"
            "Return ONLY this exact JSON, no markdown, no extra text:\n"
            + fixed_json
        ),
        expected_output=fixed_json,
        agent=quiz_agent,
    )


# ─── Summary Task ─────────────────────────────────────────────────────────────
def create_summary_task(conversation_history: str):
    return Task(
        description=(
            "Here is the full conversation the user had:\n\n"
            f"{conversation_history}\n\n"
            "Write a warm, encouraging summary (200 words max) of:\n"
            "1. The Darija words and expressions they encountered\n"
            "2. The cultural tips they learned\n"
            "3. A motivational closing message to keep learning"
        ),
        expected_output="A friendly learning summary with Darija words learned and encouragement.",
        agent=summary_agent,
    )
