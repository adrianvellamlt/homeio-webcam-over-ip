import os
import cv2
import socket
from sys import argv, platform
from time import sleep
from struct import pack
from pickle import dumps
from threading import Thread
from numpy import zeros, uint8

white = (255, 255, 255)

server = None
rtsp_clients = []

def rtsp_setup(port):
    address = os.environ["HOSTNAME"]
    print(address, port)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((address, port))
    server.listen(10)
    return server

def main():
    global server

    # set defaults args
    cap_indx = 0
    port = 8089
    output_size = (480, 640)

    # set args if passed
    if len(argv) == 4:
        cap_indx = int(argv[1])
        port = int(argv[2])
        size = argv[3].split("x")
        output_size = (int(size[1]), int(size[0]))

    cap = cv2.VideoCapture(cap_indx)

    server = rtsp_setup(port)

    clientLookup = RTSPClientLookup()
    clientLookup.start()

    while True:
        ret, img = cap.read()

        if ret == False and img is None:
            # don't send any data unless you have a stream
            cap.release() # release
            cap = cv2.VideoCapture(cap_indx) # retry
            cv2.waitKey(1)
            continue
        else:
            img = cv2.flip(img, 1)

        # resized to desired shape
        if img.shape[0] != output_size[0] or img.shape[1] != output_size[1]: 
            img = cv2.resize(img, output_size)

        data = dumps(img)
        
        for client in rtsp_clients:
            try:
                client[0].sendall(pack("L", len(data)) + data)
            except Exception as err:
                rtsp_clients.remove(client)
                print("Connections dropped: ", client[1], err)
                client[0].close()
        # mandatory for resource conservation
        cv2.waitKey(1)
    # stop looking for new clients
    clientLookup.stop()

# Lookup for new clients to stream to
# This is standard boiler plate code
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
