import sys
import os
import requests
import json

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-sonnet-4:online"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-Title": "GitHub Repo Web Search Analyzer"
}

if len(sys.argv) < 2:
    print("Usage: python analyze_github_repo.py <owner/repo or repo-url>")
    sys.exit(1)

repo_input = sys.argv[1]

# === Prompt Template ===
prompt = f"""
You are a senior software engineer.

Using up-to-date web search, analyze the GitHub repository: **{repo_input}**

Your task is to return a structured technical overview including:

1. Project Summary – what does it do? who uses it?
2. Key Features – highlight 3–5 notable capabilities
3. Architecture Overview – describe the system’s main components and flow
4. Technology Stack – programming languages, frameworks, integrations
5. Recent Activity – releases, major PRs, roadmap if available
6. Code Quality – testing, linting, structure, contributors
7. Notable Risks or Limitations – issues, weaknesses, known gaps

Do NOT hallucinate facts. Use only reputable public sources and web search. Return your response in markdown.
"""

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "web_search_options": {
        "search_context_size": "high"
    }
}

print("🔍 Sending to Claude via OpenRouter Web Search...")
response = requests.post(API_URL, headers=HEADERS, json=payload)

if response.status_code != 200:
    print(f"❌ Error {response.status_code}: {response.text}")
    sys.exit(1)

result = response.json()
message = result.get("choices", [{}])[0].get("message", {}).get("content", "")

print("\n📄 Claude’s GitHub Repo Analysis:\n")
print(message)
