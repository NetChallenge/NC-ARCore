import cv2
import numpy as np
import json
from PIL import Image
import face_recognition

image = Image.open("85.jpg")

rgb_frame = cv2.resize(np.asarray(image), (0,0), fx=1, fy=1)
face_locations = face_recognition.face_locations(rgb_frame)
print(str(face_locations))

json_face_locations = json.dumps(face_locations)

print(str(json_face_locations))
print(type(str(json_face_locations)))
