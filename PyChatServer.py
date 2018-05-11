#!/usr/bin/env python
import optparse
import os
import socket
import struct
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
    heartbeat = threading.Timer(1.0, self.timerEventHandler)
    heartbeat.start()
    self.acceptConnections()

  def timerEventHandler(self):
    #print time.time(), 'Trying to send timer text'
    self.sendDataToAllThreads('')
    if not self.done:
      threading.Timer(1.0, self.timerEventHandler).start()

  def acceptConnections(self):
    while True:
      try:
        newThread = threading.Thread(target=self.threadHandler, args=self.sock.accept()).start()
      except KeyboardInterrupt as e:
        print 'Main thread done'
        self.done = True
        break

  def sendDataToAllThreads(self, text):
    strLen = len(text)
    payload = struct.pack('l{0:d}s'.format(strLen), strLen, text)
    #if text != '':
    #  print time.time(), 'Sending payload:', repr(payload)
    self.connLock.acquire()
    for conn in self.connections:
      conn.send(payload)
    self.connLock.release()

  def threadHandler(self, connection, address):
    self.connLock.acquire()
    self.connections.append(connection)
    connection.settimeout(2.0)
    print time.time(), 'We now have', len(self.connections), 'connections after adding', address
    self.connLock.release()
    firstMessage = True
    userName = 'NONAME'
    sizeSize = struct.calcsize('l')
    threadDone = False
    while not self.done and not threadDone:
      payloadSizeData = connection.recv(sizeSize)
      if payloadSizeData == '':
        print 'Received empty data, breaking out of receive loop.'
        threadDone = True
        continue
      (payloadSize,) = struct.unpack('l', payloadSizeData)
      if payloadSize > 0:
        print 'Trying to receive payload of size:', payloadSize
        stringData = connection.recv(payloadSize)
        if stringData == '':
          threadDone = True
          continue
        else:
          print time.time(), 'Received:', stringData.strip(), 'from', userName
          if firstMessage:
            firstMessage = False
            userName = stringData
            message = '--------------------' + os.linesep
            message += userName + ' has connected to the chatroom' + os.linesep
            message += '--------------------' + os.linesep
          else:
            message = ''
            splitMess = stringData.split(os.linesep)
            for line in splitMess:
              message += ': '.join((userName, line)) + os.linesep
            #message = ': '.join((userName, stringData))
          self.sendDataToAllThreads(message)
      else:
        pass
        #print 'Received heartbeat.'
    else:
      connection.close()
      self.connLock.acquire()
      self.connections.remove(connection)
      print time.time(), 'We now have', len(self.connections), 'connections after removing', address
      self.connLock.release()

if __name__ == "__main__":
  op = optparse.OptionParser()
  op.add_option('-s', '--serverIp', type=str, dest='serverIp', help='Server IP', default=None)
  op.add_option('-p', '--serverPort', type=int, dest='serverPort', help='Server Port', default=None)
  (opts, args) = op.parse_args()
  cs = ChatServer(opts.serverIp, opts.serverPort)

