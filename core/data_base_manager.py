import json
import os

class DatabaseManager:
    @staticmethod
    def save_json(path, data):
        # 確保目錄存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_json(path, default_factory=dict):
        """
        讀取 JSON，如果檔案不存在或出錯，回傳預設值 (預設為空字典)
        """
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(default_factory)
            return default_factory()
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            # 檔案損毀時的處理
            return default_factory()