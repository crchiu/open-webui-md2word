import os
import sys
from datetime import timedelta

from google.cloud import storage


def upload_and_get_signed_url(local_path: str, bucket_name: str, dest_path: str):
    """
    上傳檔案到 GCS，並產生一個限時下載的 Signed URL。
    不使用物件 ACL，因此相容 Uniform bucket-level access。
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest_path)

    print(f"上傳檔案到 gs://{bucket_name}/{dest_path} ...")
    blob.upload_from_filename(local_path)

    print("產生 1 小時有效的 Signed URL ...")
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET",
    )

    return signed_url


def main():
    bucket_name = os.getenv("GCS_BUCKET")
    if not bucket_name:
        print("❌ 請先設定環境變數 GCS_BUCKET，例如：export GCS_BUCKET='my-bucket-name'")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("用法：python test_gcs_upload.py /path/to/file")
        sys.exit(1)

    local_path = sys.argv[1]
    if not os.path.isfile(local_path):
        print(f"❌ 找不到檔案：{local_path}")
        sys.exit(1)

    file_name = os.path.basename(local_path)
    dest_path = f"test-upload/{file_name}"

    try:
        signed_url = upload_and_get_signed_url(local_path, bucket_name, dest_path)
    except Exception as e:
        print(f"❌ 上傳或產生 Signed URL 時發生錯誤：{e}")
        sys.exit(1)

    print("\n✅ 上傳完成！")
    print("🔹 限時下載連結（Signed URL，預設 1 小時有效，任何人可下載）：")
    print(signed_url)


if __name__ == "__main__":
    main()