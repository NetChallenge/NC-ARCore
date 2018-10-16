import pymysql
from flask import Flask, render_template, request
from minio import Minio
from minio.error import ResponseError

#
minio_host = os.environ.get('MINIO_HOST', None)
minio_access_key = os.environ.get('MINIO_ACCESS_KEY', None)
minio_secret_key = os.environ.get('MINIO_SECRET_KEY', None)
minio_secure = os.environment.get('')
minio_bucket = os.environ.get('MINIO_BUCKET', None)

#
mysql_host = os.environ.get('MYSQL_HOST', None)
mysql_user = os.environ.get('MYSQL_USER', None)
mysql_password = os.environ.get('MYSQL_PWD', None)
mysql_db = os.environ.get('MYSQL_DB', None)

app = Flask(__name__)
minio_client = Minio(minio_host, minio_acess_key, minio_secret_key, minio_secure)

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

def put_file_to_minio(filename, file_content, file_content_length):
	minio_client.put_object(minio_bucket, filename, file_content, file_content_length)
	file_url = minio_client.presigned_get_object(minio_bucket, filename)

	return file_url

@app.route('/signUp', methods = ['GET','POST'])
	query = 'SELECT * FROM users WHERE id=' + request.args['id']
	rows = pymysql_fetch_query(query)

	if len(rows) != 0:
		return request.Response('false')	

@app.route('/saveFace', methods = ['GET','POST'])
def save_face():
	recv_image = request.files['file']
	image_content = request.files['file'].read()
	user_id = request.args['id']
	
	try:
		image_url = put_file_to_minio(user_id+'_'+recv_image.filename, image_content, image_content.length)
		pymysql_commit_query('INSERT')
	except ResponseError as err:
		print(err)

@app.route('/detectFace', methods = ['GET','POST'])
def face_recognition_process(img_binary):
	recv_image = request.files['file']
	image_content = requesst.files['file'].read()
	image = Image.fromstring('RGBA', image_content)

	#print(rgb_frame)
	rgb_frame = cv2.resize(rgb_frame, (0,0), fx=0.25, fy=0.25)
        face_locations = face_recognition.face_locations(rgb_frame)
	json_face_locations = json.dump(face_locations)
	#print(json_face_names)
	return json_face_loations

@app.route('/saveAudio', methods = ['GET','POST'])
def save_audio():
	recv_audio = request.files['file']
	audio_content = request.files['file'].read()
	user_id = request.args['id']

	try:
		audio_url = put_file_to_minio(user_id+'_'+recv_audio.filename, audio_content, audio_content.length)
		pymysql_commit_query('INSERT')
	except ResponseError as err:
		print(err)

@app.route('createRoom', methods = ['GET', 'POST'])
def create_room():
	pass

if __name__=='__main__':
    app.run(host='0.0.0.0',threaded=True)

