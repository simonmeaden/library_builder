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
  QObject,
  QThread,
  )
# import hglib
import shutil, subprocess, pathlib, time, sys
from twisted.internet import protocol
from twisted.internet import reactor

# from hglib.error import CapabilityError as HgCapabilityError
# from hglib.error import CommandError as HgCommandError
# from hglib.error import ResponseError as HgResponseError
# from hglib.error import ServerError as HgServerError
# import pathlib

from common_types import ExistAction

#= Twisted.internet ProcessProtocol class ===========================================
class MyPP(QObject, protocol.ProcessProtocol):
  
  send_message = Signal(str)  # # Sends a message string Qt signal

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self):
    # # Constructor
    QObject.__init__(self)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def connectionMade(self):
      pass
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def outReceived(self, data):
    self.send_message.emit(data.decode('utf-8'))
#         sys.stdout.write(data)
#         sys.stdout.flush()
      
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def errReceived(self, data):
    self.send_message.emit('Error : {}'.format(data.decode('utf-8')))
#         sys.stderr.write(data)
#         sys.stderr.flush()
      
  def inConnectionLost(self):
      pass
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def outConnectionLost(self):
      pass
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def errConnectionLost(self):
      pass
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def processExited(self, reason):
      pass
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def processEnded(self, reason):
      pass
      reactor.stop()
    
      
        
#= MercurialReader class ============================================================
class MercurialReader(QThread):
  # # classdocs

  send_message = Signal(str)  # # Sends a message string Qt signal
  finished = Signal()  # # Sends a completed Qt signal
  send_repo_path = Signal(str, str)  # Sends the repository name and path as a Qt signal

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, exist_action=ExistAction.SKIP):
    # # Constructor
    QThread.__init__(self)
    
    self.running = True
    self.exist_action = exist_action
    self.download_paths = []
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  @Slot()
  def __send_message(self, data):
    self.send_message.emit(data)
        
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
    # # The worker run method.
    # this connects in the debug breakpoints in a thread
    import pydevd;pydevd.settrace(suspend=False)
    
    while self.running:
      if len(self.download_paths) > 0:
        data = self.download_paths.pop(0)
        repo_name = data[0]
        download_path = data[1]
        repo_url = data[2]
#         exist_action = data[3]
        
        self.clone_repo(download_path, repo_name, repo_url)
        
    self.finished.emit()  

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def stop(self):
    # # Stops the worker object.
    #
    # Stops the worker and send a finished signal on completion
    
    self.running = False

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def set_clone_paths(self, download_path, repo_name, repo_url, exist_action=ExistAction.NONE):
    
    self.download_paths.append((repo_name, download_path, repo_url, exist_action))
    
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def clone_repo(self, download_path, repo_name, repo_url):
    ''''''

    repo_path = download_path / repo_name
    
#     repo = hglib.repository(repo_url)
#     self.send_message.emit("Mercurial URL : {}".format(str(repo_url)))
#     self.send_message.emit("Mercurial DL path : {}".format(str(download_path)))
#     self.send_message.emit("Mercurial repo path : {}".format(repo_path))
    print("Mercurial URL : {}".format(str(repo_url)))
    print("Mercurial DL path : {}".format(str(download_path)))
    print("Mercurial repo path : {}".format(repo_path))
#     repo_path.mkdir(parents=True, exist_ok=True)
    if repo_path.exists():
      self.send_message.emit(_('Path {} already exists').format(str(repo_path)))
      if self.exist_action == ExistAction.SKIP:
        self.send_message.emit('exist_action == Skip - loading local repository')
        return
  
      elif self.exist_action == ExistAction.OVERWRITE:
        self.send_message.emit(_('exist_action == Overwrite - deleting existing directory'))
        shutil.rmtree(repo_path)
  
      elif self.exist_action == ExistAction.BACKUP:
        self.send_message.emit(_('exist_action == Backup - backing up existing directory'))
        destination = repo_path / '.old'
        if destination.exists():
          shutil.rmtree(destination)
        shutil.copytree(repo_path, destination)
        shutil.rmtree(repo_path)
  
      else:
        self.send_message.emit(_('Invalid exist_action - stopping process'))
        return
      
      
    pp = MyPP()
    pp.send_message.connect(self.__send_message)
    reactor.spawnProcess(pp, 
                         "hg", 
                         ['hg', 'clone', repo_url, str(repo_path)],
#                          env = '/home/simonmeaden/.local/share/virtualenvs/bin/python',
                         usePTY = True)
    reactor.run()
    
#     self.send_message.emit(_('Preparing to download {} to {}').format(repo_name, repo_path))
#     proc_args = ['hg', 'clone', repo_url, str(repo_path)]
#     clone_process = subprocess.Popen(proc_args, 
# #                                      shell=True, 
#                                      stdout=subprocess.PIPE,
# #                                      stderr=subprocess.STDOUT, 
#                                      universal_newlines=True)
# #     stdout_value = clone_process.communicate()[0].decode('utf-8')
#     self.send_message.emit(_('Download starting'))
#     while clone_process.poll() is None:
# #         line = clone_process.stdout.readline()
#         line = clone_process.stdout.read(1)
#         if line:
#           self.send_message.emit(line)
# #         print("Print:" + line)        
# #         print(clone_process.returncode)
#     self.send_message.emit(_('Download of {} complete').format(repo_name))
    
#       hg clone http://selenic.com/hg
  
#     hglib.clone(source='http://hg.libsdl.org/SDL', dest='/home/simonmeaden/workspace/LibraryBuilder/downloads/SDL')#dest=str(repo_path))

#     try:
# #       hglib.clone(repo_url, str(repo_path))
#       hglib.clone(source='http://hg.libsdl.org/SDL', dest='/home/simonmeaden/workspace/LibraryBuilder/downloads/SDL')#dest=str(repo_path))
# #     self.send_repo_path.emit(repo_name, str(repo_path))
#     except (HgCommandError, HgResponseError, HgCapabilityError, HgServerError) as err:
# #       # it might already have existed
# #     self.send_message.emit("Mercurial local repo initialization failed: {}".format(err))
#       self.send_message.emit("Args: {}".format(err.args))
#       self.send_message.emit("Error: {}".format(err))
# #       raise err
    
    
