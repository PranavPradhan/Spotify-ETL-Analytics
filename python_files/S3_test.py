import boto3
from botocore.exceptions import NoCredentialsError

try:
    s3 = boto3.client('s3')
    # Replace 'your-bucket-name' with your S3 bucket name
    buckets = s3.list_buckets()
    print(buckets)
except NoCredentialsError:
    print("Credentials not available")