
import os
import time
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

endpoint = os.getenv(
    "MINIO_ENDPOINT",
    "http://object-storage-server:9000"
)
access_key = os.environ["MINIO_ROOT_USER"]
secret_key = os.environ["MINIO_ROOT_PASSWORD"]
bucket_name = os.getenv("MINIO_BUCKET_NAME", "demo")

client = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="us-east-1"
)

print("Waiting for MinIO...", flush=True)

for attempt in range(30):
    try:
        client.list_buckets()
        break
    except (EndpointConnectionError, ClientError):
        if attempt == 29:
            raise
        time.sleep(2)

try:
    client.create_bucket(Bucket=bucket_name)
    print(f"Bucket created: {bucket_name}", flush=True)
except ClientError as error:
    code = error.response["Error"]["Code"]
    if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
        print(f"Bucket already exists: {bucket_name}", flush=True)
    else:
        raise

print("Bucket initialization completed.", flush=True)
