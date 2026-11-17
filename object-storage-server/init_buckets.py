"""Idempotent MinIO bootstrap for MyMiniCloud.

Creates demo, profile-pics and documents on every run.
If sample objects are mounted under /app/sample-files, uploads them too.
No credentials or user files are bundled with this script.
"""
import os
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

endpoint = os.getenv("MINIO_ENDPOINT", "http://object-storage-server:9000")
access_key = os.environ["MINIO_ROOT_USER"]
secret_key = os.environ["MINIO_ROOT_PASSWORD"]

client = boto3.client(
    "s3", endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="us-east-1",
)

for attempt in range(30):
    try:
        client.list_buckets()
        break
    except (EndpointConnectionError, ClientError):
        if attempt == 29:
            raise
        time.sleep(2)

for bucket in ("demo", "profile-pics", "documents"):
    try:
        client.create_bucket(Bucket=bucket)
        print(f"Created bucket: {bucket}", flush=True)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise
        print(f"Bucket already exists: {bucket}", flush=True)

samples = [
    ("profile-pics", "avatar.jpg", "image/jpeg"),
    ("documents", "report.pdf", "application/pdf"),
]
sample_dir = Path(os.getenv("MINIO_SAMPLE_DIR", "/app/sample-files"))
for bucket, filename, content_type in samples:
    path = sample_dir / filename
    if not path.is_file():
        print(f"Sample not present (skipped): {path}", flush=True)
        continue
    # Do not overwrite objects that a user may have updated in MinIO.
    try:
        client.head_object(Bucket=bucket, Key=filename)
        print(f"Object already exists (kept): {bucket}/{filename}", flush=True)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code", "") not in ("404", "NoSuchKey", "NotFound"):
            raise
        client.upload_file(str(path), bucket, filename,
                           ExtraArgs={"ContentType": content_type})
        print(f"Uploaded: {bucket}/{filename}", flush=True)

print("MinIO initialization completed.", flush=True)
