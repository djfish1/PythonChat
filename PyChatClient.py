#!/usr/bin/env python
import fileinput
import gobject
import gtk
import optparse
import os
import socket
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
    self.text = ''
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
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
    self.textEntry.set_wrap_mode(gtk.WRAP_WORD)
    self.textEntry.set_editable(True)
    self.textEntry.set_cursor_visible(False)  
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_LEFT,1)
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_RIGHT,1)
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_TOP,1)
    self.textEntry.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM,1)
    self.scrollWinForTextBox = gtk.ScrolledWindow()
    self.scrollWinForTextBox.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.scrollWinForTextBox.add(self.textBox)
    self.scrollWinForTextBox.set_size_request(400, 120)
    self.scrollWinForTextEntry = gtk.ScrolledWindow()
    self.scrollWinForTextEntry.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.scrollWinForTextEntry.add(self.textEntry)
    self.scrollWinForTextEntry.set_size_request(300, 40)
    # Submit button
    self.submitButton = gtk.Button('Submit')
    self.submitButton.connect('clicked', self.sendTextHandler)

    #grid = gtk.Grid()
    #grid.attach(self.scrollWinForTextBox, 0, 0, 4, 4)
    #grid.attach(self.scrollWinForTextEntry, 0, 4, 3, 1)
    #grid.attach(self.submitButton, 3, 4, 1, 1) 
    #self.window.add(grid)
    vbox = gtk.VBox(homogeneous=False,spacing=5)
    vbox.pack_start(self.scrollWinForTextBox, expand=True)
    hbox = gtk.HBox(homogeneous=False, spacing=6)
    hbox.set_size_request(400, 40)
    hbox.pack_start(self.scrollWinForTextEntry, expand=True)
    hbox.pack_end(self.submitButton, expand=False)
    vbox.pack_end(hbox, expand=False)
    self.window.add(vbox)
    self.sock = None
    self.done = False
    self.dataGetterThread = threading.Thread(target=self.getDataFromServer)
    self.dataGetterThread.start()
    self.window.show_all()

  def sendText(self, text):
    if self.sock is not None:
      #print 'Sending text:', curText
      self.sock.send(text)

  def sendTextHandler(self, button):
    textBuffer = self.textEntry.get_buffer()
    curText = textBuffer.get_text(textBuffer.get_start_iter() , textBuffer.get_end_iter())
    curText = curText.strip() + os.linesep
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
    self.sendText(os.getenv('USER'))
    while not self.done:
      #print 'Adding line:', line.strip()
      while True:
        if self.done:
          print 'Got a done'
          break
        try:
          if self.sock.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT) != '':
            #print 'Data is available'
            break
        except BaseException as e:
          pass
        time.sleep(0.1)
      if not self.done:
        stringData = self.sock.recv(2056)
        if stringData == '':
          self.done = True
        else:
          gobject.idle_add(self.updateText, stringData)
      else:
        break
    else:
      self.sock.close()

  def updateText(self, line):
    textBuffer = self.textBox.get_buffer()
    #curText = textBuffer.get_text(textBuffer.get_start_iter() , textBuffer.get_end_iter())
    #textBuffer.set_text(os.linesep.join((curText, line.strip(os.linesep))))
    #textBuffer.insert_with_tags(textBuffer.get_end_iter(), line.strip(os.linesep))))
    for keyWord, color in MainForm.recolorDict.items():
      if line.upper().find(keyWord.upper()) >= 0:
        textTag = textBuffer.create_tag(None, foreground=color, family='fixed')
        #textTag.set_property('foreground', color)
        textBuffer.insert_with_tags(textBuffer.get_end_iter(), line, textTag)
        break
    else:
      textBuffer.insert(textBuffer.get_end_iter(), line)

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

