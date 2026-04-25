import time
from google import genai
from google.genai import errors # type: ignore
import random

class GeminiAI:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        print(f"載入了 {len(self.api_keys)} 個 Key")
        
    def get_response(self, prompt):
        max_retries = 3
        
        for i in range(max_retries):
            # 每次重試都換一個不同的 Key 試試看（負載平衡）
            selected_key = random.choice(self.api_keys)
            client = genai.Client(api_key=selected_key)
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", # 建議換成正式版更穩定
                    contents=prompt
                )
                return response.text

            except Exception as e:
                error_str = str(e).upper() # 轉大寫方便比對

                # 1. 處理 429 使用限制錯誤
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if i < max_retries - 1:
                        print(f"⚠️ Key 額度用盡，正在嘗試換一個 Key 重試 ({i+1}/{max_retries})...")
                        time.sleep(2) # 等待一下再試
                        continue
                    else:
                        return "📢 目前 AI 的使用量太高了，我的能量暫時耗盡...請等一分鐘後再跟我說話！"

                # 2. 處理 500/503 伺服器端錯誤
                elif "500" in error_str or "503" in error_str or "UNAVAILABLE" in error_str:
                    if i < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return "⚠️ Google AI 伺服器目前好像有點感冒（過載），請稍後再試試看。"

                # 3. 其他未知錯誤 (只顯示簡短訊息，不顯示完整日誌)
                else:
                    print(f"DEBUG - 未知錯誤內容: {e}") # 留在後台自己看
                    return "❌ 發生了未知的錯誤，請聯絡開發者 @gdnb 檢查日誌。"
        
        return "😵 嘗試多次後依然失敗，請檢查網路或 API 狀態。"