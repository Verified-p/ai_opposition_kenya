from flask import Flask, render_template, request, jsonify
from agents.opposition_agent import analyze_government_news, citizen_question, policy_recommendation
import json
import os

app = Flask(__name__)

# ----------------------
# Home page
# ----------------------
@app.route("/")
def index():
    return render_template("index.html")


# ----------------------
# Analyze government news
# ----------------------
@app.route("/analyze", methods=["GET"])
def analyze_news():
    try:
        result = analyze_government_news()
        # Save the analysis for later use
        with open("analysis_output.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        return jsonify(result)
    except Exception as e:
        # If live fetch fails, try fallback cache
        if os.path.exists("cache/news_cache.json"):
            with open("cache/news_cache.json", "r", encoding="utf-8") as f:
                cached_articles = json.load(f)
            return jsonify({
                "status": "warning",
                "message": f"⚠️ Live fetch failed: {e}. Using cached news.",
                "analyses": cached_articles
            })
        return jsonify({"status": "error", "message": f"⚠️ Failed to fetch or analyze news: {e}"}), 500


# ----------------------
# Citizen question endpoint
# ----------------------
@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        answer = citizen_question(question)
        return jsonify(answer)
    except Exception as e:
        return jsonify({"error": f"⚠️ Failed to answer question: {e}"}), 500


# ----------------------
# Policy recommendation endpoint
# ----------------------
@app.route("/recommend", methods=["GET", "POST"])
def recommend_policy_endpoint():
    topic = ""

    if request.method == "POST":
        data = request.get_json()
        topic = data.get("topic", "").strip()

    # Fallback: use latest analysis if GET request or POST topic empty
    if not topic:
        if os.path.exists("analysis_output.json"):
            with open("analysis_output.json", "r", encoding="utf-8") as f:
                analysis_data = json.load(f)
            # Combine all AI analyses into the context
            topic = "\n".join([art.get("analysis", "") for art in analysis_data.get("analyses", [])])
        else:
            topic = "Current government policy and recent news in Kenya."

    try:
        result = policy_recommendation(topic)
        return jsonify({"recommendation": result.get("recommendations", "⚠️ No recommendation generated.")})
    except Exception as e:
        return jsonify({"error": f"⚠️ Failed to generate policy recommendation: {e}"}), 500


# ----------------------
# Run Flask app
# ----------------------
if __name__ == "__main__":
    # Optional: set host="0.0.0.0" if you want external access
    app.run(debug=True, port=5000)
