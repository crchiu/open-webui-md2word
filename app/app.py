import os
import tempfile
import subprocess
from pathlib import Path
from datetime import timedelta
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from google.cloud import storage


# ========= 請在這裡設定 Service Account JSON 與 GCS Bucket =========

# 1. Service Account JSON 憑證檔路徑
#    請改成你實際的 JSON 檔路徑，例如：
#    SERVICE_ACCOUNT_JSON = ""
SERVICE_ACCOUNT_JSON = "/secrets/service-account.json"

# 2. GCS Bucket 名稱
#    請改成你在 GCP 建好的 bucket 名稱，例如：
#    GCS_BUCKET = "public-its-files"
GCS_BUCKET = "public-its-files"


# ========= 專案路徑與 reference.docx 設定 =========

# 專案根目錄：假設結構為 ~/github/md2word/
#   md2word/
#     ├── app/
#     │    └── app.py
#     └── pandoc_code/
#          └── reference.docx
BASE_DIR = Path(__file__).resolve().parent.parent
REFERENCE_DOC = BASE_DIR / "pandoc_code" / "reference.docx"

app = FastAPI(title="Markdown to Word Converter (GCS + Signed URL)")


# ========= Pydantic Model 定義 =========

class FileResult(BaseModel):
    file_name: str
    success: bool
    file_url: Optional[str] = None  # Signed URL
    message: Optional[str] = None


class ConvertResponse(BaseModel):
    results: List[FileResult]


# ========= Pandoc 轉檔 =========

def run_pandoc(input_md: str, output_docx: str) -> None:
    """
    呼叫 pandoc 將 Markdown 轉成 Word (.docx)，並套用 reference.docx 樣板。
    """
    if not REFERENCE_DOC.exists():
        raise RuntimeError(f"找不到 reference.docx：{REFERENCE_DOC}")

    cmd = [
        "pandoc",
        input_md,
        "-o", output_docx,
        "--reference-doc", str(REFERENCE_DOC),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"pandoc 轉檔失敗。\nSTDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
        )


# ========= GCS 上傳 + Signed URL =========

def get_gcs_client() -> storage.Client:
    """
    使用 Service Account JSON 建立 GCS Client。
    不依賴 GOOGLE_APPLICATION_CREDENTIALS 環境變數。
    """
    if not os.path.exists(SERVICE_ACCOUNT_JSON):
        raise RuntimeError(f"找不到 Service Account JSON 檔案：{SERVICE_ACCOUNT_JSON}")

    return storage.Client.from_service_account_json(SERVICE_ACCOUNT_JSON)


def upload_to_gcs(local_path: str, dest_path: str) -> str:
    """
    上傳檔案到 GCS，並回傳一個限時下載的 Signed URL（v4，預設 1 小時有效）。
    不更動 IAM / ACL，適用於啟用 Uniform bucket-level access 的 bucket。
    """
    if not GCS_BUCKET:
        raise RuntimeError("未設定 GCS_BUCKET，請在 app.py 內指定 GCS Bucket 名稱")

    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(dest_path)

    # 上傳檔案
    blob.upload_from_filename(local_path)

    # 產生限時下載的簽名網址
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET",
    )

    return signed_url


# ========= FastAPI Endpoint =========

@app.post("/convert", response_model=ConvertResponse)
async def convert_md_files(files: List[UploadFile] = File(...)):
    """
    接收多個 Markdown 檔案，逐一轉成 Word (.docx)，上傳到 GCS，
    並為每個檔案產生一個限時下載的 Signed URL。
    """
    if not files:
        raise HTTPException(status_code=400, detail="沒有收到任何檔案")

    results: List[FileResult] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for upload in files:
            filename = upload.filename or "unnamed"
            result = FileResult(file_name=filename, success=False)

            # 僅處理 .md 檔，其餘直接標記略過
            if not filename.lower().endswith(".md"):
                result.message = "檔案不是 .md，已略過"
                results.append(result)
                continue

            try:
                # 1. 將上傳內容寫到暫存 md 檔
                md_path = os.path.join(tmpdir, filename)
                base_name = os.path.splitext(filename)[0]
                docx_name = base_name + ".docx"
                docx_path = os.path.join(tmpdir, docx_name)

                content = await upload.read()
                with open(md_path, "wb") as f:
                    f.write(content)

                # 2. 用 pandoc + reference.docx 轉成 docx
                run_pandoc(md_path, docx_path)

                # 3. 上傳到 GCS 並取得 Signed URL
                #    dest_path 可依需求調整「目錄結構」
                dest_path = f"md2word-output/{docx_name}"
                signed_url = upload_to_gcs(docx_path, dest_path)

                result.success = True
                result.file_url = signed_url
                result.message = "轉檔與上傳成功（Signed URL 有效時間 1 小時）"

            except Exception as e:
                result.message = f"處理失敗：{e}"

            results.append(result)

    return ConvertResponse(results=results)