#!/usr/bin/env python
import optparse
import os
import socket
import sys
import threading
import time

class ChatServer(object):
  def __init__(self, serverIp=None, serverPort=None):
    self.serverIp = serverIp
    self.serverPort = serverPort

    self.connections = []
    self.connLock = threading.Lock()
    self.sock = socket.socket()
    self.sock.bind((self.serverIp, self.serverPort))
    self.sock.listen(0)
    self.done = False
    self.acceptConnections()

  def acceptConnections(self):
    while True:
      try:
        newThread = threading.Thread(target=self.threadHandler, args=self.sock.accept()).start()
      except KeyboardInterrupt as e:
        print 'Main thread done'
        self.done = True
        break

  def sendDataToAllThreads(self, data):
    self.connLock.acquire()
    for conn in self.connections:
      conn.send(data)
    self.connLock.release()

  def threadHandler(self, connection, address):
    self.connLock.acquire()
    self.connections.append(connection)
    print 'We now have', len(self.connections), 'connections after adding', address
    self.connLock.release()
    firstMessage = True
    userName = 'NONAME'
    while not self.done:
      # Allow the thread to exit
      while True:
        if self.done:
          print 'Got a done'
          break
        try:
          #print 'Trying to peek'
          if connection.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT) != '':
            #print 'Data is available'
            break
        except BaseException as e:
          pass
        time.sleep(0.1)
      if not self.done:
        data = connection.recv(2056)
        if data == '':
          connection.close()
          self.connLock.acquire()
          self.connections.remove(connection)
          print 'We now have', len(self.connections), 'connections after removing', address
          self.connLock.release()
          break
        else:
          print 'Received:', data.strip(), os.linesep
          if firstMessage:
            firstMessage = False
            userName = data
            message = '--------------------' + os.linesep
            message += userName + ' has connected to the chatroom' + os.linesep
            message += '--------------------' + os.linesep
          else:
            message = ': '.join((userName, data))
          self.sendDataToAllThreads(message)

if __name__ == "__main__":
  op = optparse.OptionParser()
  op.add_option('-s', '--serverIp', type=str, dest='serverIp', help='Server IP', default=None)
  op.add_option('-p', '--serverPort', type=int, dest='serverPort', help='Server Port', default=None)
  (opts, args) = op.parse_args()
  cs = ChatServer(opts.serverIp, opts.serverPort)

