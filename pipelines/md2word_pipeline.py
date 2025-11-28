"""
title: md2word Pipe
id: md2word_pipe
author: your-name
version: 0.1.1
description: 將上傳的 Markdown 檔案丟給 md2word 服務轉成 Word，並回傳下載連結。
requirements: requests
usage: 開啟Open WebUI-> Admin Panel -> Functions，新增Function後，貼上程式碼
"""

import os
from typing import Optional, List

import requests
from pydantic import BaseModel, Field
from open_webui.config import UPLOAD_DIR


class Pipe:
    # 管理員在 UI 裡可以調整的設定（Valves）
    class Valves(BaseModel):
        MD2WORD_URL: str = Field(
            default="http://192.168.50.42:8888/convert",
            description="md2word FastAPI 服務的 /convert URL",
        )
        REQUEST_TIMEOUT: int = Field(
            default=600, description="呼叫 md2word API 的逾時秒數"
        )

    class UserValves(BaseModel):
        # 目前先不開放使用者側設定
        pass

    def __init__(self):
        self.valves = self.Valves()

    def _resolve_file_path(self, file_info: dict) -> Optional[tuple[str, str]]:
        """
        根據 __files__ 單筆資料解析出 (實體路徑, 檔名)
        __files__ 常見結構大概會長這樣：
        {
          "id": "xxxx",
          "name": "README.md",
          "path": "/app/backend/data/uploads/xxxx_README.md",
          "mime": "text/markdown",
          ...
        }
        我們優先用 path，沒有 path 再 fallback 用 UPLOAD_DIR + id_name
        """
        if not file_info:
            return None

        filename = file_info.get("name") or file_info.get("filename")
        if not filename:
            return None

        # 1️⃣ 優先使用 Open WebUI 給的實體路徑（如果有）
        if file_info.get("path"):
            return file_info["path"], filename

        # 2️⃣ 沒有 path 時，用 id + name 推出檔案路徑
        file_id = file_info.get("id")
        if file_id:
            guessed_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
            return guessed_path, filename

        return None

    def pipe(
        self,
        body: dict,
        __files__: Optional[List[dict]] = None,
        __user__: Optional[dict] = None,
        **kwargs,
    ):
        """
        主邏輯：
        1. 從 __files__ 取得第一個上傳檔案的實體路徑
        2. 丟給 md2word FastAPI 轉檔
        3. 回傳下載連結文字到聊天視窗
        """
        try:
            if not __files__:
                return (
                    "⚠️ 沒有偵測到上傳的檔案。\n"
                    "請在這則訊息中附上 Markdown 檔案（.md），"
                    "並確認有勾選 / 使用「md2word Pipe」這個模型或工具。"
                )

            # 這裡先只處理第一個檔案，如要多檔可改成迴圈
            file_info = __files__[0]
            resolved = self._resolve_file_path(file_info)
            if not resolved:
                return "⚠️ 無法解析上傳檔案路徑。\n" f"收到的檔案資訊為：`{file_info}`"

            file_path, filename = resolved

            if not os.path.exists(file_path):
                return (
                    "⚠️ 找不到上傳的檔案實體路徑。\n"
                    f"預期路徑：`{file_path}`\n"
                    "請重新上傳檔案再試一次。"
                )

            # 呼叫 md2word FastAPI
            with open(file_path, "rb") as f:
                files = {
                    # 對應你原本 FastAPI /convert 的參數名稱
                    "files": (filename, f, "text/markdown"),
                }

                resp = requests.post(
                    self.valves.MD2WORD_URL,
                    files=files,
                    timeout=self.valves.REQUEST_TIMEOUT,
                )

            resp.raise_for_status()
            data = resp.json()

            # 預期 md2word 回傳格式：
            # {
            #   "results": [
            #     {
            #       "file_name": "xxx.docx",
            #       "file_url": "https://signed-url",
            #       "success": true,
            #       "message": "..."
            #     }
            #   ]
            # }
            if not isinstance(data, dict) or "results" not in data:
                return f"❌ md2word 服務回傳的格式非預期：`{data}`"

            results = data.get("results") or []
            if not results:
                return "❌ md2word 服務沒有回傳任何結果。"

            result = results[0]
            if not result.get("success", False):
                return f"❌ 轉檔失敗：{result.get('message', '未知錯誤')}"

            file_url = result.get("file_url")
            output_name = result.get("file_name", "輸出檔案.docx")

            msg_lines = [
                "✅ Markdown 已成功轉成 Word 並上傳完成。",
                f"- 原始檔名：`{filename}`",
                f"- 輸出檔名：`{output_name}`",
            ]
            if file_url:
                msg_lines.append(f"- 下載連結：{file_url}")

            return "\n".join(msg_lines)

        except Exception as e:
            # 這裡可以改成更詳細的 debug 訊息
            return f"❌ 執行 md2word Pipe 時發生例外錯誤：`{e}`"
