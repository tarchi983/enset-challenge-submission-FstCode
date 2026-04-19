"""import os
from dotenv import load_dotenv
from crewai import Agent
from crewai.tools import BaseTool
from pydantic import Field
from tools import scrape_darija_content

load_dotenv()


class MoroccanScraperTool(BaseTool):
    name: str = "Moroccan Web Scraper"
    description: str = (
        "Useful for fetching real Darija text from Moroccan websites. "
        "Input should be a URL string."
    )

    def _run(self, url: str) -> str:
        return scrape_darija_content(url)


scraping_tool = MoroccanScraperTool()

scraper_agent = Agent(
    role='Moroccan Web Explorer',
    goal='Navigate Moroccan websites to find authentic Darija phrases',
    backstory='You are a specialist in Moroccan digital slang...',
    tools=[scraping_tool],
    llm="llama-3.3-70b-versatile",
    verbose=True,
    allow_delegation=False
)

linguist_agent = Agent(
    role='Darija Linguist Expert',
    goal='Analyze Darija phrases and explain them for foreigners',
    backstory='You are a master of Moroccan linguistics...',
    llm="llama-3.3-70b-versatile",
    verbose=True,
    allow_delegation=False
)

coach_agent = Agent(
    role='Darija Language Coach',
    goal='Create interactive lessons based on real Darija',
    backstory='You are a friendly teacher...',
    llm="llama-3.3-70b-versatile",
    verbose=True,
    allow_delegation=True
)"""

"""import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from crewai.tools import BaseTool
from tools import scrape_darija_content

load_dotenv()

llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

class MoroccanScraperTool(BaseTool):
    name: str = "Moroccan Web Scraper"
    description: str = (
        "Fetches text content from a Moroccan website URL. "
        "Input must be a full URL string like 'https://www.goud.ma/topics' and 'https://www.loecsen.com/fr/cours-arabe-marocain' and 'https://www.kamus.ma/' . "
        "Use ONLY this tool. Do NOT use any other tool or search engine."
    )

    def _run(self, url: str) -> str:
        return scrape_darija_content(url)

scraping_tool = MoroccanScraperTool()

scraper_agent = Agent(
    role='Moroccan Web Explorer',
    goal='Use ONLY the Moroccan Web Scraper tool to extract Arabic text from https://www.goud.ma/topics and https://www.loecsen.com/fr/cours-arabe-marocain and https://www.kamus.ma. Do not use any search engine or other tools.',
    backstory=(
        'You are a specialist in Moroccan digital content. '
        'You have exactly ONE tool available: the Moroccan Web Scraper. '
        'You MUST use it with the URL https://www.goud.ma/topics and https://www.loecsen.com/fr/cours-arabe-marocain and https://www.kamus.ma and return what it gives you. '
        'Never call brave_search or any other tool. Never search the web.'
    ),
    tools=[scraping_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

linguist_agent = Agent(
    role='Darija Linguist Expert',
    goal='Analyze Arabic/Darija phrases and explain them clearly for foreigners',
    backstory='You are a master of Moroccan linguistics with no tools. You only read and analyze text.',
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

coach_agent = Agent(    
    role='Darija Language Coach',
    goal='Create a fun role-play dialogue and cultural tip based on the analysis',
    backstory='You are a friendly Moroccan language teacher with no tools. You only write dialogues.',
    llm=llm,
    verbose=True,
    allow_delegation=False,
)"""





"""import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Agent 1: Answers the user's question in English with Darija expressions woven in
darija_expert_agent = Agent(
    role='Darija Language Expert',
    goal=(
        'Answer the user question in English, but naturally include 3-5 real Moroccan Darija '
        'words or expressions relevant to the question. '
        'After each Darija word, immediately explain it in parentheses like: '
        'mzyan (Darija: good/nice). Be warm, friendly, and sound like a real Moroccan.'
    ),
    backstory=(
        'You are a native Moroccan Darija speaker who loves teaching Darija to foreigners. '
        'You ONLY use real, verified Darija words — NEVER invent or guess Darija words. '
        'If unsure about a word, use a known one instead. '
        'Real verified Darija vocabulary you can use: '
        'mrhba (welcome), labas (fine/how are you), shukran (thanks), '
        'bghit (I want), wash (question marker), 3ajib (weird/amazing), '
        'ghrib (strange/unusual), zwina (beautiful), mzyan (good/nice), '
        'bzzaf (a lot/very much), khouya (my brother), sahbi (my friend), '
        'daba (now), mazal (not yet), walu (nothing), smiya (name), '
        'kifash (how), fayn (where), mnin (from where), '
        'wakha (okay/alright), bslama (goodbye), mshi mushkil (no problem). '
        'You answer in English but sprinkle in these real Darija expressions naturally. '
        'You have NO tools — you answer purely from your knowledge.'
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

# Agent 2: Adds a cultural tip relevant to the user's question
cultural_coach_agent = Agent(
    role='Moroccan Cultural Coach',
    goal=(
        'Give the user one short practical Pro Cultural Tip directly related to their question '
        'to help them understand or navigate Moroccan culture better.'
    ),
    backstory=(
        'You are a friendly Moroccan cultural ambassador. '
        'You give short, memorable, practical tips about Moroccan customs and everyday life. '
        'You have NO tools — you answer purely from your knowledge.'
    ),  
    llm=llm,
    verbose=True,
    allow_delegation=False,
)"""


'''import os
import json
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

# ─── Agent 1: Darija Expert ───────────────────────────────────────────────────
darija_expert_agent = Agent(
    role='Darija Language Expert',
    goal=(
        'Answer the user question in English, naturally including 3-5 real Moroccan Darija '
        'words or expressions. After each Darija word explain it in parentheses like: '
        'mzyan (Darija: good/nice). Be warm and friendly like a real Moroccan.'
    ),
    backstory=(
        'You are a warm Moroccan who loves teaching Darija to foreigners. '
        'You answer in English but always sprinkle in real Darija from your knowledge base. '
        + DARIJA_CONTEXT +
        'You have NO tools — answer purely from your knowledge.'
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

# ─── Agent 2: Cultural Coach ──────────────────────────────────────────────────
cultural_coach_agent = Agent(
    role='Moroccan Cultural Coach',
    goal=(
        'Give the user one short practical Pro Cultural Tip directly related to their question.'
    ),
    backstory=(
        'You are a friendly Moroccan cultural ambassador who gives short memorable tips. '
        + DARIJA_CONTEXT +
        'You have NO tools.'
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

# ─── Agent 3: Quiz Agent ──────────────────────────────────────────────────────
quiz_agent = Agent(
    role='Darija Quiz Master',
    goal=(
        'Create a fun multiple-choice quiz question about Moroccan Darija. '
        'Return ONLY valid JSON in this exact format: '
        '{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A"}'
    ),
    backstory=(
        'You are a fun and engaging Darija quiz master. '
        'You create clear multiple-choice questions to test Darija knowledge. '
        + DARIJA_CONTEXT +
        'IMPORTANT: Always return ONLY the JSON object, nothing else. No extra text.'
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

# ─── Agent 4: Summary Agent ───────────────────────────────────────────────────
summary_agent = Agent(
    role='Learning Summary Expert',
    goal=(
        'Read the full conversation history and write a friendly summary of what '
        'the user learned about Moroccan Darija during the session.'
    ),
    backstory=(
        'You are an encouraging Moroccan teacher. '
        'You review chat history and highlight the Darija words, expressions, and cultural '
        'tips the user encountered. You make them feel proud of what they learned. '
        'You have NO tools.'
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)'''







import os
import re
import json
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

# ─── Load Darija Knowledge Base ───────────────────────────────────────────────
with open("data/darija_knowledge.json", "r", encoding="utf-8") as f:
    DARIJA_KB = json.load(f)

# Build a flat lookup list from ALL categories for fast search
_ALL_ENTRIES = []
for _cat, _items in DARIJA_KB.items():
    if isinstance(_items, list):
        for _item in _items:
            if isinstance(_item, dict) and "darija" in _item:
                _item["_category"] = _cat
                _ALL_ENTRIES.append(_item)

def lookup_darija(query: str) -> str:
    """
    Search darija_knowledge.json for any entry matching the query word.
    Returns a formatted block of verified data to inject into the task prompt,
    preventing the LLM from hallucinating the meaning.
    Returns empty string if no match found.
    """
    q = query.strip().lower()
    # Strip common question prefixes so "what is the meaning of Ssehd" -> "ssehd"
    q = re.sub(
        r"^(what'?s?|what is|what does|how do you say|translate|define|"
        r"meaning of|the meaning of|translation of|explanation of)\s+",
        "", q, flags=re.IGNORECASE
    ).strip().strip("\"'")

    matches = []
    for entry in _ALL_ENTRIES:
        variants = [v.strip().lower() for v in entry["darija"].split("/")]
        if any(q == v or q in v or v in q for v in variants):
            matches.append(entry)

    if not matches:
        return ""

    # Cap at 1 best match to keep prompt tokens minimal
    m = matches[0]
    return f"  - '{m['darija']}' = '{m['english']}'"



llm = LLM(
    model="openrouter/google/gemma-4-31b-it",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ─── Agent 1: Darija Expert ───────────────────────────────────────────────────
darija_expert_agent = Agent(
    role='Darija Expert',
    goal='Answer questions about Moroccan Darija accurately. Use KB data when provided.',
    backstory=(
        'Moroccan Darija expert. When KB data is in the task, use it exactly — never override it. '
        'Weave real Darija words naturally into your English answers.'
    ),
    llm=llm,
    verbose=False,
    allow_delegation=False,
)

# ─── Agent 2: Cultural Coach ──────────────────────────────────────────────────
cultural_coach_agent = Agent(
    role='Moroccan Cultural Coach',
    goal='Give one short practical cultural tip about Morocco.',
    backstory='Friendly Moroccan cultural guide. Keep tips brief and practical.',
    llm=llm,
    verbose=False,
    allow_delegation=False,
)

# ─── Agent 3: Quiz Agent ──────────────────────────────────────────────────────
quiz_agent = Agent(
    role='Darija Quiz Master',
    goal='Return ONE quiz question as valid JSON only.',
    backstory='Darija quiz creator. Return only valid JSON, no extra text.',
    llm=llm,
    verbose=False,
    allow_delegation=False,
)

# ─── Agent 4: Summary Agent ───────────────────────────────────────────────────
summary_agent = Agent(
    role='Learning Summary Expert',
    goal='Summarize (max 200 words) what the user learned about Darija.',
    backstory='Encouraging Moroccan teacher who summarizes learning sessions warmly.',
    llm=llm,
    verbose=False,
    allow_delegation=False,
)
