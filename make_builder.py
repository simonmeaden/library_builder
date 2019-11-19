"""

Copyright 2019 Simon Meaden

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

@author: Simon Meaden

"""

from PySide2.QtCore import (
#   Qt,
#   QObject,
  Signal,
  Slot,
  QThread,
  )

import  os, subprocess

      
        
#= MakeBuilder class ============================================================
class MakeBuilder(QThread):
  # # classdocs

  send_message = Signal(str)  # # Sends a message string Qt signal
  send_same_line_message = Signal(str)  # # Sends a message string Qt signal that overwrites the previous line
  finished = Signal()  # # Sends a completed Qt signal
  complete = Signal(str, str)  # Sends the repository name and path as a Qt signal

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self):
    # # Constructor
    QThread.__init__(self)
    
    self.running = True
    self.paths = []
   
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  @Slot()
  def __send_message(self, data):
    self.send_message.emit(data)
        
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  @Slot()
  def __send_same_line_message(self, data):
    self.send_same_line_message.emit(data)
        
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
    # # The worker run method.
    # this connects in the debug breakpoints in a thread
    import pydevd;pydevd.settrace(suspend=False)
    
    while self.running:
      if len(self.paths) > 0:
        data = self.paths.pop(0)
        path = data[0]
        args = data[1]
        
        self.make(path, args)
        
    self.finished.emit()  

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def stop(self):
    # # Stops the worker object.
    #
    # Stops the worker and send a finished signal on completion
    
    self.running = False

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def set_make_paths(self, path):
    
    self.paths.append((path))
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def make(self, path):
    ''''''

    os.chdir(path)
    self.send_message.emit(_('Changed working directory to {}').format(os.getcwd()))

    process = subprocess.run(['make'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             universal_newlines=True)
    
    while True:
      out = process.stdout.readline()
      if out == '' and process.poll() is not None:
        self.send_message.emit(_('Make completed with returncode {}').format(process.returncode))
        self.complete.emit()
        break
      if out:
        self.print_message(out.strip())

    
    
    