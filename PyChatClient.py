#!/usr/bin/env python
from __future__ import print_function
import fileinput
useGtk = False
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
  recolorDict = {os.getenv('USER') : '#00a000',
                 'WARNING' : '#d0a000',
                 'ERROR' : '#e00000'}
  def __init__(self, serverIp=None, serverPort=None):
    self.serverIp = serverIp
    self.serverPort = serverPort
    self.connected = False
    self.sock = None
    self.done = False
    self.useGtk = useGtk
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
      frame = tk.Frame(self.root, width=750, height=750)
      frame.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
      frame.columnconfigure(0, weight=10)
      frame.rowconfigure(0, weight=10)
      self.textBox = tk.Text(frame)
      self.textBox.grid(column=0, row=0, columnspan=2, rowspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))
      self.textEntry = tk.Text(frame)
      self.textEntry.grid(column=0, row=1, columnspan=1, rowspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))
      self.submitButton = tk.Button(frame, text="submit", command=self.submitHandler)
      self.submitButton.grid(column=1, row=1, columnspan=1, rowspan=1, sticky=(tk.N, tk.E))
      for keyWord, color in MainForm.recolorDict.items():
        self.textBox.tag_configure(keyWord, foreground=color)

      self.textBox.columnconfigure(0, weight=10)
      self.textBox.rowconfigure(0, weight=10)
      self.textBox.columnconfigure(1, weight=1)
      self.textBox.rowconfigure(1, weight=3)
      #self.root.update_idletasks()
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

  def sendText(self, text):
    strLen = len(text)
    payload = struct.pack('l{0:d}s'.format(strLen), strLen, str(text))
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
    self.sendText(os.getenv('USER'))
    sizeSize = struct.calcsize('l')
    while not self.done:
      try:
        payloadSizeData = self.sock.recv(sizeSize)
      except BaseException as e:
        print('Error trying to receive data:', e)
        self.doBackgroundUpdateText('WARNING: Connection to the server appears to be lost.')
        payloadSizeData = ''
      if payloadSizeData == '':
        self.done = True
        self.connected = False
        continue
      (payloadSize,) = struct.unpack('l', payloadSizeData)
      if payloadSize > 0:
        print('Trying to receive a payload of size:', payloadSize)
        try:
          stringData = self.sock.recv(payloadSize)
        except BaseException as e:
          print('Error trying to receive data:', e)
          self.doBackgroundUpdateText('WARNING: Connection to the server appears to be lost.')
          stringData = ''
        if stringData == '':
          self.done = True
          self.connected = False
        else:
          self.doBackgroundUpdateText(stringData)
      else:
        pass
    else:
      print(time.time(), 'Got a done')
      print(time.time(), 'Closing socket')
      self.sock.close()
    print(time.time(), 'End of getDataFromServer')

  def doBackgroundUpdateText(self, text):
    if self.useGtk:
      gobject.idle_add(self.updateText, text)
    else:
      print('Trying to after_idle add text:', text)
      self.root.after_idle(self.updateText, text)

  def updateText(self, text):
    if self.useGtk:
      textBuffer = self.textBox.get_buffer()
      #fontSizeTag = textBuffer.create_tag(None, scale=1.0, scale_set=True, family='fixed', weight=800)
      #curText = textBuffer.get_text(textBuffer.get_start_iter() , textBuffer.get_end_iter())
      #textBuffer.set_text(os.linesep.join((curText, text.strip(os.linesep))))
      #textBuffer.insert_with_tags(textBuffer.get_end_iter(), text.strip(os.linesep))))
      for keyWord, color in MainForm.recolorDict.items():
        if text.upper().find(keyWord.upper()) >= 0:
          textTag = textBuffer.create_tag(None, foreground=color)
          #textTag.set_property('foreground', color)
          #textBuffer.insert_with_tags(textBuffer.get_end_iter(), text, textTag, fontSizeTag)
          textBuffer.insert_with_tags(textBuffer.get_end_iter(), text, textTag)
          break
      else:
        #textBuffer.insert_with_tags(textBuffer.get_end_iter(), text, fontSizeTag)
        textBuffer.insert_with_tags(textBuffer.get_end_iter(), text)
    else:
      for keyWord, color in MainForm.recolorDict.items():
        if text.upper().find(keyWord.upper()) >= 0:
          self.textBox.insert('end', text, (keyWord, ))
          break
      else:
        self.textBox.insert('end', text)

def main():
  gtk.main()
  
if __name__ == "__main__":
  op = optparse.OptionParser()
  op.add_option('-s', '--serverIp', type=str, dest='serverIp', help='Server IP', default=None)
  op.add_option('-p', '--serverPort', type=int, dest='serverPort', help='Server Port', default=None)
  (opts, args) = op.parse_args()
  mainForm = MainForm(opts.serverIp, opts.serverPort)
  #mainForm.start()
  if mainForm.useGtk:
    gtk.gdk.threads_init()
    gtk.main()
  else:
    tk.mainloop()

