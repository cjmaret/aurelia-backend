import json
from together import Together
from app.config import Config

def chat_with_ollama(model: str, prompt: str, max_tokens: int = 256):
    try:
        
        api_key = Config.TOGETHER_API_KEY
        if not api_key:
            raise RuntimeError("TOGETHER_API_KEY is not set in the environment.")

        client = Together(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0, # more deterministic, less creative
            # max_tokens=max_tokens,
        )

        content = response.choices[0].message.content

        # strip extra whitespace or wrapping characters
        content = content.strip()
        if content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()
        if content.startswith("json"):
            content = content[4:].strip()

        try:
            parsed_content = json.loads(content)
            return parsed_content
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {str(e)}")
            print(f"Raw content: {content}")
            raise ValueError("The response from the model is not valid JSON.")
    except Exception as e: 
        raise RuntimeError(
            f"An error occurred while communicating with the model: {str(e)}")
