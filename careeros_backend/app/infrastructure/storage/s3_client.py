import logging

logger = logging.getLogger("careeros")


class S3Client:
    """
    SIMULATED S3 client: it stores nothing and returns fake URLs. The application no longer uses it (uploads go
    through LocalFileStorage); it is kept only because an old contract test imports it. Do not use it for real files.
    """

    def __init__(self, bucket_name: str = "careeros-resumes"):
        self.bucket_name = bucket_name

    async def upload_file(self, file_content: bytes, file_name: str, key: str) -> str:
        logger.info(f"Uploading {file_name} to S3 bucket {self.bucket_name} at key {key}")
        # Simulated S3 upload
        return f"s3://{self.bucket_name}/{key}"

    async def generate_presigned_url(self, key: str, expires_in_seconds: int = 900) -> str:
        logger.info(f"Generating presigned URL for key {key}")
        # Simulated pre-signed URL generation
        return f"https://{self.bucket_name}.s3.amazonaws.com/{key}?AWSAccessKeyId=MOCK&Expires={expires_in_seconds}"

    async def delete_file(self, key: str) -> bool:
        logger.info(f"Deleting {key} from S3 bucket {self.bucket_name}")
        return True


s3_client = S3Client()
