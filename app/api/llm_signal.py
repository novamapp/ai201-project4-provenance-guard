# llm_signal.py
import os
import json
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from the local .env file
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a highly specialized forensic linguistic analysis engine engineered to detect AI-generated text, with a strict focus on poetry and creative writing.

Analyze the provided text against known patterns of Large Language Model generation, specifically inspecting for:
1. Semantic Clichés: Overuse of predictable metaphors, romantic tropes, or neat thematic wrap-ups.
2. Rigid Schemas: Unbroken, perfectly predictable rhyme schemes or metrical meters lacking natural human variations or intentional slant rhymes used to create tension.
3. Lack of Intentional Imperfections: Overly smooth syntax and uniform sentence-like punctuation flows that lack typical human spontaneity.

You must return your evaluation EXCLUSIVELY as a valid JSON object. Do not include any introductory text, markdown wrappers, or markdown formatting blocks (like ```json ... ```).

The JSON object must contain exactly these two keys with floating-point values between 0.0 and 1.0:
{
  "human_likely": <float value between 0.0 and 1.0 representing human likelihood>,
  "AI_likely": <float value between 0.0 and 1.0 representing AI likelihood>
}
"""

def analyze_text_with_llm(text):
    """
    Submits the target text to Groq's llama-3.3-70b-versatile model
    to evaluate human vs AI writing likelihood characteristics.
    """
    if not text or not text.strip():
        return {"human_likely": 0.5, "AI_likely": 0.5}

    try:
        # Request completion from Groq API
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this poem:\n\n{text}"}
            ],
            temperature=0.1,  # Low temperature forces determinism and structural adherence
            max_tokens=150,
            response_format={"type": "json_object"}  # Hard enforces a JSON object payload response
        )
        
        # Extract response content
        response_content = completion.choices[0].message.content.strip()
        
        # Parse output safely
        data = json.loads(response_content)
        print('LLM:', data)
        
        # Ensure values exist and are numeric types clamped appropriately
        human_likely = float(data.get("human_likely", 0.5))
        AI_likely = float(data.get("AI_likely", 0.5))
        
        return {
            "human_likely": max(0.0, min(1.0, human_likely)),
            "AI_likely": max(0.0, min(1.0, AI_likely))
        }

    except Exception as e:
        # If the API call fails or JSON formatting is invalid, fallback to neutral weights
        print(f"[LLM Signal Error] Failed to evaluate text: {e}")
        return {"human_likely": 0.5, "AI_likely": 0.5}