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
#  Qt,
  QThread,
  Signal,
#   Slot,
  )
import shutil, subprocess
from contextlib import suppress
# from pygit2 import clone_repository, RemoteCallbacks
# from git import RemoteProgress
# from git.repo.base import Repo

from common_types import ExistAction



#= BaseReader class =================================================================
class BaseReader(QThread):
  ## The BaseReader class stores basic information of all Reader classes.
  #
  # Stores path, name and the action to take if a copy of the repository 
  # already exists locally.
  
  send_message = Signal(str) ## Sends a message string Qt signal
  send_repo_path = Signal(str, str) # Sends the repository name and path via a Qt signal

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, download_path, repo_name, exist_action=ExistAction.SKIP, parent=None):
    ## Constructor
    #
    # The GitReader constructor takes an optional progress monitor object as a parameter.
    #
    # /param remote - optional GitProgress object
    QThread.__init__(self, parent)
    
#     print("Initalising BaseReader for {}".format(repo_name))
    self.download_path = download_path
    self.repo_name = repo_name
    self.exist_action = exist_action
    self.repo_path = download_path / repo_name
    self.running = True
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def create_download_path(self):
    if not self.download_path.exists():  # should already be
      self.download_path.mkdir(parents=True, exist_ok=True)
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def backup_if_needed(self):
    
    if self.repo_path.exists():
      self.send_message.emit(_('Path {} already exists. Exist action is {}').format(str(self.repo_path), repr(self.exist_action)))
      if self.exist_action == ExistAction.SKIP:
        self.send_message.emit('Action is Skip - loading local repository')
        return
  
      elif self.exist_action == ExistAction.OVERWRITE:
        self.send_message.emit(_('Action is Overwrite - deleting existing directory'))
        shutil.rmtree(self.repo_path)
  
      elif self.exist_action == ExistAction.BACKUP:
        # renames to PATH.old, deleting any existing PATH.old directory. 
        # TODO maybe to version ?
        self.send_message.emit(_('Action is Backup - backing up existing directory'))
        destination = self.download_path / '{}{}'.format(self.repo_name, '.old')
        self.send_message.emit(_('{} directory already exists!').format(self.repo_name))
        self.send_message.emit(_('Saving old version to {}').format(destination.name))
        
        if destination.exists():
          self.send_message.emit(_('A version of {} already exists. Deleting it!').format(destination.name))
          shutil.rmtree(destination)
          
        self.repo_path.rename(destination)
  
      else:
        self.send_message.emit(_('Invalid exist_action - stopping process'))
        return 

#= End of BaseReader class ==================================================================





      
#= BaseUrlReader class ==============================================================
class BaseUrlReader(BaseReader):   
  ## The BaseUrlReader class extends the BaseReader class to store URL information.
  #
  
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, download_path, repo_name, repo_url, exist_action=ExistAction.SKIP, parent=None):
    ## Constructor
    #
    # The GitReader constructor takes an optional progress monitor object as a parameter.
    #
    # /param remote - optional GitProgress object
    BaseReader.__init__(self, download_path, repo_name, exist_action, parent)
    
#     print("Initalising BaseUrlReader for {}".format(self.repo_name))
    self.repo_url = repo_url

#= End of BaseUrlReader class ==================================================================






#= GitReader class ==================================================================
class GitReader(BaseUrlReader):
  ## The GitReader class clones the specified remote repository into you specified directory.
  #
  # The GitReader class is used to clone a GIT repository into a local download directory.
  # 
  # GitReader runs as  a separate thread so the master application does not block. Data about
  # the required repository, the library name and the download directory is passed when the 
  # thread is initialised and the library name and download directory are passed back to 
  # the application via a Qt send_repo_path signal when the download is completed.

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, download_path, repo_name, repo_url, exist_action=ExistAction.SKIP, parent= None):
    ## Constructor
    #
    # The GitReader constructor takes an optional progress monitor object as a parameter.
    #
    # /param remote - optional GitProgress object
    BaseUrlReader.__init__(self, download_path, repo_name, repo_url, exist_action, parent)
    
    # this connects in the debug breakpoints in a thread
#     import pydevd; pydevd.settrace(suspend=False)
#     print("Initalising GitReader for {}".format(self.repo_name))

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
     
    while self.running:
      
      self.create_download_path()
      self.backup_if_needed()
        
#       with suppress(TypeError): # didn't work damn it
    
      self.send_message.emit(_('Starting Git clone of {}').format(self.repo_name))
      self.send_message.emit(_('Downloading {} might take some time if a large repository').format(self.repo_name))
      process = subprocess.Popen([b'git', 
                                  b'clone', 
                                  bytes(str(self.repo_url), 'utf-8'),
                                  bytes(str(self.repo_path), 'utf-8')],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True)
      while True:
        # I attempted to catch the progress bars from Mercurial but
        # it seems that they are not sent to stdout OR stderr so can't find them.
        out = process.stdout.readline()#.encode('utf-8')
        if out == '' and process.poll() is not None:
          self.send_message.emit(_('Completed Git clone of {}').format(self.repo_name))
          self.send_repo_path.emit(self.repo_name, str(self.repo_path))
          self.running = False
          break
        if out:
          self.send_message.emit(out)      
          self.msleep(100)    

           
    self.finished.emit()  
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def stop(self):
    ## Stops the worker object.
    #
    # Stops the worker and send a finished signal on completion
    
    self.running = False
   
#= End of GitReader class ==================================================================     
        
#= MercurialReader class ============================================================
class MercurialReader(BaseUrlReader):
  # # classdocs

  send_same_line_message = Signal(str)  # # Sends a message string Qt signal that overwrites the previous line

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, download_path, repo_name, repo_url, exist_action=ExistAction.SKIP):
    # # Constructor
    BaseUrlReader.__init__(self)
    # this connects in the debug breakpoints in a thread
#     import pydevd;pydevd.settrace(suspend=False) 
       
        
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
    

    while self.running:
        
      self.create_download_path()
      self.backup_if_needed()

      self.send_message.emit(_('Starting Mercurial clone of {}').format(self.repo_name))
      self.send_message.emit(_('Downloading {} might take some time if a large repository').format(self.repo_name))
      process = subprocess.Popen([b'hg', 
                                  b'clone', 
                                  bytes(str(self.repo_url), 'utf-8'),
                                  bytes(str(self.repo_path), 'utf-8')],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True)
      while True:
        # I attempted to catch the progress bars from Mercurial but
        # it seems that they are not sent to stdout OR stderr so can't find them.
        out = process.stdout.readline()
        if out == '' and process.poll() is not None:
          self.send_message.emit(_('Completed Mercurial clone of {}').format(self.repo_name))
          self.send_repo_path.emit(self.repo_name, str(self.repo_path))
          self.running = False
          break
        if out:
          self.send_message.emit(out.strip())      
          self.msleep(100)
        
    self.finished.emit()  

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def stop(self):
    # # Stops the worker object.
    #
    # Stops the worker and send a finished signal on completion
    
    self.running = False

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
    

