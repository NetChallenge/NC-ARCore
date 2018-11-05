# -- coding: utf-8 --
import os
import sys
import io
import cv2
import numpy as np
import json
from PIL import Image
from flask import Flask, render_template, request, Response, jsonify
import face_recognition
import my_mysql
import my_minio
import uuid
import http
import docker

app = Flask(__name__)
cli = None
mysql_client = None
minio_client = None

'''
@app.route('/signUp', methods = ['GET','POST'])
	query = 'SELECT * FROM users WHERE id=' + request.args['id']
	rows = pymysql_fetch_query(query)

	if len(rows) != 0:
		return request.Response('false')	
'''
@app.route('/checkIsRegister', methods = ['GET', 'POST'])
def check_is_register():
	#print("checkIsRegister", file=sys.stderr)
	user_email = request.args['email']
	user_name = request.args['name']
	mysql_client.pymysql_commit_query('INSERT IGNORE INTO user(user_email, user_name) VALUES ("'+user_email+'","'+user_name+'")')
	#print("(user_token): ", file=sys.stdout)

	if minio_client.check_is_file_exist_in_minio(user_email+"_face.png") == False:
		#print("no face images", file=sys.stdout)
		return '1'

	if minio_client.check_is_file_exist_in_minio(user_email+"_audio.mp4") == False:
		#print("no voice files", file=sys.stdout)
		return '2'
	
	print("exist all files", file=sys.stdout)
	return '0'
		

@app.route('/saveFace', methods = ['GET','POST'])
def save_face():
	recv_image = request.files['image']
	recv_image.seek(0, os.SEEK_END)
	file_length = recv_image.tell()
	recv_image.seek(0, 0)
	user_email = request.form['email']
	user_name = request.form['name']	

	try:
		image_url = minio_client.put_file_to_minio(user_email+'_face.png', recv_image, file_length)
		mysql_client.pymysql_commit_query('INSERT INTO face(user_email, user_name, image_url) VALUES("'+user_email+'","'+user_name+'","'+image_url+'") ON DUPLICATE KEY UPDATE image_url="'+image_url+'";')
		
		return '1'
	except Exception as err:
		print(err)
		return '0'

@app.route('/detectFace', methods = ['GET','POST'])
def detect_face():
	recv_image = request.files['image']
	image_content = request.files['image'].read()
	#image = Image.frombytes('RGBA', len(image_content), image_content)
	image = Image.open(io.BytesIO(image_content))

	#print(rgb_frame)
	rgb_frame = cv2.resize(np.asarray(image), (0,0), fx=1, fy=1)
	face_locations = face_recognition.face_locations(rgb_frame)
	json_face_locations = json.dumps(face_locations)
	return Response(json_face_locations, mimetype="application/json")

@app.route('/saveAudio', methods = ['GET','POST'])
def save_audio():
	recv_audio = request.files['audio']
	recv_audio.seek(0, os.SEEK_END)
	audio_length = recv_audio.tell()
	recv_audio.seek(0, 0)
	user_email = request.form['email']
	user_name = request.form['name']

	try:
		audio_url = minio_client.put_file_to_minio(user_email+'_audio.mp4', recv_audio, audio_length)
		mysql_client.pymysql_commit_query('INSERT INTO voice(user_email, user_name, audio_url) VALUES("'+user_email+'","'+user_name+'","'+audio_url+'")')
		
		return '1'
	except Exception as err:
		print(err)
		return '0'

@app.route('/getRoomInfoByEmail', methods = ['GET', 'POST'])
def get_room_info_by_email():
	user_email = request.args['email']
	row = mysql_client.pymysql_fetchone_query('SELECT room_id FROM room_user WHERE user_email="'+user_email+'";')
	if not row:
		return ('', http.HTTPStatus.NO_CONTENT)

	room_id, = row
	row = mysql_client.pymysql_fetchone_query('SELECT room_title FROM room WHERE room_id="'+str(room_id)+'";')
	room_title, = row
	stt_ip, stt_port, stt_id, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic, = mysql_client.pymysql_fetchone_query('SELECT stt_ip, stt_port, stt_id, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic FROM room_user WHERE room_id='+str(room_id)+' AND user_email="'+user_email+'";')

	json_msg = {}
	json_msg['room_id'] = room_id
	json_msg['room_title'] = room_title
	json_msg['stt_ip'] = stt_ip
	json_msg['stt_port'] = stt_port
	json_msg['stt_id'] = stt_id
	json_msg['stt_max_size'] = int(1024)
	json_msg['mqtt_ip'] = mqtt_ip
	json_msg['mqtt_port'] = mqtt_port
	json_msg['mqtt_id'] = mqtt_id
	json_msg['mqtt_topic'] = str(room_id)+"/"+mqtt_topic
	json_string = json.dumps(json_msg)

	return Response(json_string, mimetype="application/json")

@app.route('/getRoomInfoByTitle', methods = ['GET', 'POST'])
def get_room_info_by_title():
	room_title = request.args['title']
	row = mysql_client.pymysql_fetchone_query('SELECT room_id, user_email FROM room WHERE room_title="'+room_title+'";')
	if row == None:
		return ('', http.HTTPStatus.NO_CONTENT)

	room_id, user_email, = row
	stt_ip, stt_port, stt_id, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic, = mysql_client.pymysql_fetchone_query('SELECT stt_ip, stt_port, stt_id, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic FROM room_user WHERE room_id='+str(room_id)+' AND user_email="'+user_email+'";')

	json_msg = {}
	json_msg['room_id'] = room_id
	json_msg['room_title'] = room_title
	json_msg['stt_ip'] = stt_ip
	json_msg['stt_port'] = stt_port
	json_msg['stt_id'] = stt_id
	json_msg['stt_max_size'] = int(1024)
	json_msg['mqtt_ip'] = mqtt_ip
	json_msg['mqtt_port'] = mqtt_port
	json_msg['mqtt_id'] = mqtt_id
	json_msg['mqtt_topic'] = str(room_id)+"/"+mqtt_topic
	json_string = json.dumps(json_msg)

	return Response(json_string, mimetype="application/json")

@app.route('/searchUser', methods = ['GET', 'POST'])
def search_user():
	user_name = request.args['name']
	rows = mysql_client.pymysql_fetch_query('SELECT * FROM user WHERE user_name="'+user_name+'";')
	
	return Response(json.dumps(rows), mimetype="application/json")
	
@app.route('/createRoom', methods = ['GET', 'POST'])
def create_room():
	room_title = request.args['title']
	user_email = request.args['email']
	user_name = request.args['name']
	users_json = request.args['users']
	users = json.loads(users_json)

	#we need to create edge container and mqtt id
	stt_ip = "163.180.117.216"
	stt_port = int(-1)
	stt_id = "NULL"
	mqtt_ip = "163.180.117.216"
	mqtt_port = int(1883)
	mqtt_id = "-1"
	mqtt_topic = "msg"
	rows = mysql_client.pymysql_fetch_query('SELECT * FROM room WHERE room_title="'+room_title+'";')
	if rows:
		return ('', http.HTTPStatus.NO_CONTENT)

	room_id = mysql_client.pymysql_commit_query_and_get_last_id('INSERT INTO room(room_id, user_email, room_title) VALUES(NULL,"'+user_email+'","'+room_title+'")')
	room_id = int(room_id)

	for user in users:
		tmp_mqtt_id = str(uuid.uuid4())
		if user['userEmail'] == user_email:
			mqtt_id = tmp_mqtt_id
		mysql_client.pymysql_commit_query('INSERT INTO room_user(room_id, user_email, user_name, stt_ip, stt_port, stt_id, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic) VALUES('+str(room_id)+',"'+user['userEmail']+'","'+user['userName']+'","'+stt_ip+'",'+str(stt_port)+','+stt_id+',"'+mqtt_ip+'",'+str(mqtt_port)+',"'+tmp_mqtt_id+'","'+mqtt_topic+'")')
			
	#we need to create edge container with environment variable
	

	json_msg = {}
	json_msg['room_id'] = room_id
	json_msg['room_title'] = room_title
	json_msg['stt_ip'] = stt_ip
	json_msg['stt_port'] = stt_port
	json_msg['stt_id'] = stt_id
	json_msg['stt_max_size'] = int(1024)
	json_msg['mqtt_ip'] = mqtt_ip
	json_msg['mqtt_port'] = mqtt_port
	json_msg['mqtt_id'] = mqtt_id
	json_msg['mqtt_topic'] = str(room_id)+"/"+mqtt_topic
	json_string = json.dumps(json_msg)

	return Response(json_string, mimetype="application/json")

@app.route('/enterRoom', methods = ['GET', 'POST'])
def enter_room():
	room_id = request.args['room_id']
	user_email = request.args['email']
	user_name = request.args['name']

	room_id, stt_ip, stt_port, stt_id, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic, = mysql_client.pymysql_fetchone_query('SELECT room_id, stt_ip, stt_port, stt_id, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic FROM room_user WHERE room_id='+room_id+' AND user_email="'+user_email+'";')

	#container not yet
	bound_random_port = int(-1)
	if stt_port == int(-1):
		envList = ['LANGUAGE=ko_KR.UTF-8','LANG=ko_KR.UTF-8',
			'MINIO_HOST='+minio_client.get_host(),'MINIO_ACCESS_KEY='+minio_client.get_access_key(),
			'MINIO_SECRET_KEY='+minio_client.get_secret_key(),'MINIO_BUCKET='+minio_client.get_bucket(),
			'MYSQL_HOST='+mysql_client.get_host(),'MYSQL_USER='+mysql_client.get_user(),'MYSQL_PWD='+mysql_client.get_pwd(),'MYSQL_DB='+mysql_client.get_db(),
			'MQTT_IP='+mqtt_ip,'MQTT_PORT='+str(mqtt_port),'MQTT_ID='+mqtt_id,'MQTT_TOPIC='+str(room_id)+"/"+mqtt_topic,
			'GOOGLE_APPLICATION_CREDENTIALS=/root/ar-server/python/Voucher-82ad460a212c.json',
			'ROOM_ID='+str(room_id),'USER_EMAIL='+user_email,'USER_NAME='+user_name]

		print(envList)
		host_config = cli.create_host_config(port_bindings={5678: ('0.0.0.0', None)})
		info = cli.create_container(image='ar-edge:latest', command='python3 /root/ar-server/python/ar_server.py', ports=[5678], host_config=host_config, environment=envList, detach=True)

		#we need to start before getting port. because, port is changed when starting.
		cli.start(info['Id'])		
		bound_random_port = cli.port(info['Id'], 5678)
		mysql_client.pymysql_commit_query('UPDATE room_user SET stt_port='+str(bound_random_port[0]['HostPort'])+', stt_id="'+info['Id']+'" WHERE room_id='+str(room_id)+' AND user_email="'+user_email+'";')
	else:
		cli.start(stt_id)
		bound_random_port = cli.port(stt_id, 5678)
		mysql_client.pymysql_commit_query('UPDATE room_user SET stt_port='+str(bound_random_port[0]['HostPort'])+' WHERE room_id='+str(room_id)+' AND user_email="'+user_email+'";')

	json_msg = {}
	json_msg['stt_port'] = bound_random_port[0]['HostPort']
	json_string = json.dumps(json_msg)

	return Response(json_string, mimetype="application/json")
	

@app.route('/leaveRoom', methods = ['GET', 'POST'])
def leave_room():
	room_id = request.args['room_id']
	user_email = request.args['email']

	stt_id, = mysql_client.pymysql_fetchone_query('SELECT stt_id FROM room_user WHERE room_id='+str(room_id)+' AND user_email="'+user_email+'";')
	cli.stop(stt_id, 2)
	
	return Response(json.dumps({'success':True}), mimetype="application/json")

def initialize():
	global mysql_client, minio_client, cli
	#load mysql client
	mysql_client = my_mysql.MyMysql(os.environ.get('MYSQL_HOST', None), os.environ.get('MYSQL_USER', None), os.environ.get('MYSQL_PWD', None), os.environ.get('MYSQL_DB', None))

	#load minio client
	minio_client = my_minio.MyMinio(os.environ.get('MINIO_HOST', None), os.environ.get('MINIO_ACCESS_KEY', None), os.environ.get('MINIO_SECRET_KEY', None), (os.environ.get('MINIO_SECURE', None) == 'True'), os.environ.get('MINIO_BUCKET', None))

	#load docker client
	cli = docker.APIClient(base_url='http://'+os.environ.get('DOCKER_HOST', None)+":"+os.environ.get('DOCKER_PORT', None))	

	#initialize flask
	app.run(host='0.0.0.0', port=os.environ.get('APP_PORT', None), debug=True, threaded=True)	

if __name__=='__main__':
	initialize()
