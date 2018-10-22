# -- coding: utf-8 --
import os
import sys
import io
import cv2
import numpy as np
import json
from PIL import Image
from flask import Flask, render_template, request, Response
import face_recognition
import my_mysql
import my_minio

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

	if check_is_file_exist_in_minio(user_email+"_face.png") == False:
		#print("no face images", file=sys.stdout)
		return '1'

	if check_is_file_exist_in_minio(user_email+"_audio.mp4") == False:
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
	
	try:
		image_url = put_file_to_minio(user_email+'_face.png', recv_image, file_length)
		pymysql_commit_query('INSERT INTO face(user_email, image_url) VALUES("'+user_email+'","'+image_url+'")')
		
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

	try:
		audio_url = put_file_to_minio(user_email+'_audio.mp4', recv_audio, audio_length)
		pymysql_commit_query('INSERT INTO voice(user_email, audio_url) VALUES("'+user_email+'","'+audio_url+'")')
		
		return '1'
	except Exception as err:
		print(err)
		return '0'

@app.route('/createRoom', methods = ['GET', 'POST'])
def create_room():
	pass

if __name__=='__main__':
	app.run(host='0.0.0.0', port=app_port, debug=True, threaded=True)


