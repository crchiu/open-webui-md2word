FROM python:3.11-slim

WORKDIR /app

# 安裝 pandoc 與其他系統相依套件（視需求調整）
RUN apt-get update && \
    apt-get install -y pandoc && \
    rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY app.py .

# 環境變數（可在 docker run / compose 中覆蓋）
ENV GOOGLE_DRIVE_FOLDER_ID=""
ENV GOOGLE_SERVICE_ACCOUNT_JSON="/secrets/service_account.json"

# 預留 Service Account 憑證掛載點
VOLUME ["/secrets"]

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]