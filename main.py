'''from crewai import Crew, Process
from agents import scraper_agent, linguist_agent, coach_agent
from tasks import scrape_task, analyze_task, coach_task

darija_crew = Crew(
    agents=[scraper_agent, linguist_agent, coach_agent],
    tasks=[scrape_task, analyze_task, coach_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("🚀 Starting the Darija AI Immersion System...\n")
    
    result = darija_crew.kickoff()
    
    print("\n" + "="*50)
    print("🎯 FINAL DARIJA LESSON")
    print("="*50 + "\n")
    print(result)l'''


from crewai import Crew, Process
from agents import darija_expert_agent, cultural_coach_agent
from tasks import create_tasks


def run_darija_chat(user_question: str):
    answer_task, tip_task = create_tasks(user_question)

    crew = Crew(
        agents=[darija_expert_agent, cultural_coach_agent],
        tasks=[answer_task, tip_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff()


def main():
    print("=" * 60)
    print("🇲🇦  Welcome to the Darija AI Immersion System!")
    print("Ask anything about Morocco, Moroccan culture, or Darija.")
    print("Type 'exit' or 'quit' to leave.")
    print("=" * 60)

    while True:
        print()
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye", "bslama"):
            print("\n🇲🇦 Bslama! (Goodbye!) Hope you learned some Darija today!\n")
            break

        print("\n⏳ Your Darija expert is thinking...\n")

        try:
            result = run_darija_chat(user_input)
            print("\n" + "=" * 60)
            print("🎯 DARIJA EXPERT ANSWER")
            print("=" * 60)
            print(result)
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ Something went wrong: {e}")
            print("Try asking again in a moment.\n")


if __name__ == "__main__":
    main()