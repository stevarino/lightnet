# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $

from bluetooth import (BluetoothSocket, RFCOMM, PORT_ANY, SERIAL_PORT_PROFILE.
                       SERIAL_PORT_CLASS)
import socket

server_sock=BluetoothSocket(RFCOMM)
server_sock.bind(("", PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

print("port: ", port)

uuid = "28ccf815-245e-436f-a002-8e72a67422a8"

print("uuid: ", uuid)

advertise_service(server_sock, "LightNet",
                  service_id = uuid,
                  service_classes = [uuid, SERIAL_PORT_CLASS],
                  profiles = [SERIAL_PORT_PROFILE])
                   
print("Waiting for connection on RFCOMM channel %d" % port)

client_sock, client_info = server_sock.accept()
print("Accepted connection from ", client_info)

cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

try:
    while True:
        data = client_sock.recv(1024)
        if len(data) == 0: break
        print("received [%s]" % data)
        cs.sendto(data, ('255.255.255.255', 54545))
except IOError:
    pass

print("disconnected")

client_sock.close()
server_sock.close()
print("all done")
