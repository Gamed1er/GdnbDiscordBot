# 使用輕量版的 Python 3.10
FROM python:3.10-slim

# 設定容器內的工作目錄
WORKDIR /app

# 複製環境變數與套件清單
COPY requirements.txt .

# 安裝套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼到容器
COPY . .

# 執行機器人
CMD ["python", "main.py"]