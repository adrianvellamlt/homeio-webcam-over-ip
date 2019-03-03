import cv2
import socket
from sys import argv
from time import sleep
from struct import pack
from pickle import dumps
from threading import Thread
from numpy import zeros, uint8

white = (255, 255, 255)

shape = (480, 640)
offlineStreamImg = zeros((shape), dtype=uint8)
textsize = cv2.getTextSize("Stream Offline", cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
centreCoords = ( int((shape[1] - textsize[0]) / 2), int((shape[0] + textsize[1]) / 2) )
cv2.putText(offlineStreamImg, "Stream Offline", centreCoords, cv2.FONT_HERSHEY_SIMPLEX, 1, (69, 53, 220), 2)

server = None
rtsp_clients = []

def rtsp_setup(port):
    address = socket.gethostbyname("localhost")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((address, port))
    server.listen(10)
    return server

def main():
    global server

    cap_indx = 0
    port = 8089

    if len(argv) == 3:
        cap_indx = int(argv[1])
        port = int(argv[2])

    title = "Webcam - " + str(cap_indx)
    cap = cv2.VideoCapture(cap_indx)

    server = rtsp_setup(port)

    clientLookup = RTSPClientLookup()
    clientLookup.start()

    while True:
        ret, img = cap.read()
        img = cv2.flip(img, 1)

        cv2.waitKey(1)

        if ret == False and img is None:
            cap.release() # release
            cap = cv2.VideoCapture(cap_indx) # retry
            cv2.imshow(title, offlineStreamImg)
            continue
        
        cv2.rectangle(img, (0, 0), (img.shape[1], img.shape[0]), white, 2)
        cv2.putText(img, title, (10, 30), 0, 1, white, 2)

        img = cv2.resize(img, dsize=(img.shape[1]//2, img.shape[0]//2), interpolation=cv2.INTER_CUBIC)

        data = dumps(img)
        
        for client in rtsp_clients:
            try:
                client[0].sendall(pack("L", len(data)) + data)
            except Exception as err:
                rtsp_clients.remove(client)
                print("Connections dropped: ", client[1], err)
                client[0].close()

        cv2.imshow(title, img)
    
    clientLookup.stop()

# Lookup for new clients to stream to
class RTSPClientLookup(Thread):
    def __init__(self):
        self.running = True
        super(RTSPClientLookup, self).__init__(name = "RTSP Client Lookup")

    def stop(self): self.running = False

    def run(self):
        global server
        global rtsp_clients

        try:
            while self.running:
                try:
                    if len(rtsp_clients) <= 5:
                        conn, addr = server.accept()
                        print("Connection established to:", addr)
                        rtsp_clients.append((conn, addr))
                except:
                    print("Server connection dropped")
        except Exception as err:
            print("RTSP Client Lookup Thread stopped:", str(err))

if __name__ == "__main__":
    main()