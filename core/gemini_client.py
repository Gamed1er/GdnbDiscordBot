import time
import random
from google import genai
from google.genai import types

class GeminiAI:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        print(f"載入了 {len(self.api_keys)} 個 Key")
        
    def get_response(self, prompt, files_list=None):
        """
        files_list 格式應為: [{"bytes": b'...', "mime_type": "image/png"}, ...]
        """
        max_retries = 3
        contents = []
        
        # 1. 處理多個檔案附件
        if files_list:
            for file_info in files_list:
                try:
                    file_part = types.Part.from_bytes(
                        data=file_info["bytes"],
                        mime_type=file_info["mime_type"],
                    )
                    contents.append(file_part)
                except Exception as e:
                    print(f"DEBUG - 封裝多模態檔案失敗: {e}")

        # 2. 將文字 Prompt 補在最後面
        contents.append(prompt)
        
        for i in range(max_retries):
            selected_key = random.choice(self.api_keys)
            client = genai.Client(api_key=selected_key)
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents
                )
                return response.text

            except Exception as e:
                error_str = str(e).upper()

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if i < max_retries - 1:
                        print(f"⚠️ Key 額度用盡，正在嘗試換一個 Key 重試 ({i+1}/{max_retries})...")
                        time.sleep(2)
                        continue
                    else:
                        return "📢 目前 AI 的使用量太高了，我的能量暫時耗盡...請等一分鐘後再跟我說話！"

                elif "500" in error_str or "503" in error_str or "UNAVAILABLE" in error_str:
                    if i < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return "⚠️ Google AI 伺服器目前好像有點感冒（過載），請稍後再試試看。"

                else:
                    print(f"DEBUG - 未知錯誤內容: {e}")
                    return "❌ 發生了未知的錯誤，請聯絡開發者 @gdnb 檢查日誌。"
        
        return "😵 嘗試多次後依然失敗，請檢查網路或 API 狀態。"