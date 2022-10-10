# Team stackOverflow, Honda Mobility Challenge
# Linus, Shantha, Renhao, Michael
import base64
import os
import sys
import uuid
import face_recognition
import cv2
import numpy as np
import requests
from playsound import playsound
import datetime
import threading
import subprocess

# import statements above

# Get frame from webcam
video_capture = cv2.VideoCapture(0)


# Function about recognize user photo
def recognize_user_photo(file_path):
    user_image = face_recognition.load_image_file(file_path)
    face_encode = face_recognition.face_encodings(user_image, num_jitters=50, model="large")[0]
    return face_encode


# method for boxing and identifying faces as unknown or by their saved names
def draw_boxes(user_face_locations, face_names, frame):
    for (top, right, bottom, left), name in zip(user_face_locations, face_names):
        top = top * 4
        right = right * 4
        bottom = bottom * 4
        left = left * 4
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 30), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_TRIPLEX
        cv2.putText(frame, name, (left + 5, bottom - 5), font, 1.0, (255, 255, 255), 1)


def record_log(user_data):
    for data in log_dict:
        log_dict.append(user_data)
        if user_data[0] != data[0]:
            log_dict.append(user_data)
        else:
            pass


def reload():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def opening(file):
    kernel = np.ones((5, 5), np.uint8)
    opening = cv2.morphologyEx(file, cv2.MORPH_OPEN, kernel, iterations=3)
    return opening


def alert_to_user(token, title, text):
    link = "https://api.day.app/push"
    icon = "https://hack.osu.edu/assets/img/favicon.ico"
    alert_object = {
        'title': title,
        'body': text,
        'device_key': token,
        'icon': icon
    }
    handle_request = requests.post(link, alert_object)
    if handle_request.status_code == 200:
        return True
    else:
        return False


def push_to_rtmp(frame):
    path = 0
    rtmp_url = "rtmp://127.0.0.1:14514/live/"
    # gather video info to ffmpeg
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # command and params for ffmpeg
    command = ['ffmpeg',
               '-y',
               '-f', 'rawvideo',
               '-vcodec', 'rawvideo',
               '-pix_fmt', 'bgr24',
               '-s', "{}x{}".format(width, height),
               '-r', str(fps),
               '-i', '-',
               '-c:v', 'libx264',
               '-pix_fmt', 'yuv420p',
               '-preset', 'ultrafast',
               '-f', 'flv',
               rtmp_url]

    # using subprocess and pipe to fetch frame data
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    process.stdin.write(frame.tobytes())


def get_all_user():
    result = requests.get("https://visual-helper.qwq.xyz/allUsers").json()
    return result["users"]


def get_user(uid):
    result = requests.get("https://visual-helper.qwq.xyz/user?uid=" + str(uid)).json()
    return result


def convert_base64_to_file(base64_text):
    filename = str(uuid.uuid4())
    path = "./resources/photo/" + filename + ".png"
    with open(path, "wb") as fh:
        fh.write(base64.b64decode(base64_text))
    return path


def post_log(uid):
    # headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = "https://visual-helper.qwq.xyz/log"
    body = {
        'uid': uid,
    }
    result = requests.post(url, body)
    return result


# has photo of owner of car & potential family members as well
known_face_encodings = []
known_face_names = []
known_face_uid = []
# name shown for each person
for user in get_all_user():
    uid = user["uid"]
    name = user['name']
    photo_base64 = get_user(uid)["image_data"]
    #print(photo_base64)
    photo = convert_base64_to_file(photo_base64)
    known_face_encodings.append(recognize_user_photo(photo))
    known_face_names.append(name)
    known_face_uid.append(uid)

# Test Area
# known_face_encodings.append(recognize_user_photo("./resources/photo/1.jpeg"))
# known_face_names.append("Linus")
# known_face_uid.append("100001")

user_face_locations = []
face_encodings = []
face_names = []
log_dict = []
# listing of all the persons and corresponding faces

# Some status variable
alert_voice_status = 0
alert_notice_status = 0

process_this_frame = True
currFrame = 0
strangerFrame = 0
match_times = 0


# goes through each frame & sets variables for parsing each frame and updating when stranger is encountered

def detector():
    # using subprocess and pipe to fetch frame data

    # always true until the user quits or enters their car
    global match_times, strangerFrame, user_face_locations, face_names
    while True:
        ret, frame = video_capture.read()

        # captures a single frame
        if process_this_frame:
            # always true until the user presses q
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # changing size of frames as person gets closer/farther from camera
            rgb_small_frame = small_frame[:, :, ::-1]
            # updates boxes depending on where the face has moved
            user_face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, user_face_locations)
            face_names = []
            for face_encoding in face_encodings:
                # compares known user photos to the face in the camera
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, 0.45)
                name = "Unknown"
                # automates the name to "Unknown"
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                # 实时匹配到的index
                best_match_index = np.argmin(face_distances)
                # if it is a known face, match it

                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    if match_times == 0 or match_times % 500 == 0:
                        user_data = [name, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                        record_log(user_data)

                        alert_to_user("TosXScciT2wTXp7uA4hDLf", "New Alert",
                                      name + " access the location\nTime: " + datetime.datetime.now().strftime(
                                          '%Y-%m-%d %H:%M:%S'))
                        post_log(known_face_uid[best_match_index])
                        # print(name)
                        # print(known_face_uid[best_match_index])
                    match_times = match_times + 1
                else:
                    # if not, identify as stranger
                    if strangerFrame == 0 or strangerFrame % 300 == 0:
                        playsound('./resources/sound/beep-01a.mp3')
                        # cv2.imwrite('stranger' + str(currFrame) + '.png', frame)
                        user_data = ["unknown", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                        record_log(user_data)
                        alert_to_user("TosXScciT2wTXp7uA4hDLf", "Emergency Alert",
                                      "ILLEGAl ACCESS \nTime: " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        post_log(100000)
                        # method to save stranger photo & add them to known_stranger_faces
                    strangerFrame = strangerFrame + 1
                    # if currFrame - strangerFrame > 50:
                    #     # to avoid beeping the entire time a stranger is around (who could be getting into their own car)
                    #     playsound('./resources/sound/beep-01a.mp3')
                    #     cv2.imwrite('stranger' + str(currFrame) + '.png', frame)
                    #     user_data = ["unknown", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                    #     record_log(user_data)
                    #     print(user_data)

                face_names.append(name)

        draw_boxes(user_face_locations, face_names, frame)
        # process.stdin.write(frame.tobytes())

        cv2.imshow('Video', frame)
        # push_to_rtmp(frame)
        # out.write(frame)
        # currFrame = currFrame + 1  # update currframe as each frame is parsed

        if cv2.waitKey(1) & 0xFF == ord('q'):  # to terminate the program
            break
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    thread_1 = threading.Thread(detector())
    thread_1.start()
    thread_1.join()
# close camera window after person hypothetically enters car
