---
title: Darija AI
emoji: 🚀
colorFrom: red
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# 🇲🇦 Darija AI Immersion System

An AI-powered web app that teaches Moroccan Darija through real conversations, quizzes, and cultural insights.

Built by **Team DarijaAI** — Oussama Tarchi · Ali Zouine · Taha Rajel

---

## 🚀 Features
- 🤖 **AI Chat** — Ask anything, get answers in English with real Darija expressions.
- 🧠 **Quiz Mode** — AI-generated multiple choice questions to test your Darija.
- 📊 **Session Summary** — Personalized, lightning-fast recap of everything you learned.
- 🔐 **Advanced Authentication** — Secure login with robust password policies, Server-side MX email checking, and seamless **Google OAuth Integration**.
- 📚 **Knowledge Base** — JSON database of 500+ Darija words and cultural tips tightly integrated with the agent to prevent hallucinations.
- 🌐 **Hugging Face Ready** — Fully configured to be deployed as a Docker Space on Hugging Face.

---

## 🛠️ Tech Stack
- **Python + CrewAI** (multi-agent AI structure)
- **OpenRouter API** powering the highly capable **`google/gemma-4-31b-it`** model for high-accuracy local dialects.
- **Flask** (backend web server) + **MongoDB Atlas** (Cloud Database with local JSON fallback)
- **HTML / Vanilla CSS / JavaScript** (premium dark-mode frontend)

---

## ⚙️ How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/tarchi983/DarijaAgent_Project.git
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
Create a `.env` file in the project root containing your API key:
```env
OPENROUTER_API_KEY=your_openrouter_key_here
```
*(Get your key at: https://openrouter.ai/)*

### 5. Run the app
```bash
python app.py
```

### 6. Open in browser
Navigate to:
```
http://localhost:7860
```
*(Note: The server defaults to port 7860 for strict Hugging Face compatibility)*

---

## 🐳 Hugging Face Deployment
This repository is configured out-of-the-box for **Hugging Face Spaces**. 
It includes the required `Dockerfile` and the metadata configuration block at the very top of this `README.md`. 
To deploy, simply link your GitHub repository to a new Hugging Face Space and choose **Docker** as your SDK.

---

## 🗂️ Project Structure
```text
DarijaAgent_Project/
├── static/
│   ├── index.html      # Landing page
│   ├── login.html      # Glassmorphic auth page with Google OAuth
│   ├── menu.html       # Mode selection
│   ├── chat.html       # AI chat interface
│   ├── quiz.html       # Quiz interface
│   └── summary.html    # Session summary
├── data/
│   └── darija_knowledge.json  # Anti-hallucination Darija database
├── auth/
│   └── users.json      # Local fallback for user accounts
├── agents.py           # CrewAI customized agents targeting Gemma
├── tasks.py            # CrewAI instructional tasks
├── app.py              # Flask server and optimized API endpoints
├── main.py             # Terminal version
├── tools.py            # Web scraper integrations
├── Dockerfile          # Configuration for Hugging Face Spaces integration
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```

---

## 🔑 Demo Account
- **Email:** `demo@darija.ai`
- **Password:** `demo1234`