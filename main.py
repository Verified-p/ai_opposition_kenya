from agents.opposition_agent import (
    analyze_government_news,
    citizen_question,
    policy_recommendation,
    root_agent
)
import json  # ✅ Added import for saving analysis

def main():
    print("\nType 'start' to activate Opposition AI Kenya:")
    command = input("> ").strip().lower()

    if command == "start":
        print("\n🇰🇪 Digital Opposition Kenya is running...\n")

        # 🔹 Step 1: Automatically fetch and analyze government news
        print("📡 Fetching and analyzing latest government news...\n")
        analysis_result = analyze_government_news()
        print("\n=== 📰 Opposition AI Analysis ===\n")

        if analysis_result.get("analyses"):
            for i, art in enumerate(analysis_result["analyses"], 1):
                print(f"🗞️  Article {i}: {art['title']}\n")
                print(f"{art['analysis']}\n")
                print(f"🔗 Source: {art['source']}\n")
                print("=" * 80)

            # ✅ Save analyses to a JSON file for record keeping
            try:
                with open("analysis_output.json", "w", encoding="utf-8") as f:
                    json.dump(analysis_result, f, indent=4, ensure_ascii=False)
                print("\n💾 All analyses have been saved to 'analysis_output.json'\n")
            except Exception as e:
                print(f"⚠️ Error saving analyses: {e}\n")
        else:
            print("⚠️ No analyses available at the moment.\n")

    # 🔹 Step 2: Allow citizen interaction (Q&A)
    while True:
        question = input("\nAsk about current government matters (or type 'exit'): ").strip()
        if question.lower() in ["exit", "quit"]:
            print("\n👋 Opposition AI Kenya signing off. Stay informed, stay empowered!")
            break

        if question:
            print("\n🤖 Processing your question...\n")
            response = citizen_question(question)
            print("💬 Opposition AI Response:\n")
            print(response.get("answer", "⚠️ No response generated.\n"))
            print("-" * 80)

if __name__ == "__main__":
    main()
