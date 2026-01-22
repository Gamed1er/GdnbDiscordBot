import time
from google import genai
from google.genai import errors

def get_response(self, prompt):
    max_retries = 3
    for i in range(max_retries):
        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash", # 或你使用的模型
                contents=prompt
            )
            return response.text
        except errors.ServerError as e:
            if i < max_retries - 1:
                time.sleep(2) # 等待 2 秒後重試
                continue
            else:
                return "⚠️ AI 伺服器目前過載中，請稍後再試。"
        except Exception as e:
            return f"❌ 發生未知錯誤: {str(e)}"