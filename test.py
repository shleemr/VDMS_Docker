import cv2

capture = cv2.VideoCapture("rtsp://meta:meta1234@meta.cns-link.net:557//h264Preview_01_main")
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = capture.read()
    
    cv2.imshow("VideoFrame", frame)
    

capture.release()
cv2.destroyAllWindows()
