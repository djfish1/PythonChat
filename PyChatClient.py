#!/usr/bin/env python
import fileinput
import gobject
import gtk
import optparse
import os
import socket
import struct
import sys
import threading
import time

class MainForm:
  recolorDict = {'STATUS' : '#00cc00',
                 'WARNING' : '#d0a000',
                 'ERROR' : '#e00000'}
  def __init__(self, serverIp=None, serverPort=None):
    self.serverIp = serverIp
    self.serverPort = serverPort
    self.connected = False
    self.text = ''
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.get_settings().set_string_property('gtk-font-name', 'monospace bold 10', '')
    self.window.set_title("PyChat")
    self.window.set_default_size(750,450)
    self.window.connect('destroy', self.doQuit)
    # Text Box for viewing
    self.textBox = gtk.TextView()
    self.textBox.set_wrap_mode(gtk.WRAP_WORD)
    self.textBox.set_editable(False)
    self.textBox.set_cursor_visible(False)  
    self.textBox.set_border_window_size(gtk.TEXT_WINDOW_LEFT,1)
    self.textBox.set_border_window_size(gtk.TEXT_WINDOW_RIGHT,1)
    self.textBox.set_border_window_size(gtk.TEXT_WINDOW_TOP,1)
    self.textBox.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM,1)
    # Text Entry
    self.textEntry = gtk.TextView()
    self.textEntry.set_wrap_mode(gtk.WRAP_NONE)
    self.textEntry.set_editable(True)
    self.textEntry.set_cursor_visible(False)  
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_LEFT,1)
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_RIGHT,1)
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_TOP,1)
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM,1)
    #tb = self.textEntry.get_buffer()
    #tb.connect('changed', self.applyFont)
    self.scrollWinForTextBox = gtk.ScrolledWindow()
    self.scrollWinForTextBox.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.scrollWinForTextBox.add(self.textBox)
    self.scrollWinForTextBox.set_size_request(400, 220)
    self.scrollWinForTextEntry = gtk.ScrolledWindow()
    self.scrollWinForTextEntry.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.scrollWinForTextEntry.add(self.textEntry)
    self.scrollWinForTextEntry.set_size_request(300, 60)
    # Submit button
    self.submitButton = gtk.Button('submit')
    self.submitButton.connect('clicked', self.submitHandler)
    accelGroup = gtk.AccelGroup()
    key, mod = gtk.accelerator_parse('<Control>s')
    self.submitButton.add_accelerator('clicked', accelGroup, key, mod, gtk.ACCEL_VISIBLE)

    #grid = gtk.Grid()
    #grid.attach(self.scrollWinForTextBox, 0, 0, 4, 4)
    #grid.attach(self.scrollWinForTextEntry, 0, 4, 3, 1)
    #grid.attach(self.submitButton, 3, 4, 1, 1) 
    #self.window.add(grid)
    vbox = gtk.VBox(homogeneous=False,spacing=5)
    vbox.pack_start(self.scrollWinForTextBox, expand=True)
    hbox = gtk.HBox(homogeneous=False, spacing=6)
    hbox.set_size_request(400, 60)
    hbox.pack_start(self.scrollWinForTextEntry, expand=True)
    hbox.pack_end(self.submitButton, expand=False)
    vbox.pack_end(hbox, expand=False)
    self.window.add(vbox)
    self.window.add_accel_group(accelGroup)
    self.sock = None
    self.done = False
    self.dataGetterThread = threading.Thread(target=self.getDataFromServer)
    self.dataGetterThread.start()
    heartbeat = threading.Timer(1.0, self.timerEventHandler)
    heartbeat.start()
    self.window.show_all()

  #def applyFont(self, textBuffer):
  #  fontSizeTag = textBuffer.create_tag(None, scale=1.0, scale_set=True, family='fixed', weight=800)
  #  textBuffer.apply_tag(fontSizeTag, textBuffer.get_start_iter(), textBuffer.get_end_iter())

  def timerEventHandler(self):
    #print time.time(), 'Trying to send timer text'
    self.sendText('')
    if not self.done and self.connected:
      threading.Timer(1.0, self.timerEventHandler).start()

  def sendText(self, text):
    strLen = len(text)
    payload = struct.pack('l{0:d}s'.format(strLen), strLen, text)
    #if text != '':
    #  print time.time(), 'Sending payload:', repr(payload)
    if (self.sock is not None) and (not self.done) and self.connected:
      #print 'Sending text:', curText
      self.sock.send(payload)

  def submitHandler(self, button):
    textBuffer = self.textEntry.get_buffer()
    curText = textBuffer.get_text(textBuffer.get_start_iter() , textBuffer.get_end_iter())
    curText = curText.strip().strip(os.linesep)
    self.sendText(curText)
    textBuffer.set_text('')

  def doQuit(self, button):
    self.done = True
    if self.sock is not None:
      self.sock.close()
    self.dataGetterThread.join()
    gtk.main_quit()

  def getDataFromServer(self):
    self.sock = socket.socket()
    self.sock.connect((self.serverIp, self.serverPort))
    self.connected = True
    self.sock.settimeout(2.0)
    self.sendText(os.getenv('USER'))
    sizeSize = struct.calcsize('l')
    while not self.done:
      #print 'Adding line:', line.strip()
      payloadSizeData = self.sock.recv(sizeSize)
      if payloadSizeData == '':
        self.done = True
        self.connected = False
        continue
      (payloadSize,) = struct.unpack('l', payloadSizeData)
      #print 'Trying to receive a payload of size:', payloadSize
      if payloadSize > 0:
        stringData = self.sock.recv(payloadSize)
        if stringData == '':
          self.done = True
          self.connected = False
        else:
          gobject.idle_add(self.updateText, stringData)
      else:
        pass
    else:
      print time.time(), 'Got a done'
      self.updateText('WARNING: Connection to the server appears to be lost.')
      self.sock.close()

  def updateText(self, line):
    textBuffer = self.textBox.get_buffer()
    #fontSizeTag = textBuffer.create_tag(None, scale=1.0, scale_set=True, family='fixed', weight=800)
    #curText = textBuffer.get_text(textBuffer.get_start_iter() , textBuffer.get_end_iter())
    #textBuffer.set_text(os.linesep.join((curText, line.strip(os.linesep))))
    #textBuffer.insert_with_tags(textBuffer.get_end_iter(), line.strip(os.linesep))))
    for keyWord, color in MainForm.recolorDict.items():
      if line.upper().find(keyWord.upper()) >= 0:
        textTag = textBuffer.create_tag(None, foreground=color)
        #textTag.set_property('foreground', color)
        #textBuffer.insert_with_tags(textBuffer.get_end_iter(), line, textTag, fontSizeTag)
        textBuffer.insert_with_tags(textBuffer.get_end_iter(), line, textTag)
        break
    else:
      #textBuffer.insert_with_tags(textBuffer.get_end_iter(), line, fontSizeTag)
      textBuffer.insert_with_tags(textBuffer.get_end_iter(), line)

def main():
  gtk.main()
  
if __name__ == "__main__":
  op = optparse.OptionParser()
  op.add_option('-s', '--serverIp', type=str, dest='serverIp', help='Server IP', default=None)
  op.add_option('-p', '--serverPort', type=int, dest='serverPort', help='Server Port', default=None)
  (opts, args) = op.parse_args()
  mainForm = MainForm(opts.serverIp, opts.serverPort)
  gtk.gdk.threads_init()
  gtk.main()

