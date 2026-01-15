from google import genai

class GeminiAI:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def get_response(self, prompt):
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt
        )
        return response.text