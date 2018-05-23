#!/usr/bin/env python
import optparse
import os
import socket
import struct
import sys
import threading
import time

class MultiServer(object):
  def __init__(self, serverIp=None, serverPort=None):
    self.serverIp = serverIp
    self.serverPort = serverPort
    self.connections = []
    self.connLock = threading.Lock()
    self.done = False

  def start(self):
    # You can call this in a separate thread as below, but then you have to
    # worrry about doing all the KeyboardInterrupt handling appropriately. It
    # seems cleaner to do it as the main thread.
    #threading.Thread(target=self.acceptConnections).start()
    self.acceptConnections()

  def acceptConnections(self):
    print('Creating socket')
    self.sock = socket.socket()
    print('Binding socket')
    self.sock.bind((self.serverIp, self.serverPort))
    print('Listening to socket')
    self.sock.listen(0)
    while True:
      try:
        newThread = threading.Thread(target=self.threadHandler, args=self.sock.accept()).start()
      except KeyboardInterrupt as e:
        print('Accept connections done')
        self.done = True
        break
    else:
      print('Closing socket')
      self.sock.close()

  def sendDataToAllThreads(self, userName, data):
    payload = self.formPayload(userName, data)
    #if data != '':
    #  print(time.time(), 'Sending payload:', repr(payload))
    self.connLock.acquire()
    connectionsToRemove = []
    for conn in self.connections:
      try:
        conn.send(payload)
      except BaseException as e:
        print(time.time(), 'Unable to send data on connection:', conn, e)
        connectionsToRemove.append(conn)
    for conn in connectionsToRemove:
      print(time.time(), 'Removing connection:', conn)
      self.connections.remove(conn)
    self.connLock.release()


