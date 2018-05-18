#!/usr/bin/env python
from __future__ import print_function
import optparse
import os
import socket
import struct
import sys
import threading
import time
import MultiServer

class ChatServer(MultiServer.MultiServer):
  def __init__(self, serverIp=None, serverPort=None):
    MultiServer.MultiServer.__init__(self, serverIp, serverPort)
    threading.Timer(1.0, self.timerEventHandler).start()
    self.start()

  def timerEventHandler(self):
    #print(time.time(), 'Trying to send timer text')
    self.sendDataToAllThreads('')
    if not self.done:
      threading.Timer(1.0, self.timerEventHandler).start()

  def textToBytes(self, text):
    #print('Major verion:', sys.version_info.major)
    if sys.version_info.major == 2:
      #print('Preserving original text,', text)
      retBytes = str(text)
    else:
      retBytes = bytes(text, 'ASCII')
    return retBytes

  def formPayload(self, text):
    strLen = len(text)
    payload = struct.pack('l{0:d}s'.format(strLen), strLen, self.textToBytes(text))
    return payload

  def threadHandler(self, connection, address):
    self.connLock.acquire()
    self.connections.append(connection)
    connection.settimeout(2.0)
    print(time.time(), 'We now have', len(self.connections), 'connections after adding', address)
    self.connLock.release()
    firstMessage = True
    userName = 'NONAME'
    sizeSize = struct.calcsize('l')
    threadDone = False
    while not self.done and not threadDone:
      try:
        payloadSizeData = connection.recv(sizeSize)
      except BaseException as e:
        print(time.time(), 'Error while trying to receive data:', e)
        payloadSizeData = ''
      if payloadSizeData == '' or payloadSizeData == b'':
        print('Received empty data, breaking out of receive loop.')
        threadDone = True
        continue
      #print('Received payloadSizeData:', payloadSizeData)
      (payloadSize,) = struct.unpack('l', payloadSizeData)
      if payloadSize > 0:
        print('Trying to receive payload of size:', payloadSize)
        try:
          stringData = connection.recv(payloadSize)
        except BaseException as e:
          print(time.time(), 'Error while trying to receive data:', e)
          stringData = ''
        stringData = stringData.decode('ASCII')
        if stringData == '':
          threadDone = True
          continue
        else:
          print(time.time(), 'Received:', stringData.strip(), 'from', userName)
          if firstMessage:
            firstMessage = False
            userName = stringData
            message = '/**** Server: ' + userName + ' has connected to the chatroom ****/' + os.linesep
          else:
            message = ''
            splitMess = stringData.split(os.linesep)
            for line in splitMess:
              message += ': '.join((userName, line)) + os.linesep
            #message = ': '.join((userName, stringData))
          self.sendDataToAllThreads(message)
      else:
        pass
        #print('Received heartbeat.')
    else:
      connection.close()
      self.connLock.acquire()
      self.connections.remove(connection)
      print(time.time(), 'We now have', len(self.connections), 'connections after removing', address)
      self.connLock.release()
      self.sendDataToAllThreads(': '.join((userName, 'has left the chat.')) + os.linesep)

if __name__ == "__main__":
  op = optparse.OptionParser()
  op.add_option('-s', '--serverIp', type=str, dest='serverIp', help='Server IP', default=None)
  op.add_option('-p', '--serverPort', type=int, dest='serverPort', help='Server Port', default=None)
  (opts, args) = op.parse_args()
  cs = ChatServer(opts.serverIp, opts.serverPort)

