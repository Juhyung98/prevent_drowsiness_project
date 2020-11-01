# -*- encoding: utf-8 -*-
#  sudo pip3 install opencv, dlib, flask, imutils
# USAGE
# python main.py --c haarcascade_frontalface_default.xml -p shape_predictor_68_face_landmarks.dat [-a 1]

# import the necessary packages
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import argparse
import imutils
import dlib
import cv2
from flask import Flask, render_template, Response, jsonify
import numpy as np
import time
import threading
import time


'''
###############################################################################
'''


def euclidean_dist(ptA, ptB):
    # compute and return the euclidean distance between the two
    # points
    return np.linalg.norm(ptA - ptB)


def eye_aspect_ratio(eye):
    # compute the euclidean distances between the two sets of
    # vertical eye landmarks (x, y)-coordinates
    A = euclidean_dist(eye[1], eye[5])
    B = euclidean_dist(eye[2], eye[4])

    # compute the euclidean distance between the horizontal
    # eye landmark (x, y)-coordinates
    C = euclidean_dist(eye[0], eye[3])

    # compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)

    # return the eye aspect ratio
    return ear


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--cascade", required=True,
                help="path to where the face cascade resides")
ap.add_argument("-p", "--shape-predictor", required=True,
                help="path to facial landmark predictor")
ap.add_argument("-a", "--alarm", type=int, default=0,
                help="boolean used to indicate if TraffHat should be used")
args = vars(ap.parse_args())

# check to see if we are using GPIO/TrafficHat as an alarm
if args["alarm"] > 0:
    from gpiozero import TrafficHat
    th = TrafficHat()
    print("[INFO] using TrafficHat alarm...")

# define two constants, one for the eye aspect ratio to indicate
# blink and then a second constant for the number of consecutive
# frames the eye must be below the threshold for to set off the
# alarm
EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 16

# initialize the frame counter as well as a boolean used to
# indicate if the alarm is going off
COUNTER = 0
ALARM_ON = False

# load OpenCV's Haar cascade for face detection (which is faster than
# dlib's built-in HOG detector, but less accurate), then create the
# facial landmark predictor
print("[INFO] loading facial landmark predictor...")
detector = cv2.CascadeClassifier(args["cascade"])
predictor = dlib.shape_predictor(args["shape_predictor"])

# grab the indexes of the facial landmarks for the left and
# right eye, respectively
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# start the video stream thread
print("[INFO] starting video stream thread...")


# 카메라 웹 스트리밍
# https://www.hackster.io/ruchir1674/video-streaming-on-flask-server-using-rpi-ef3d75 참고
# https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/ 참고
# https://opencv-python.readthedocs.io/en/latest/index.html 참고

# 라즈베리파이 카메라 설정
# 1. USB웹 캠이 아닌 picamera이면 2번을 꼭 수행
# 2. https://webnautes.tistory.com/1192 참고하여 /etc/modules 수정하여 /dev/video0 장치로 인식
# 카메라 장치 연결, debug 모드에선 동작X, 프레임 크기 축소
vs = VideoStream(src=0).start()  # 0(for USB) or -1(for picamera)
# vs = VideoStream(usePiCamera=True).start()
time.sleep(1.0)

# global variable for checking toggle-onoff, is_sleep
outputFrame = None
active = False
is_sleep = False
humidity = 13
temperature = 15
lock = threading.Lock()

# loop over frames from the video stream


def sleep_detect():
    global outputFrame, lock, COUNTER, active, is_sleep, ALARM_ON

    while True:
        # grab the frame from the threaded video file stream, resize
        # it, and convert it to grayscale
        # channels)
        frame = vs.read()
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect faces in the grayscale frame
        rects = detector.detectMultiScale(gray, scaleFactor=1.1,
                                          minNeighbors=5, minSize=(30, 30),
                                          flags=cv2.CASCADE_SCALE_IMAGE)

        # loop over the face detections
        for (x, y, w, h) in rects:
            # construct a dlib rectangle object from the Haar cascade
            # bounding box
            rect = dlib.rectangle(int(x), int(y), int(x + w),
                                  int(y + h))

            # determine the facial landmarks for the face region, then
            # convert the facial landmark (x, y)-coordinates to a NumPy
            # array
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            # extract the left and right eye coordinates, then use the
            # coordinates to compute the eye aspect ratio for both eyes
            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)

            # average the eye aspect ratio together for both eyes
            ear = (leftEAR + rightEAR) / 2.0

            # compute the convex hull for the left and right eye, then
            # visualize each of the eyes
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            # check to see if the eye aspect ratio is below the blink
            # threshold, and if so, increment the blink frame counter
            if ear < EYE_AR_THRESH:
                COUNTER += 1

                # if the eyes were closed for a sufficient number of
                # frames, then sound the alarm
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    # if the alarm is not on, turn it on
                    if not ALARM_ON:
                        ALARM_ON = True

                        # check to see if the TrafficHat buzzer should
                        # be sounded
                        if args["alarm"] > 0 and active == True:
                            th.buzzer.blink(0.1, 0.1, 10,
                                            background=True)

                    # is_sleep on
                    is_sleep = True
                    # draw an alarm on the frame
                    cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # otherwise, the eye aspect ratio is not below the blink
            # threshold, so reset the counter and alarm
            else:
                COUNTER = 0
                ALARM_ON = False
                is_sleep = False

            # draw the computed eye aspect ratio on the frame to help
            # with debugging and setting the correct eye aspect ratio
            # thresholds and frame counters
            cv2.putText(frame, "EAR: {:.3f}".format(ear), (300, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # acquire the lock, set the output frame, and release the lock
        with lock:
            outputFrame = frame.copy()
    # while end

# def sleep_detect(): end


'''
###############################################################################
'''

# flask 웹서버
app = Flask(__name__)


# gen():
# : outputFrame 에 저장된 값이 있다면 , 이 데이터를 웹이 읽을 수 있는 byte형식으로 인코딩한다.
# @app.route("/video_feed"):
# 해당 URL로 접속 시 "http://ip주소:port(5000)/video_feed") 카메라 데이터를 볼 수 있다.
def gen():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')
# def gen(): end


@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(gen(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


'''
###############################################################################
'''
# 해당 URL로 접속 시 아래 함수 안 코드 수행 ex)"http://ip주소:port(5000)/index.html")

# index.html page


@app.route('/')
def index():

    return render_template('index.html')
# def index(): end

# toggle active variable


@app.route('/active')
def activeToggle():
    global active

    active = not active

    return str(active)
# def activeToggle(): end


# get data json format
'''
import Adafruit_DHT
sensor = Adafruit_DHT.DHT11
gpio_pin = 4

try:
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
except Exception:
    pass
'''
@app.route('/data')
def getSleepData():
    global humidity, temperature

    data = {
        'sensor1': temperature,
        'sensor2': humidity,
        }

    return jsonify(data)

@app.route('/sleep')
def getSensorData():
    global is_sleep

    data = {
        'sleep': is_sleep,
        }

    return jsonify(data)    
# def getData(): end


'''
###############################################################################
'''

# 메인 스레드 시작
# : sleep_detect() 서브스레드 시작
# : flask 웹 서버 시작
if __name__ == '__main__':
    # start a thread that will perform trafficlight detect
    t = threading.Thread(target=sleep_detect)
    t.daemon = True
    try:
        t.start()
        print("[INFO] sub Thread: sleep_detect run")
    except Exception as error:
        print(error)
    app.run(host='0.0.0.0', threaded=True)

# release the video stream pointer and program end
vs.stop()
print("[INFO] program End")


'''
###############################################################################
'''
