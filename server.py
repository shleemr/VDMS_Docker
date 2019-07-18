from concurrent import futures
import time
import grpc
import rtsp_stream_pb2
import rtsp_stream_pb2_grpc
import cv2
import numpy as np
from PIL import Image
import io
import threading
import pytesseract

cam = cv2.VideoCapture("rtsp://meta:meta1234@meta.cns-link.net:557//h264Preview_01_main")
data = None
imageWidth = 1024
imageHeight = 768
#cam = cv2.VideoCapture(0)
car = 0

class Rtspstream(rtsp_stream_pb2_grpc.RtspstreamServicer):
    def GetStreaming(self, request, context):
        global imageWidth
        global imageHeight
        global data
        global car
        print(request.token)
        requestToken = request.token
        requestChannel = request.channel
        imageWidth = request.imageWidth
        imageHeight = request.imageHeight
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
    #server.add_insecure_port('183.109.221.193:1007')
    server.add_insecure_port('192.168.7.100:1007')
    
    server.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        server.stop(0)

def viewVideo():
    global data
    global cam
    global imageWidth
    global imageHeight
    global car
    while(True):
        ret_val, img = cam.read()

        img = cv2.resize(img, (imageWidth, imageHeight))

        copy_img=img.copy()
        #cv2.imshow('init_img',img)
        img2=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        #cv2.imshow('gray',img2)
        blur = cv2.GaussianBlur(img2,(3,3),0)
        #cv2.imshow('blur',blur)
        canny=cv2.Canny(blur,100,200)
        #cv2.imshow('canny',canny)
        cnts,contours,hierarchy  = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        box1=[]
        f_count=0
        select=0
        #plate_width=0

        for i in range(len(contours)):
             cnt=contours[i]          
             area = cv2.contourArea(cnt)
             x,y,w,h = cv2.boundingRect(cnt)
             rect_area=w*h  #area size
             aspect_ratio = float(w)/h # ratio = width/height
      
             if  (aspect_ratio>=0.2)and(aspect_ratio<=1.0)and(rect_area>=100)and(rect_area<=700): 
                 cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),1)
                 box1.append(cv2.boundingRect(cnt))

        for i in range(len(box1)): ##Buble Sort on python
            for j in range(len(box1)-(i+1)):
                  if box1[j][0]>box1[j+1][0]:
                       temp=box1[j]
                       box1[j]=box1[j+1]
                       box1[j+1]=temp
             
        #to find number plate measureing length between rectangles
        for m in range(len(box1)):
             count=0
             for n in range(m+1,(len(box1)-1)):
                  delta_x=abs(box1[n+1][0]-box1[m][0])
                  if delta_x > 150:
                       break
                  delta_y =abs(box1[n+1][1]-box1[m][1])
                  if delta_x ==0:
                       delta_x=1
                  if delta_y ==0:
                       delta_y=1           
                  gradient =float(delta_y) /float(delta_x)
                  if gradient<0.25:
                      count=count+1
             #measure number plate size         
             if count > f_count:
                  select = m
                  f_count = count
                  plate_width=delta_x
        #cv2.imshow('scan',img)
        r = 0
        y = 0
        h = 0
        w = 0

        if select > 0:
             r = box1[select][1]-30
             y = box1[select][3]+box1[select][1]+20
             h = box1[select][0]-30
             w = 140+box1[select][0]

        if r < y and h < w and select > 0 and r > 31 and h > 31:
             #print(r)
             #print("rrrrrrrrrrrrrrrr")

             #print(y)
             #print("yyyyyyyyyyyyyyyyy")

             #print(h)
             #print("hhhhhhhhhhhhhhhhhhhh")

             #print(w)
             #print("wwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
             car=1
             print(1)
             number_plate=copy_img[r:y,h:w] 
             #cv2.imshow('number_plate',number_plate)
            
             resize_plate=cv2.resize(number_plate,None,fx=1.8,fy=1.8,interpolation=cv2.INTER_CUBIC+cv2.INTER_LINEAR) 
             plate_gray=cv2.cvtColor(number_plate,cv2.COLOR_BGR2GRAY)
             ret_val,th_plate = cv2.threshold(plate_gray,127,255,cv2.THRESH_BINARY)

             #cv2.imshow('plate_th',th_plate)
             kernel = np.ones((3,3),np.uint8)
             er_plate = cv2.erode(th_plate,kernel,iterations=1)
             er_invplate = er_plate
             #cv2.imwrite('er_plate.jpg',er_invplate)
             #result = pytesseract.image_to_string(Image.open('er_plate.jpg'), lang='kor')
             #cv2.imshow('result',result)
        
             #print(result)
        #return(result.replace(" ",""))
        #time.sleep(1)
        else :
             car=0
             print(0)


        if cv2.waitKey(1) & 0xFF == ord('q'):
             break
        data = cv2.imencode('.jpg', img)[1].tostring()
    cam.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    t = threading.Thread(target=viewVideo)
    t.start()
    serve()
