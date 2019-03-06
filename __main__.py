import cv2
import socket
from sys import argv, platform
from time import sleep
from struct import pack
from pickle import dumps
from threading import Thread
from numpy import zeros, uint8
from subprocess import run, PIPE

white = (255, 255, 255)

shape = (480, 640)
offlineStreamImg = zeros((shape), dtype=uint8)
textsize = cv2.getTextSize("Stream Offline", cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
centreCoords = ( int((shape[1] - textsize[0]) / 2), int((shape[0] + textsize[1]) / 2) )
cv2.putText(offlineStreamImg, "Stream Offline", centreCoords, cv2.FONT_HERSHEY_SIMPLEX, 1, (69, 53, 220), 2)

server = None
rtsp_clients = []

def rtsp_setup(port):
    address = socket.gethostbyname(socket.gethostname())
    if address.startswith("127.") and (platform == "linux" or platform == "linux2"):
        address = str(run("hostname -I", shell=True, stdout=PIPE).stdout)
        address = address.replace("\\n", "").replace(" ", "")[2:-1]
    print(address, port)
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

        if ret == False and img is None:
            cap.release() # release
            cap = cv2.VideoCapture(cap_indx) # retry
            img = offlineStreamImg
            # cv2.imshow(title, offlineStreamImg)
        else:
            img = cv2.flip(img, 1)

        data = dumps(img)
        
        for client in rtsp_clients:
            try:
                client[0].sendall(pack("L", len(data)) + data)
            except Exception as err:
                rtsp_clients.remove(client)
                print("Connections dropped: ", client[1], err)
                client[0].close()

        # cv2.imshow(title, img)
        cv2.waitKey(1)
    
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
