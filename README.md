# 📄 md2word Function — Markdown ➜ Word 自動轉換系統

本專案利用 **Open WebUI 的 Function（Pipe）機制** 與 **md2word FastAPI microservice**，
讓使用者可透過 WebUI 上傳 Markdown 檔並自動轉換成 Word（.docx），
並將輸出上傳至 Google Cloud Storage，最後提供可直接下載的 Signed URL。

---

# 🚀 系統架構

```
┌───────────────────────────┐
│       Open WebUI          │
│   (使用者介面 + Pipe)     │
└───────────────┬───────────┘
                │  呼叫 Function Pipe
                ▼
        md2word FastAPI
    (markdown → docx + GCS)
                │
                ▼
    Google Cloud Storage (Signed URL)
```

---

# 📦 1. md2word FastAPI 功能

- 接收上傳的 Markdown (.md)
- 使用 Pandoc + reference.docx 生成 `.docx`
- 上傳到 Google Cloud Storage
- 回傳 Signed URL

### FastAPI 端點

```
POST /convert
```

回傳格式：

```json
{
  "results": [
    {
      "file_name": "README.docx",
      "file_url": "https://storage.googleapis.com/...signed-url",
      "success": true,
      "message": ""
    }
  ]
}
```

---

# 🐳 2. Docker Compose（只需啟動 md2word）

```
version: "3.9"

services:
  md2word:
    build: .
    container_name: md2word
    restart: unless-stopped
    ports:
      - "8888:8888"
    environment:
      - TZ=Asia/Taipei
    volumes:
      - ./sstc-aiteam-88133bbdce80.json:/secrets/service-account.json:ro
      - ./pandoc_code:/pandoc_code:ro
```

---

# 🧩 3. Open WebUI Function（Pipe）設定

在 WebUI → `Workspace → Tools → Functions → +New → Pipe` 貼入 Function 版本的 md2word Pipe 程式碼。

---

# 💡 4. 使用方式

1. 在 WebUI 上傳 `.md` 檔案
2. 選模型「md2word Pipe」
3. 發送訊息
4. 取得 Word 檔案下載連結

---

# ☁️ 5. Google Cloud Storage 設定

- 建立 bucket（建議 Uniform bucket-level access）
- 建立 Service Account（授權 Storage Admin）
- 將 JSON 金鑰放入：`./sstc-aiteam-88133bbdce80.json`

---

# 📂 6. 推薦目錄架構

```
md2word/
├── app/
│   └── app.py
├── pandoc_code/
│   └── reference.docx
├── docker-compose.yml
├── sstc-aiteam-88133bbdce80.json
└── README.md
```

---

# 🧰 7. Troubleshooting

| 問題 | 原因 | 解法 |
|------|------|------|
| 找不到檔案 | WebUI 尚未寫入 uploads | 重試 |
| GCS 403 | 權限不足 | 加 Storage Admin |
| Word 格式錯誤 | reference.docx 路徑錯誤 | 修正路徑 |

---

# 📝 License

MIT / Internal Use
