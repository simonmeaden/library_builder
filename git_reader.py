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
  QObject,
  Signal,
  QThread,
  )
import shutil
from pygit2 import clone_repository, RemoteCallbacks

from common_types import ExistAction

#= GitProgress class ==================================================================
class GitProgress(QObject, RemoteCallbacks):
  ## Git progress tracking
  #
  # A GitProgress object will need to be passed to your GitReader object's
  # constructor if you want to monitor download progress. Various sQt signals are 
  # sent by the transfer_progress method and you will need to link your progress
  # methods to these values. 
  
  send_update_objects = Signal(int) ## Sends an int object progress update.
  send_update_delta = Signal(int)   ## Sends the int delta progress update.
  send_start_delta = Signal(int)    ## Sends the total delta count to be downloaded.
  send_start_objects = Signal(int)  ## Sends the total object count to be downloaded.
  send_start = Signal(int)          ## Sends an int total count. Equivalent to send_start_objects + send_start_deltas. 
  send_update = Signal(int)         ## Sends the int total downloaded objects and deltas.
  
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self):
    ## Constructor 
    
    RemoteCallbacks.__init__(self)
    QObject.__init__(self)
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def transfer_progress(self, stats):
    ## Monitors transfer progress and sends messages with download progress. 
    #
    # You will need to connect to the various Qt signals, send_start_objects and
    # send_start_delta to get initial counts and send_update_objects and 
    # send_update_delta to get updated object and delta progress counts.
    
    total_objects = 0
    total_deltas = 0
    received_objects = 0
    indexed_deltas = 0
    
    if stats.total_objects > 0:
      total_objects = stats.total_objects
    if stats.total_deltas > 0:
      total_deltas = stats.total_deltas
    if stats.received_objects > 0:
      received_objects = stats.received_objects
    if stats.indexed_deltas > 0:
      indexed_deltas = stats.indexed_deltas
      
    totals = total_objects + total_deltas
    downloads = received_objects + indexed_deltas

    if total_deltas > 0:
      self.send_start_delta.emit(total_deltas)
    if total_objects > 0:
      self.send_start_objects.emit(total_objects)
    if received_objects > 0:
      self.send_update_objects.emit(received_objects)  
    if indexed_deltas:
      self.send_update_delta.emit(indexed_deltas)    
    if totals:
      self.send_start.emit(stats.totals)        
    if downloads:
      self.send_update.emit(downloads)
      
    RemoteCallbacks.transfer_progress(self, stats)



#= GitReader class ==================================================================
class GitReader(QThread):
  ## The GitReader class clones the specified remote repository into you specified directory.
  #
  # The GitReader class is used to clone a GIT repository into a local download directory.
  # 
  # GitReader runs as  a separate thread so the maaster application does not block. Data about
  # the required repository is passed to the downloader via the set_clone_paths method and 
  # the library name and download directory is passed back to the application via a Qt
  # send_repo_path signal.
  #
  # If an optional GitProgress object is passed as the remote parameter, then Qt progress 
  # signals are passed back to your progress monitor.  
  #
  # Repositories 

  send_message = Signal(str) ## Sends a message string Qt signal
  finished = Signal() ## Sends a completed Qt signal
  send_repo_path = Signal(str, str) # Sends the repository name and path as a Qt signal

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, remote=None, exist_action=ExistAction.SKIP):
    ## Constructor
    #
    # The GitReader constructor takes an optional progress monitor object as a parameter.
    #
    # /param remote - optional GitProgress object
    QThread.__init__(self)
    
    self.remote = remote
    self.running = True
    self.download_paths = []
    self.exist_action = exist_action

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
    ## The worker run method.
    while self.running:
      if len(self.download_paths) > 0:
        data = self.download_paths.pop(0)
        repo_name = data[0]
        download_path = data[1]
        repo_url = data[2]
        exist_action = data[3]
        
        self.clone_repo(download_path, repo_name, repo_url, exist_action, self.remote)
        
    self.finished.emit()  

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def set_clone_paths(self, download_path, repo_name, repo_url, exist_action=ExistAction.NONE):
    ## The set_clone_paths method is used to send repository information to the worker thread.
    #
    # Adds the download data to the worker todo list. The exist_action parameter can be used
    # to specify various actions to take if the repository has alread been downloaded. the options
    # are:
    # - Skip. The download is ignored, specified by ExistAction.SKIP
    # - Backup The original directory is backed up and a new one is created, specified by ExistAction.BACKUP
    # - Overwrite The original directory is removed and recreated with na new download. Specified by ExistAction.OVERWRITE
    #
    # In addition the worker will check if the new download is newer than the existing download.
    # if so the original download will be backed up.
    # 
    # /param download_path - the base download directory.
    # /param repo_name - the name of the library.
    # /param repo_url - the GIT repository URL.
    # /param exist_action - the action to take if the repository already exists 
    
    self.download_paths.append((repo_name, download_path, repo_url, exist_action))
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def stop(self):
    ## Stops the worker object.
    #
    # Stops the worker and send a finished signal on completion
    
    self.running = False
        
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def clone_repo(self, download_path, repo_name, repo_url, exist_action, remote = None):
    # create a working directory from a remote url
    #
    # Creates a new working directory and clones the remote replository
    # into that directory. If the directory already exists then the
    # result will depend on the value of the exist_action flag.
    try:
      if not download_path.exists():  # should already be
        download_path.mkdir(parents=True, exist_ok=True)

      repo_path = download_path / repo_name
      
      if repo_path.exists():
        self.send_message.emit(_('Path {} already exists').format(str(repo_path)))
        if self.exist_action == ExistAction.SKIP:
          self.send_message.emit('Exist Action == Skip - loading local repository')
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
  
      repo = clone_repository(url=repo_url, path=repo_path, callbacks=remote)
#         self.create_local_repo(repo_path)

      if not repo.is_bare:
        self.send_message.emit(_('Remote repo at {} successfully loaded.').format(repo_url))
        self.remote_repo = repo
        
      self.send_repo_path.emit(repo_name, str(repo_path))

    except ValueError:
      self.send_message.emit(_('Remote repo at {} failed to load : value error').format(repo_url))
      raise


  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def get_remote_branches(self):
#     """ get a list of remote branches """
#     if not self.local_repo.is_bare:
#       remote_branches = list(self.local_repo.branches.remote)
#       return remote_branches

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def get_local_commits(self):
#     """ get a list of local commits """
#     if (not self.local_repo.is_bare):
#       commits = []
# 
#       for commit in self.local_repo.walk(self.local_repo.head.oid, pygit2.GIT_SORT_TIME):
#           commits.append({
#               'hash': commit.hex,
#               'message': commit.message,
#               'commit_date': datetime.utcfromtimestamp(commit.commit_time).strftime('%Y-%m-%dT%H:%M:%SZ'),
#               'author_name': commit.author.name,
#               'author_email': commit.author.email,
#               'parents': [c.hex for c in commit.parents],
#           })
# 
#       print(commits)

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def create_local_repo(self, repo_path):
#     """ Creates a local repository from a local repository path
# 
#     If you are cloning  remote repository via create_remote_repository(repo_path, repo_url)
#     you will not need to call this as well as it will be called from create_remote_repository.
#     Otherwise if you are not creating a remote repository, but need to interact solely
#     with the local repository call this BEFORE you call any of the functions actioning the local
#     repository such as print_local_branches() or print_remote_branches().
#     """
#     try:
#       repo = init_repository(repo_path.name)
#       if not repo.is_bare:
#         self.send_message.emit(_('Local repo at {} successfully loaded.').format(repo_path))
#         self.local_repo = repo
# 
#     except:
#       self.send_message.emit(_('Local repo at {} failed to load : value error').format(repo_path))
  #======================================================================================
#   def push(self):
#     """
#     """
#
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def pull(self):
#     """
#     """