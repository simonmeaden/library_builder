'''
Created on 19 Nov 2019

@author: simonmeaden
'''

from PySide2.QtCore import (
#   Qt,
#   QObject,
  Signal,
  Slot,
  QObject,
  QThread,
  )
# import hglib
import  subprocess
import shutil

      
        
#= ConfigureBuilder class ============================================================
class ConfigureBuilder(QThread):
  # # classdocs

  send_message = Signal(str)  # # Sends a message string Qt signal
  send_same_line_message = Signal(str)  # # Sends a message string Qt signal that overwrites the previous line
  finished = Signal()  # # Sends a completed Qt signal
  send_repo_path = Signal(str, str)  # Sends the repository name and path as a Qt signal

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, path):
    # # Constructor
    QThread.__init__(self)
    
    self.running = True
    self.path = path
   
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
    
    if repo_path.exists():
      self.send_message.emit(_('Path {} already exists').format(str(repo_path)))
      if self.exist_action == ExistAction.SKIP:
        self.send_message.emit('Exist Action == Skip - using existing local repository')
        self.send_repo_path.emit(repo_name, str(repo_path))
        return
  
      elif self.exist_action == ExistAction.OVERWRITE:
        self.send_message.emit(_('Exist Action == Overwrite - deleting existing directory'))
        shutil.rmtree(repo_path)
  
      elif self.exist_action == ExistAction.BACKUP:
        # renames to PATH.old, deleting any existing PATH.old directory. 
        # TODO maybe to version ?
        self.send_message.emit(_('Exist Action == Backup - backing up existing directory'))
        destination = download_path / '{}{}'.format(repo_name, '.old')
        self.send_message.emit(_('{} directory already exists!').format(repo_name))
        self.send_message.emit(_('Saving old version to {}').format(destination.name))
        
        if destination.exists():
          self.send_message.emit(_('A version of {} already exists. Deleting it!').format(destination.name))
          shutil.rmtree(destination)
          
        repo_path.rename(destination)
  
      else:
        self.send_message.emit(_('Invalid exist_action - stopping process'))
        return
      
    self.send_message.emit(_('Starting Mercurial clone of {}').format(repo_name))
    self.send_message.emit(_('Downloading {} might take some time if a large repository').format(repo_name))
    process = subprocess.Popen([b'hg', 
                                b'clone', 
                                str(repo_url).encode('utf-8'),
                                str(repo_path).encode('utf-8')],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True)
    while True:
      # I attempted to catch the progress bars from Mercurial but
      # it seems that they are not sent to stdout OR stderr so can't find them.
      out = process.stdout.readline()
      if out == '' and process.poll() is not None:
        self.send_message.emit(_('Completed Mercurial clone of {}').format(repo_name))
        self.send_repo_path.emit(repo_name, str(repo_path))
        break
      if out:
        self.send_message.emit(out.strip())#.decode('utf-8'))
    
    
    