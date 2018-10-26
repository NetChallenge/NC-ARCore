import os
import sys
import pymysql
#
mysql_host = os.environ.get('MYSQL_HOST', None)
mysql_user = os.environ.get('MYSQL_USER', None)
mysql_password = os.environ.get('MYSQL_PWD', None)
mysql_db = os.environ.get('MYSQL_DB', None)

def get_mysql_conn():
	conn = pymysql.connect(mysql_host, mysql_user, mysql_password, mysql_db)
	curs = conn.cursor()

	return conn, curs

def pymysql_commit_query(query):
	conn, curs = get_mysql_conn()
	curs.execute(query)
	conn.commit()
	conn.close()

def pymysql_fetch_query(query):
	conn, curs = get_mysql_conn()
	curs.execute(query)
	rows = curs.fetchall()

	return rows

def pymysql_fetchone_query(query):
	conn, curs = get_mysql_conn()
	curs.execute(query)
	row = curs.fetchone()
	
	return row

def pymysql_commit_query_and_get_last_id(query):
	conn, curs = get_mysql_conn()
	curs.execute(query)
	conn.commit()
	last_id = curs.lastrowid
	conn.close()
	
	return last_id
