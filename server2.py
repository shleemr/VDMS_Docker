from concurrent import futures
import grpc
import rtsp_stream_pb2
import rtsp_stream_pb2_grpc
import cv2
from PIL import Image
import io
import threading
import time


#LTE
#cam = cv2.VideoCapture("rtsp://meta:meta1234@meta.cns-link.net:557//h264Preview_01_main")

#####     MRlab     #####
#cam = cv2.VideoCapture("rtsp://meta:meta1234@vandilab.iptime.org:557//h264Preview_01_main")
cam = cv2.VideoCapture("uphill_road_10km.mp4")
data = None
imgWidth = 640
imgHeight = 360
img = None
imgResize = None
detected = False

class Rtspstream(rtsp_stream_pb2_grpc.RtspstreamServicer):
    def GetStreaming(self, request, context):
        global imageWidth
        global imageHeight
        global data
        global detected
        global img
        global imgResize

        print(request.token)
        requestToken = request.token
        requestChannel = request.channel
        imageWidth = request.imageWidth
        imageHeight = request.imageHeight

        if detected :
            car = 1
            data = cv2.imencode('.jpg', img)[1].tostring()
        else :
            car = 0
            data = cv2.imencode('.jpg', imgResize)[1].tostring()
        detected = False

        return rtsp_stream_pb2.StreamData(token=requestToken, channel=requestChannel, carDetected=car, image=data)

    def GetCheckStreaming(self, request, context):
        global data
        print(request.token)
        if data is None :
            checkValue = 0
        else :
            checkValue = 1
        return rtsp_stream_pb2.CheckData(readyCheck=checkValue)

def serve():
    print("start server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rtsp_stream_pb2_grpc.add_RtspstreamServicer_to_server(Rtspstream(), server)
    #####     MRlab     #####
    server.add_insecure_port('192.168.101.244:1004')
    #server.add_insecure_port('183.109.221.193:1007')
    
    #LTE
    #server.add_insecure_port('192.168.7.100:1007')    
    server.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        server.stop(0)

def viewVideo():
    global cam
    global img
    global imgResize

    while(True):
        ret_val, img = cam.read()
        imgResize = cv2.resize(img, (640, 360))
        if cv2.waitKey(1) == ord('q'): break
        
    cam.release()
    cv2.destroyAllWindows()


def detectCar():
    global img
    global data
    global imgResize
    global detected

    print("start detect")
    if not img is None :
        car_cascade = cv2.CascadeClassifier('cars.xml')
        checkImg = cv2.resize(img, (320, 180))
        gray = cv2.cvtColor(checkImg, cv2.COLOR_BGR2GRAY)

        # Detect cars
        cars = car_cascade.detectMultiScale(gray, 1.1, 1) #daylight
        ncars=0
        
        # Draw border
        for (x, y, w, h) in cars:
            if h > 90 :
                cv2.rectangle(checkImg, (x,y), (x+w,y+h), (0,0,255), 2)
                ncars = ncars + 1

        if ncars > 0 :
            detected = True

        cv2.imshow("test",checkImg)

    threading.Timer(0.01, detectCar).start()

if __name__ == '__main__':
    t = threading.Thread(target=viewVideo)
    t.start()
    detectCar()
    serve()
