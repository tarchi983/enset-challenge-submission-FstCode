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













'''from crewai import Task
from agents import darija_expert_agent, cultural_coach_agent


def create_tasks(user_question: str):
    """Creates tasks dynamically based on the user's question."""

    answer_task = Task(
        description=(
            f"The user asked: \"{user_question}\"\n\n"
            "Answer this question in English. "
            "Naturally include 3-5 real Moroccan Darija words or expressions that fit the topic. "
            "For each Darija word/phrase, explain it right after in parentheses like: "
            "labas (Darija: I'm fine / no problem). "
            "Be conversational and warm, like a Moroccan friend explaining things."
        ),
        expected_output=(
            "A friendly English answer to the user's question that naturally includes "
            "3-5 Darija expressions, each explained in parentheses."
        ),
        agent=darija_expert_agent,
    )

    tip_task = Task(
        description=(
            f"The user asked: \"{user_question}\"\n\n"
            "Write ONE 'Pro Cultural Tip' of 2-3 sentences that is directly relevant "
            "to the user's question. Make it practical and easy to remember."
        ),
        expected_output="A Pro Cultural Tip of 2-3 sentences relevant to the user's question.",
        agent=cultural_coach_agent,
        context=[answer_task],
    )
    
    return answer_task, tip_task
'''




from crewai import Task
from agents import (
    darija_expert_agent,
    cultural_coach_agent,
    quiz_agent,
    summary_agent,
)


# ─── Chat Tasks ───────────────────────────────────────────────────────────────
def create_chat_tasks(user_question: str):
    answer_task = Task(
        description=(
            f'The user asked: "{user_question}"\n\n'
            "Answer in English with 3-5 Darija words/expressions explained in parentheses. "
            "Be warm and conversational like a Moroccan friend."
        ),
        expected_output="Friendly English answer with 3-5 Darija expressions explained.",
        agent=darija_expert_agent,
    )

    tip_task = Task(
        description=(
            f'The user asked: "{user_question}"\n\n'
            "Write ONE Pro Cultural Tip of 2-3 sentences directly related to the question."
        ),
        expected_output="A Pro Cultural Tip of 2-3 sentences.",
        agent=cultural_coach_agent,
        context=[answer_task],
    )

    return answer_task, tip_task


# ─── Quiz Task ────────────────────────────────────────────────────────────────
def create_quiz_task(topic: str = "general Darija"):
    return Task(
        description=(
            f"Create ONE multiple-choice quiz question about: {topic}.\n"
            "Return ONLY this JSON format, no extra text:\n"
            '{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A"}'
        ),
        expected_output='A JSON object with keys: question, options (list of 4), answer (letter).',
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

