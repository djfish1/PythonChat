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
        self.sendDataToAllThreads('', '')
        if not self.done:
            threading.Timer(1.0, self.timerEventHandler).start()

    def textToBytes(self, text):
        #print('Major verion:', sys.version_info.major)
        if sys.version_info[0] == 2:
            #print('Preserving original text,', text)
            retBytes = str(text)
        else:
            retBytes = bytes(text, 'ASCII')
        return retBytes

    def formPayload(self, args):
        userName = args[0]
        text = args[1]
        strLen = len(text)
        uLen = len(userName)
        payload = struct.pack('ll{0:d}s{1:d}s'.format(uLen, strLen),
                uLen, strLen, self.textToBytes(userName), self.textToBytes(text))
        return payload

    def threadHandler(self, connection, address):
        self.connLock.acquire()
        self.connections.append(connection)
        connection.settimeout(2.0)
        print(time.time(), 'We now have', len(self.connections), 'connections after adding', address)
        self.connLock.release()
        firstMessage = True
        userName = 'NONAME'
        sizeSize = struct.calcsize('ll')
        threadDone = False
        while not self.done and not threadDone:
            try:
                payloadSizeData = connection.recv(sizeSize)
            except BaseException as e:
                print(time.time(), 'Error while trying to receive data:', e)
                payloadSizeData = ''
            if payloadSizeData == '' or payloadSizeData == b'':
                #print('Received empty data, breaking out of receive loop.')
                threadDone = True
                continue
            #print('Received payloadSizeData:', payloadSizeData)
            (userNameSize, payloadSize) = struct.unpack('ll', payloadSizeData)
            #print('Trying to receive payload of size:', userNameSize + payloadSize)
            try:
                stringData = connection.recv(userNameSize + payloadSize)
            except BaseException as e:
                print(time.time(), 'Error while trying to receive data:', e)
                stringData = b''
            if payloadSize == 0:
                continue # this is a heartbeat
            stringData = stringData.decode('ASCII')
            if stringData == '':
                threadDone = True
                continue
            else:
                timeStr = time.asctime(time.gmtime()) + 'Z'
                message = timeStr + os.linesep
                if firstMessage:
                    firstMessage = False
                    userName = stringData[0:userNameSize]
                    userNameForMessage = 'PyChatServer'
                    message += '/**** ' + userName + ' has connected to the chatroom from ' + str(address) + ' ****/' + os.linesep
                else:
                    userNameForMessage = stringData[0:userNameSize]
                    rawMessage = stringData[userNameSize:]
                    splitMess = rawMessage.split(os.linesep)
                    for line in splitMess:
                        message += ': '.join(('    '+userNameForMessage, line)) + os.linesep
                #print(time.time(), 'Received:', rawMessage, 'from', userName)
                print(message)
                self.sendDataToAllThreads(userNameForMessage, message)
        else:
            connection.close()
            self.connLock.acquire()
            self.connections.remove(connection)
            self.connLock.release()
            print(userName, address, 'has left the chat')
            print(time.time(), 'We now have', len(self.connections), 'connections after removing', address)
            userNameForMessage = 'PyChatServer'
            self.sendDataToAllThreads(userNameForMessage, userName + ' has left the chat ' + str(address) + os.linesep)

if __name__ == "__main__":
    op = optparse.OptionParser()
    op.add_option('-s', '--serverIp', type=str, dest='serverIp', help='Server IP', default=None)
    op.add_option('-p', '--serverPort', type=int, dest='serverPort', help='Server Port', default=None)
    (opts, args) = op.parse_args()
    cs = ChatServer(opts.serverIp, opts.serverPort)

