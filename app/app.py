# app.py
import os
import tempfile
import subprocess
from typing import List
import request
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Markdown to Word Converter (File Upload)")

# 之後你要真的上傳 Google Drive 再補這些
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/secrets/service_account.json")


class FileResult(BaseModel):
    file_name: str
    success: bool
    file_url: str | None = None
    message: str | None = None


class ConvertResponse(BaseModel):
    results: List[FileResult]


def run_pandoc(input_md: str, output_docx: str) -> None:
    """呼叫 pandoc 將 Markdown 轉為 Word (.docx)"""
    result = subprocess.run(
        ["pandoc", input_md, "-o", output_docx],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pandoc 轉檔失敗：{result.stderr}")


def upload_to_google_drive(docx_path: str) -> str:
    """
    將 docx 檔案上傳至 Google Drive Shared Drive。
    這裡先回傳假連結，之後你再補真正的上傳邏輯。
    """
    file_name = os.path.basename(docx_path)
    # TODO: 改成實際 Google Drive 上傳結果
    dummy_link = f"https://drive.google.com/file/d/FAKE_ID_{file_name}/view?usp=sharing"
    return dummy_link


@app.post("/convert", response_model=ConvertResponse)
async def convert_md_files(files: List[UploadFile] = File(...)):
    """
    接收多個上傳的檔案（預期為 .md），逐一轉成 .docx 並上傳 Google Drive。
    回傳每一個檔案的處理結果。
    """
    if not files:
        raise HTTPException(status_code=400, detail="沒有收到任何檔案")

    results: List[FileResult] = []

    # 使用共同的 temp 目錄
    with tempfile.TemporaryDirectory() as tmpdir:
        for upload in files:
            filename = upload.filename or "unnamed"
            result = FileResult(file_name=filename, success=False)

            # 只處理 .md 檔，其它直接回報錯誤
            if not filename.lower().endswith(".md"):
                result.message = "檔案不是 .md，已略過"
                results.append(result)
                continue

            try:
                # 1. 將上傳檔案寫到 temp 檔
                md_path = os.path.join(tmpdir, filename)
                docx_name = os.path.splitext(filename)[0] + ".docx"
                docx_path = os.path.join(tmpdir, docx_name)

                content = await upload.read()
                with open(md_path, "wb") as f:
                    f.write(content)

                # 2. 呼叫 pandoc 轉檔
                run_pandoc(md_path, docx_path)

                # 3. 上傳到 Google Drive（這裡先 stub）
                file_url = upload_to_google_drive(docx_path)

                result.success = True
                result.file_url = file_url
                result.message = "轉檔與上傳成功"

            except Exception as e:
                result.message = f"處理失敗：{e}"

            results.append(result)

    return ConvertResponse(results=results)
