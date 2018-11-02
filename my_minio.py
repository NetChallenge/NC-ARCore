import os
import sys
from minio import Minio
from minio.error import ResponseError

class MyMinio(object):
	def __init__(self, minio_host, minio_access_key, minio_secret_key, minio_secure, minio_bucket):
		self.__minio_host = minio_host
		self.__minio_access_key = minio_access_key
		self.__minio_secret_key = minio_secret_key
		self.__minio_secure = minio_secure
		self.__minio_bucket = minio_bucket
		self.__minio_client = Minio(minio_host, minio_access_key, minio_secret_key, minio_secure)

	def put_file_to_minio(self, filename, file_content, file_content_length):
		self.__minio_client.put_object(self.__minio_bucket, filename, file_content, file_content_length)
		file_url = self.__minio_client.presigned_get_object(self.__minio_bucket, filename)

		return file_url

	def check_is_file_exist_in_minio(self, filename):
		try:
			self.__minio_client.stat_object(self.__minio_bucket, filename)
			return True
		except Exception as err:
			return False

	def get_host(self):
		return self.__minio_host

	def get_access_key(self):
		return self.__minio_access_key

	def get_secret_key(self):
		return self.__minio_secret_key

	def get_secure(self):
		return self.__minio_secure

	def get_bucket(self):
		return self.__minio_bucket
