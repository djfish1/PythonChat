#!/usr/bin/env python
from __future__ import print_function
import fileinput
useGtk = True
try:
  import gobject
  import gtk
except:
  print('Unable to import GTK')
  useGtk = False
import optparse
import os
import socket
import struct
import sys
import threading
import time
try:
  import Tkinter as tk
except:
  try:
    import tkinter as tk
  except:
    print('Unable to import tkinter')

class MainForm:
  def __init__(self, opts):
    self.serverIp = opts.serverIp
    self.serverPort = opts.serverPort
    self.connected = False
    self.sock = None
    self.done = False
    self.useGtk = useGtk
    if hasattr(opts, 'userName') and opts.userName is not None:
      self.userName = userName
    else:
      self.userName = os.getenv('USER')
    self.recolorDict = {self.userName : '#00a000',
                   'WARNING' : '#d0a000',
                   'ERROR' : '#e00000'}
    if self.useGtk:
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
      self.start()
      self.window.show_all()
    else:
      self.root = tk.Tk()
      self.root.protocol('WM_DELETE_WINDOW', self.doQuit)
      #contentFrame = tk.Frame()
      frame = tk.Frame(self.root)#, width=60, height=400)
      frame.grid(column=0, row=0, sticky=(tk.N + tk.E + tk.W + tk.S))
      frame.rowconfigure(0, weight=5)
      frame.rowconfigure(1, weight=1)
      frame.columnconfigure(0, weight=10)
      frame.columnconfigure(1, weight=1)
      frame.columnconfigure(2, weight=2)
      frame.columnconfigure(3, weight=1)
      tbScrollbar = tk.Scrollbar(frame)
      tbScrollbar.grid(column=3, row=0, columnspan=1, rowspan=1, sticky=(tk.N+tk.W+tk.S))
      self.textBox = tk.Text(frame, width=60, height=30, wrap=tk.WORD, state=tk.DISABLED)
      self.textBox.grid(column=0, row=0, columnspan=3, rowspan=1, sticky=(tk.N + tk.E + tk.W))
      self.textBox.config(yscrollcommand=tbScrollbar.set)
      tbScrollbar.config(command=self.textBox.yview)
      teScrollbar = tk.Scrollbar(frame)
      teScrollbar.grid(column=1, row=1, columnspan=1, rowspan=1, sticky=(tk.N+tk.S+tk.W))
      self.textEntry = tk.Text(frame, width=60, height=5, wrap=tk.WORD, state=tk.NORMAL)
      self.textEntry.grid(column=0, row=1, columnspan=1, rowspan=1, sticky=(tk.E + tk.W))
      self.textEntry.config(yscrollcommand=teScrollbar.set)
      teScrollbar.config(command=self.textEntry.yview)
      self.textEntry.focus()
      self.submitButton = tk.Button(frame, text="submit", command=self.submitHandler)
      self.submitButton.grid(column=2, row=1, columnspan=2, rowspan=1, sticky=(tk.S + tk.E))
      for keyWord, color in self.recolorDict.items():
        self.textBox.tag_configure(keyWord, foreground=color, background='#dddddd', lmargin1=50, lmargin2=50)

      frame.pack()
      self.start()

  def start(self):
    self.dataGetterThread = threading.Thread(target=self.getDataFromServer)
    #self.dataGetterThread.daemon = True
    self.dataGetterThread.start()
    heartbeat = threading.Timer(1.0, self.timerEventHandler)
    heartbeat.start()

  #def applyFont(self, textBuffer):
  #  fontSizeTag = textBuffer.create_tag(None, scale=1.0, scale_set=True, family='fixed', weight=800)
  #  textBuffer.apply_tag(fontSizeTag, textBuffer.get_start_iter(), textBuffer.get_end_iter())

  def timerEventHandler(self):
    #print(time.time(), 'Trying to send timer text')
    if not self.done and self.connected:
      self.sendText('')
      threading.Timer(1.0, self.timerEventHandler).start()

  def textToBytes(self, text):
    #print('Major verion:', sys.version_info.major)
    if sys.version_info.major == 2:
      #print('Preserving original text,', text)
      retBytes = str(text)
    else:
      retBytes = bytes(text, 'ASCII')
    return retBytes

  def sendText(self, text):
    strLen = len(text)
    uLen = len(self.userName)
    payload = struct.pack('ll{0:d}s{1:d}s'.format(uLen, strLen),
        uLen, strLen, self.textToBytes(self.userName), self.textToBytes(text))
    #if text != '':
    #  print(time.time(), 'Sending payload:', repr(payload))
    if (self.sock is not None) and (not self.done) and self.connected:
      #print('Sending text:', curText)
      self.sock.send(payload)

  def submitHandler(self, button=None):
    if self.useGtk:
      textBuffer = self.textEntry.get_buffer()
      curText = textBuffer.get_text(textBuffer.get_start_iter() , textBuffer.get_end_iter())
      curText = curText.strip().strip(os.linesep)
      self.sendText(curText)
      textBuffer.set_text('')
    else:
      curText = self.textEntry.get('1.0', 'end')
      curText = curText.strip().strip(os.linesep)
      self.sendText(curText)
      self.textEntry.delete('1.0', 'end')

  def doQuit(self, button=None):
    self.done = True
    if self.sock is not None:
      self.sock.close()
    print('Waiting to join threads')
    self.dataGetterThread.join()
    print('Threads joined')
    if self.useGtk:
      gtk.main_quit()
    else:
      tk.Tk().quit()
      tk.Tk().destroy()
    print('Done quitting')

  def getDataFromServer(self):
    self.sock = socket.socket()
    self.sock.connect((self.serverIp, self.serverPort))
    self.connected = True
    print(time.time(), 'Succussfully connected to', self.serverIp)
    self.sock.settimeout(2.0)
    self.sendText(self.userName)
    sizeSize = struct.calcsize('ll')
    while not self.done:
      try:
        payloadSizeData = self.sock.recv(sizeSize)
      except BaseException as e:
        print('Error trying to receive data:', e)
        #self.doBackgroundUpdateText('WARNING: Connection to the server appears to be lost.')
        payloadSizeData = ''
      if payloadSizeData == '' or payloadSizeData == b'':
        self.done = True
        self.connected = False
        continue
      (uNameSize, payloadSize) = struct.unpack('ll', payloadSizeData)
      if payloadSize > 0:
        #print('Trying to receive a payload of size:', payloadSize)
        try:
          stringData = self.sock.recv(uNameSize + payloadSize)
        except BaseException as e:
          print('Error trying to receive data:', e)
          #self.doBackgroundUpdateText('WARNING: Connection to the server appears to be lost.')
          stringData = ''
        stringData = stringData.decode('ASCII')
        if stringData == '':
          self.done = True
          self.connected = False
        else:
          self.doBackgroundUpdateText(stringData[0:uNameSize], stringData[uNameSize:])
      else:
        pass
    else:
      print(time.time(), 'Got a done')
      print(time.time(), 'Closing socket')
      self.sock.close()
    print(time.time(), 'End of getDataFromServer')

  def doBackgroundUpdateText(self, userName, text):
    if self.useGtk:
      gobject.idle_add(self.updateText, userName, text)
    else:
      print('Trying to after_idle add text:', text, 'from user:', userName)
      self.root.after_idle(self.updateText, userName, text)

  def updateText(self, userName, text):
    #textToAdd = userName + ':' + os.linesep + text
    textToAdd = text
    if self.useGtk:
      textBuffer = self.textBox.get_buffer()
      for keyWord, color in self.recolorDict.items():
        if userName.upper() == keyWord.upper():
          textTag = textBuffer.create_tag(None, foreground=color)
          textBuffer.insert_with_tags(textBuffer.get_end_iter(), textToAdd, textTag)
          break
      else:
        textBuffer.insert_with_tags(textBuffer.get_end_iter(), textToAdd)
    else:
      self.textBox.config(state=tk.NORMAL)
      for keyWord, color in self.recolorDict.items():
        if userName.upper() == keyWord.upper():
          self.textBox.insert('end', textToAdd, (keyWord, ))
          break
      else:
        self.textBox.insert('end', textToAdd)
      self.textBox.config(state=tk.DISABLED)

def main():
  gtk.main()
  
if __name__ == "__main__":
  op = optparse.OptionParser()
  op.add_option('-s', '--serverIp', type=str, dest='serverIp', help='Server IP', default=None)
  op.add_option('-p', '--serverPort', type=int, dest='serverPort', help='Server Port', default=None)
  #op.add_option('-u', '--userName', type=str, dest='userName', help='User name (debug only)', default=None)
  (opts, args) = op.parse_args()
  mainForm = MainForm(opts)
  #mainForm.start()
  if mainForm.useGtk:
    gtk.gdk.threads_init()
    gtk.main()
  else:
    tk.mainloop()

