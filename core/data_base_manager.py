import json
import os

class DatabaseManager:
    @staticmethod
    def save_json(path, data):
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_json(path, default=None):
        """
        讀取 JSON，如果檔案不存在、為空或損毀，自動以預設值重建並回傳。
        """
        if default is None:
            default = {}

        if not os.path.exists(path):
            DatabaseManager.save_json(path, default)
            return default

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                DatabaseManager.save_json(path, default)
                return default
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            DatabaseManager.save_json(path, default)
            return default