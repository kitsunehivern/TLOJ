import google.generativeai as genai
from config import Config

genai.configure(api_key=Config().gemini_api_key)

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config={"temperature": 0.2, "max_output_tokens": 1024},
)


def call_gemini_api(prompt: str) -> str:
    try:
        response = model.generate_content(
            contents=[{"parts": [{"text": prompt}]}],
        )

        return response.text if response and response.text else ""
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return ""
