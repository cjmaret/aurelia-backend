import json
from together import Together
from app.config import Config


def chat_with_ollama(model: str, prompt: str, max_tokens: int = 256):
    try:

        api_key = Config.TOGETHER_API_KEY
        if not api_key:
            raise RuntimeError(
                "TOGETHER_API_KEY is not set in the environment.")

        client = Together(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,  # more deterministic, less creative
            # max_tokens=max_tokens,
        )
 
        content = response.choices[0].message.content

        # print(f"Response from model: {content}")

        # strip extra whitespace or wrapping characters
        content = content.strip()
        if content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()
        if content.startswith("json"):
            content = content[4:].strip()

        try:
            start_index = content.find("[")
            end_index = content.rfind("]") + 1
            if start_index == -1 or end_index == -1:
                raise ValueError("No valid JSON array found in the response.")

            json_content = content[start_index:end_index]

            parsed_content = json.loads(json_content)
            
            filtered_content = filter_superfluous_errors(parsed_content)

            return filtered_content
        
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {str(e)}")
            raise ValueError("The response from the model is not valid JSON.")
    except Exception as e:
        raise RuntimeError(
            f"An error occurred while communicating with the model: {str(e)}")


def filter_superfluous_errors(parsed_content):
    excluded_types = {"pronunciation", "spelling", "punctuation", "capitalization"}
    for sentence in parsed_content:
        filtered_errors = []
        for error in sentence.get("errors", []):
            # attempt to filter out errors about ounctuation
            if (
                "comma" in error.get("reason", "").lower()
                or "comma" in error.get("error", "").lower()
                or "punctuation" in error.get("reason", "").lower()
            ):
                continue 
    
            # attempt to filter out error objects with no errors
            if not (
                error.get("error", "").lower() == "no error found"
                or error.get("reason", "").lower() == "the sentence is grammatically correct"
                # remove non-speech errors
                or error.get("type", "").lower() in excluded_types
            ):
                filtered_errors.append(error)

        # Update the errors array with only meaningful errors
        sentence["errors"] = filtered_errors
    return parsed_content
