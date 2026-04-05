# 🇲🇦 Darija AI Immersion System

An AI-powered web app that teaches Moroccan Darija through real conversations, quizzes, and cultural insights.

Built by **Team DarijaAI** — Oussama Tarchi · Ali Zouine · Taha Rajel

---

## 🚀 Features
- 🤖 **AI Chat** — Ask anything, get answers in English with real Darija expressions
- 🧠 **Quiz Mode** — AI-generated multiple choice questions to test your Darija
- 📊 **Session Summary** — Personalized recap of everything you learned
- 🔐 **Authentication** — Register/Login system
- 📚 **Knowledge Base** — JSON database of 500+ Darija words and cultural tips

---

## 🛠️ Tech Stack
- Python + CrewAI (multi-agent AI)
- Groq API (llama-3.1-8b-instant)
- Flask (web server)
- HTML / CSS / JavaScript (frontend)

---

## ⚙️ How to Run

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/DarijaAgent_Project.git
cd DarijaAgent_Project
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_key_here
```
Get a free key at: https://console.groq.com

### 5. Run the app
```bash
python app.py
```

### 6. Open in browser
```
http://localhost:5000
```

---

## 🗂️ Project Structure
```
DarijaAgent_Project/
├── static/
│   ├── index.html      # Landing page
│   ├── login.html      # Auth page
│   ├── menu.html       # Mode selection
│   ├── chat.html       # AI chat interface
│   ├── quiz.html       # Quiz interface
│   └── summary.html    # Session summary
├── data/
│   └── darija_knowledge.json  # Darija database
├── auth/
│   └── users.json      # User accounts
├── agents.py           # CrewAI agents
├── tasks.py            # CrewAI tasks
├── app.py              # Flask server
├── main.py             # Terminal version
├── tools.py            # Web scraper tool
├── .env                # API keys (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔑 Demo Account
- Email: `demo@darija.ai`
- Password: `demo1234`