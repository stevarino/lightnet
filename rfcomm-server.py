'''
RFCOMM Server - Serial Over Bluetooth to UDP Broadcast
Based on https://github.com/karulis/pybluez/blob/master/examples/simple/rfcomm-server.py
'''

import argparse
import contextlib
import os.path as path
import socket
import traceback
import yaml

from bluetooth import (BluetoothSocket, RFCOMM, PORT_ANY, SERIAL_PORT_PROFILE,
                       SERIAL_PORT_CLASS, advertise_service)

class RfcommServer(object):
    '''An RFComm Server designed to propagate bluetooth messages to UDP broadcasts.'''
    def __init__(self, establish_bt=True):
        folder = path.dirname(path.abspath(__file__))
        try:
            with open(path.join(folder, 'settings.yaml')) as settings_file:
                self.settings = yaml.safe_load(settings_file)
        except FileNotFoundError:
            print("Create a settings.yaml file by copying settings-example.yaml")
            raise
        self.server_sock = None
        self.client_sock = None
        if establish_bt:
            self.server_sock = BluetoothSocket(RFCOMM)
            self.server_sock.bind(("", PORT_ANY))
            self.server_sock.listen(1)
            uuid = "28ccf815-245e-436f-a002-8e72a67422a8"

            # doesn't appear to do anything on RasPi...
            advertise_service(self.server_sock, "LightNet",
                              service_id=uuid,
                              service_classes=[uuid, SERIAL_PORT_CLASS],
                              profiles=[SERIAL_PORT_PROFILE])

        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def loop(self, gen=None):
        '''Listen for and handle bluetooth commands.'''
        if not gen:
            gen = self.command_generator()
        broadcast_dest = (self.settings['broadcast']['ip'],
                          self.settings['broadcast']['port'])
        for command in gen:
            print("received [{}]".format(command))
            self.broadcast_socket.sendto(command, broadcast_dest)
            self.respond('okay')
            
        print("all done")

    def respond(self, msg):
        '''Send a bluetooth response if connected.'''
        if not self.client_sock:
            return
        self.client_sock.send(msg)

    def command_generator(self):
        '''Establishes a client connection, yielding any commands given and
        raising StopIteration upon close. '''
        whitelist = self.settings.get('whitelist', [])
        while True:
            print("Waiting for connection on RFCOMM channel")
            client_sock, client_info = self.server_sock.accept()
            if whitelist and not client_info in whitelist:
                print("Denied connection from ", client_info)
                client_sock.close()
                continue
            print("Accepted connection from ", client_info)
            self.client_sock = client_sock

            while True:
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        raise StopIteration
                    yield data
                except IOError:
                    traceback.print_exc()
                except (KeyboardInterrupt, SystemExit, StopIteration):
                    raise
                finally:
                    print("disconnected")
                    self.client_sock = None
                    client_sock.close()

    def close(self):
        '''Closes the server connection if open.'''
        if self.server_sock:
            self.server_sock.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--commands', '-c', nargs='*',
                        help='One or more commands to be passed on to the listener.')
    args = parser.parse_args()

    if args.commands:
        server = RfcommServer(establish_bt=False)
        server.loop((c.encode('utf-8') for c in args.commands))
    else:
        server = RfcommServer()
        with contextlib.closing(server):
            server.loop()
