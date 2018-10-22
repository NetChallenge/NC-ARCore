import os
import sys
from minio import Minio
from minio.error import ResponseError


#
minio_host = os.environ.get('MINIO_HOST', None)
minio_access_key = os.environ.get('MINIO_ACCESS_KEY', None)
minio_secret_key = os.environ.get('MINIO_SECRET_KEY', None)
minio_secure = False
minio_bucket = os.environ.get('MINIO_BUCKET', None)
minio_client = Minio(minio_host, minio_access_key, minio_secret_key, minio_secure)

def put_file_to_minio(filename, file_content, file_content_length):
	minio_client.put_object(minio_bucket, filename, file_content, file_content_length)
	file_url = minio_client.presigned_get_object(minio_bucket, filename)

	return file_url

def check_is_file_exist_in_minio(filename):
	try:
		minio_client.stat_object(minio_bucket, filename)
		return True
	except Exception as err:
		return False
