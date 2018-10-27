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

app_port = os.environ.get('APP_PORT', None)
app = Flask(__name__)

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
	#print("(user_token): ", file=sys.stdout)

	if my_minio.check_is_file_exist_in_minio(user_email+"_face.png") == False:
		#print("no face images", file=sys.stdout)
		return '1'

	if my_minio.check_is_file_exist_in_minio(user_email+"_audio.mp4") == False:
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
		image_url = my_minio.put_file_to_minio(user_email+'_face.png', recv_image, file_length)
		my_mysql.pymysql_commit_query('INSERT INTO face(user_email, user_name, image_url) VALUES("'+user_email+'","'+user_name+'","'+image_url+'") ON DUPLICATE KEY UPDATE image_url="'+image_url+'";')
		
		return '1'
	except Exception as err:
		print(err)
		return '0'

@app.route('/detectFace', methods = ['GET','POST'])
def face_recognition_process():
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
		audio_url = my_minio.put_file_to_minio(user_email+'_audio.mp4', recv_audio, audio_length)
		my_mysql.pymysql_commit_query('INSERT INTO voice(user_email, user_name, audio_url) VALUES("'+user_email+'","'+user_name+'","'+audio_url+'")')
		
		return '1'
	except Exception as err:
		print(err)
		return '0'

@app.route('/getRoomInfoByEmail', methods = ['GET', 'POST'])
def get_room_info_by_email():
	user_email = request.args['email']
	room_id, room_title, = my_mysql.pymysql_fetchone_query('SELECT room_id, room_title FROM room WHERE user_email="'+user_email+'";')
	if room_id == None:
		return ('', http.HTTPStatus.NO_CONTENT)

	stt_ip, stt_port, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic, = my_mysql.pymysql_fetchone_query('SELECT stt_ip, stt_port, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic FROM room_user WHERE room_id='+str(room_id)+' AND user_email="'+user_email+'";')

	json_msg = {}
	json_msg['room_id'] = room_id
	json_msg['room_title'] = room_title
	json_msg['stt_ip'] = stt_ip
	json_msg['stt_port'] = stt_port
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
	room_id, user_email, = my_mysql.pymysql_fetchone_query('SELECT room_id, user_email FROM room WHERE room_title="'+room_title+'";')
	if room_id == None:
		return ('', http.HTTPStatus.NO_CONTENT)

	stt_ip, stt_port, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic, = my_mysql.pymysql_fetchone_query('SELECT stt_ip, stt_port, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic FROM room_user WHERE room_id='+str(room_id)+' AND user_email="'+user_email+'";')

	json_msg = {}
	json_msg['room_id'] = room_id
	json_msg['room_title'] = room_title
	json_msg['stt_ip'] = stt_ip
	json_msg['stt_port'] = stt_port
	json_msg['stt_max_size'] = int(1024)
	json_msg['mqtt_ip'] = mqtt_ip
	json_msg['mqtt_port'] = mqtt_port
	json_msg['mqtt_id'] = mqtt_id
	json_msg['mqtt_topic'] = str(room_id)+"/"+mqtt_topic
	json_string = json.dumps(json_msg)

	return Response(json_string, mimetype="application/json")

@app.route('/createRoom', methods = ['GET', 'POST'])
def create_room():
	room_title = request.args['title']
	user_email = request.args['email']
	user_name = request.args['name']

	#we need to create edge container and mqtt id
	stt_ip = "163.180.117.216"
	stt_port = int(5690)
	mqtt_ip = "163.180.117.216"
	mqtt_port = int(1883)
	mqtt_id = str(uuid.uuid4())
	mqtt_topic = "msg"
	rows = my_mysql.pymysql_fetch_query('SELECT * FROM room WHERE room_title="'+room_title+'";')
	if len(rows) != 0:
		return ('', http.HTTPStatus.NO_CONTENT)

	room_id = my_mysql.pymysql_commit_query_and_get_last_id('INSERT INTO room(room_id, user_email, room_title) VALUES(NULL,"'+user_email+'","'+room_title+'")')
	room_id = int(room_id)
	my_mysql.pymysql_commit_query('INSERT INTO room_user(room_id, user_email, user_name, stt_ip, stt_port, mqtt_ip, mqtt_port, mqtt_id, mqtt_topic) VALUES('+str(room_id)+',"'+user_email+'","'+user_name+'","'+stt_ip+'",'+str(stt_port)+',"'+mqtt_ip+'",'+str(mqtt_port)+',"'+mqtt_id+'","'+mqtt_topic+'")')

	json_msg = {}
	json_msg['room_id'] = room_id
	json_msg['room_title'] = room_title
	json_msg['stt_ip'] = stt_ip
	json_msg['stt_port'] = stt_port
	json_msg['stt_max_size'] = int(1024)
	json_msg['mqtt_ip'] = mqtt_ip
	json_msg['mqtt_port'] = mqtt_port
	json_msg['mqtt_id'] = mqtt_id
	json_msg['mqtt_topic'] = str(room_id)+"/"+mqtt_topic
	json_string = json.dumps(json_msg)

	return Response(json_string, mimetype="application/json")

if __name__=='__main__':
        app.run(host='0.0.0.0', port=app_port, debug=True, threaded=True)
