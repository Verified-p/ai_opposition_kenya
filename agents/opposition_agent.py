import os
import json
import datetime
from typing import Optional
from google import genai
from google.adk.agents import Agent
from dotenv import load_dotenv
import time
import requests
import feedparser
from pathlib import Path

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY not found. Add it in your .env file:\nGEMINI_API_KEY=YOUR_API_KEY_HERE"
    )

# --- Initialize Gemini client ---
client = genai.Client(api_key=GEMINI_API_KEY)

# --- Local cache folder ---
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
NEWS_CACHE_FILE = CACHE_DIR / "news_cache.json"

# --- Helper function: fetch feed using requests ---
def fetch_feed(url: str, retries: int = 3, delay: int = 5) -> Optional[feedparser.FeedParserDict]:
    """Fetch RSS feed using requests with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                timeout=10,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
                    )
                },
                verify=True,  # ✅ ensure SSL verification is on
            )
            if response.status_code == 200:
                return feedparser.parse(response.content)
            else:
                print(f"⚠️ HTTP {response.status_code} for {url}")
        except requests.exceptions.SSLError as ssl_err:
            print(f"⚠️ SSL error for {url}: {ssl_err}")
        except Exception as e:
            print(f"⚠️ Error fetching {url} (attempt {attempt+1}/{retries}): {e}")
        time.sleep(delay)
    print(f"⚠️ Failed to fetch feed after {retries} attempts: {url}")
    return None

# === 1️⃣ Tool: Analyze Government News ===
def analyze_government_news(_: Optional[str] = None) -> dict:
    feeds = [
        "https://www.standardmedia.co.ke/kenya/rss.xml",
        "https://rss.nation.africa/rss.xml",
        "https://www.theeastafrican.co.ke/rss.xml",
        "https://www.kbc.co.ke/feed/",
        "https://www.msn.com/en-xl/feeds/news",
        "https://allafrica.com/tools/headlines/rdf/kenya/headlines.rdf",
        "https://www.bbc.co.uk/feeds/rss/africa.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ]

    articles = []
    for url in feeds:
        feed = fetch_feed(url)
        if feed and feed.entries:
            for entry in feed.entries[:5]:
                articles.append({
                    "title": entry.get("title", "Untitled"),
                    "link": entry.get("link", "No link"),
                    "summary": entry.get("summary", entry.get("description", "No summary available."))
                })

    articles = articles[:15]

    if not articles and NEWS_CACHE_FILE.exists():
        print("⚠️ Using cached news data.")
        with open(NEWS_CACHE_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)

    if not articles:
        print("⚠️ No live feeds found — using fallback article.")
        articles = [{
            "title": "Government launches new affordable housing project",
            "link": "https://example.com/fallback",
            "summary": (
                "The Kenyan government has announced a new affordable housing project "
                "aimed at urban youth and low-income families."
            )
        }]

    with open(NEWS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

    analyses = []
    for art in articles:
        prompt = f"""
You are **Opposition AI Kenya**, a civic digital agent helping citizens analyze government actions.

Analyze this article through 5 lenses:

1️⃣ Checks & Balances – Any misuse of power?
2️⃣ Critique & Challenge – What risks exist?
3️⃣ Citizen Impact – Who benefits or suffers?
4️⃣ Accountability – Are promises or transparency lacking?
5️⃣ Alternative Proposals – Suggest better realistic actions.
                                                 
Article:
Title: {art['title']}
Summary: {art['summary']}
Source: {art['link']}

Be factual, concise, and aware of the Kenyan context.
"""
        try:
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            ai_text = getattr(resp, "text", None) or "⚠️ No analysis generated."
            analyses.append({
                "title": art["title"],
                "analysis": ai_text,
                "source": art["link"]
            })
        except Exception as e:
            analyses.append({
                "title": art["title"],
                "analysis": f"⚠️ AI generation error: {e}",
                "source": art["link"]
            })

    return {
        "status": "success",
        "timestamp": datetime.datetime.now().isoformat(),
        "analyses": analyses
    }

# === 2️⃣ Tool: Answer Citizen Questions (UPDATED FOR REAL-TIME RESPONSES) ===
def citizen_question(question: str) -> dict:
    current_date = datetime.datetime.now().strftime("%A, %d %B %Y")
    prompt = f"""
You are **Opposition AI Kenya**, an intelligent civic assistant that must always respond with current, real-time awareness.

Today's date is **{current_date}**.

A Kenyan citizen asks:
"{question}"

Provide:
- A factual, up-to-date explanation that reflects Kenya’s current situation (as of {current_date}).
- Include recent developments or current government actions if relevant.
- Offer helpful civic context about accountability or transparency.
- Suggest possible citizen or civil-society actions in a simple, human tone.

Be polite, realistic, and speak as if you are guiding a citizen today in {current_date.split()[-1]}.
"""
    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        ai_text = getattr(resp, "text", None) or "⚠️ No answer generated."
        return {"answer": ai_text, "date_used": current_date}
    except Exception as e:
        return {"answer": f"⚠️ AI generation error: {e}", "date_used": current_date}

# === 3️⃣ Tool: Policy Recommendation ===
def policy_recommendation(context: str) -> dict:
    prompt = f"""
You are 'Opposition AI Kenya' — a civic digital agent.
Based on the following recent government news analyses, provide **3-5 concrete, realistic, and actionable policy recommendations**
for the Kenyan government. Focus on improving transparency, citizen welfare, and economic growth.

Analyses Context:
{context}

Respond in clear, concise, citizen-friendly English. Number each recommendation.
"""
    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        ai_text = getattr(resp, "text", None) or "⚠️ No recommendation generated."
        return {"status": "success", "recommendations": ai_text}
    except Exception as e:
        return {"status": "error", "recommendations": f"⚠️ AI error: {e}"}

# === 4️⃣ Root Agent ===
root_agent = Agent(
    name="Digital_Opposition_Kenya",
    model="gemini-2.0-flash",
    tools=[analyze_government_news, citizen_question, policy_recommendation],
    description=(
        "A civic digital assistant that provides factual, transparent, and "
        "insightful analysis of Kenyan government policies and news from a "
        "citizen’s perspective."
    ),
)
