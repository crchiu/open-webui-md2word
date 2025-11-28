import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 之後你要真的上傳 Google Drive 再補這些
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1SlC6d3xFteB-xUfQ3bBjSGH9xS9vHs4K")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "../google_drive_api_code/logical-light-479407-e4-019e43a076cf.json")

def main():
    if not GOOGLE_DRIVE_FOLDER_ID:
        raise RuntimeError("請先設定環境變數 GOOGLE_DRIVE_FOLDER_ID（Shared Drive 的資料夾 ID）")

    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_JSON):
        raise RuntimeError(f"找不到 Service Account JSON：{GOOGLE_SERVICE_ACCOUNT_JSON}")

    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_JSON,
        scopes=scopes,
    )
    service = build("drive", "v3", credentials=creds)

    # 建一個小測試檔
    test_path = "drive_upload_test.txt"
    with open(test_path, "w", encoding="utf-8")
        f.write("Hello from md2word test.\n")

    file_metadata = {
        "name": "drive_upload_test.txt",
        "parents": [GOOGLE_DRIVE_FOLDER_ID],
    }

    media = MediaFileUpload(
        test_path,
        mimetype="text/plain",
        resumable=False,
    )

    created_file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink, driveId, parents",
            supportsAllDrives=True,
        )
        .execute()
    )

    print("上傳成功：")
    print("id:", created_file.get("id"))
    print("name:", created_file.get("name"))
    print("webViewLink:", created_file.get("webViewLink"))
    print("driveId:", created_file.get("driveId"))
    print("parents:", created_file.get("parents"))

if __name__ == "__main__":
    main()