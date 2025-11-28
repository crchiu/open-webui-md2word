FROM python:3.11-slim

# 環境設定
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 安裝 pandoc 與系統相依套件
RUN apt-get update && \
    apt-get install -y --no-install-recommends pandoc && \
    rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 複製程式與 reference.docx
COPY app ./app
COPY pandoc_code ./pandoc_code

# 對外開放 8000 port
EXPOSE 8888

# 啟動 FastAPI 服務
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8888"]