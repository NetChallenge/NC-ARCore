import os
import sys
import pymysql

class MyMysql(object):
	def __init__(self, mysql_host, mysql_user, mysql_password, mysql_db):
		self.__mysql_host = mysql_host
		self.__mysql_user = mysql_user
		self.__mysql_password = mysql_password
		self.__mysql_db = mysql_db

	def __get_mysql_conn(self):
		conn = pymysql.connect(self.__mysql_host, self.__mysql_user, self.__mysql_password, self.__mysql_db)
		curs = conn.cursor()

		return conn, curs

	def pymysql_commit_query(self, query):
		conn, curs = self.__get_mysql_conn()
		curs.execute(query)
		conn.commit()
		conn.close()

	def pymysql_fetch_query(self, query):
		conn, curs = self.__get_mysql_conn()
		curs.execute(query)
		rows = curs.fetchall()

		return rows

	def pymysql_fetchone_query(self, query):
		conn, curs = self.__get_mysql_conn()
		curs.execute(query)
		return curs.fetchone()

	def pymysql_commit_query_and_get_last_id(self, query):
		conn, curs = self.__get_mysql_conn()
		curs.execute(query)
		conn.commit()
		last_id = curs.lastrowid
		conn.close()
	
		return last_id

	def get_host(self):
		return self.__mysql_host

	def get_user(self):
		return self.__mysql_user

	def get_pwd(self):
		return self.__mysql_password

	def get_db(self):
		return self.__mysql_db
