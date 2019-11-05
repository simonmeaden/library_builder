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

import shutil , os
# from datetime import datetime
from pathlib import Path
import urlgrabber
from urllib.request import urlsplit
import zipfile, tarfile
import re


from PySide2.QtCore import (
    Signal,
#    Slot,
    QObject,
    QThread,
  )

from pygit2 import clone_repository, RemoteCallbacks

from common_types import ExistAction


import gettext
gb = gettext.translation('repository', localedir='locales', languages=['en_GB'])
gb.install()
_ = gb.gettext # English (United Kingdom)

# #========================================================================================
# class Decompression(QThread):
#   """"""
# 
#   send_message = Signal(str)
#   finished = Signal()
#   
#   #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def __init__(self):
#     """
#     Constructor 
#     """
#     QThread.__init__(self)
#     
#     self.running = True
#     
#     
#   #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def run(self):
#     while self.running:
#       ''''''
#         
#     self.finished.emit()  
#     
#   #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def decompress(self, filename, download_file, download_path, extract_path):
#     self.print_message(_('Decompressing file {}.').format(filename))
#     # decompress it
#     compressed_filename = str(download_file)
#     if zipfile.is_zipfile(compressed_filename):
#       with zipfile.ZipFile(compressed_filename, 'r') as zip_file:
#         zip_file.extract_all(str(extract_path))
#         return extract_path
#       
#     else:
#       try:
#         tar_archive = tarfile.open(compressed_filename, 'r:*')
#         tar_archive.extractall(path=str(download_path))
#         root_dir = os.path.commonprefix(tar_archive.getnames())
#         return Path(root_dir)
#         
#       except tarfile.ReadError as error:
#         self.print_message(str(error))
#         
#       self.print_message(_('Decompressing file {} complete.').format(filename))

    
#========================================================================================
class FileTransfer(QThread):
  """"""
  
  send_message = Signal(str)
  finished = Signal()
  send_repo_path = Signal(str, str)

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self):
    """
    Constructor 
    """
    QThread.__init__(self)
    
    self.running = True
    self.download_paths = []
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
    while self.running:
      ''''''
      if len(self.download_paths) > 0:
        data = self.download_paths.pop(0)
        name = data[0]
        libname = data[1]
        url = data[2]
        download_path = data[3]
        self.__download_file(name, libname, url, download_path)
        
    self.finished.emit()  
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def set_download_path(self, name, libname, url, download_path, exist_action):
    '''''' 
    self.download_paths.append((name, libname, url, download_path, exist_action))
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __download_remote_file(self, local_file, download_file):
    data = local_file.read() # read the file data for later reuse
  # save the file.
    with open(str(download_file), 'wb') as f:
      f.write(data)
    local_file.close()

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __download_file(self, name, libname, url, download_path):
    # try to detect already downloaded file
    (version, exists) = self.__detect_existing_download(libname, download_path)
    
    if not exists:
      # download new local version
      try:
        # urlgrabber follows redirects better than using burllib directly
        local_file = urlgrabber.urlopen(url)  # use urlgrabber to open the url
        actual_url = local_file.url  # detects the actual filename of the redirected url
        values = urlsplit(actual_url)  # split the url up into bits
        filepath = Path(values[2].decode('UTF-8'))  # part 2 is the file name section of the url
        filename = filepath.name  # just extract the file name.
        
      except urlgrabber.grabber.URLGrabError as error:
        self.print_message(str(error))
        
      self.print_message(_('Started downloading {}').format(download_path, filename))
      download_file = download_path / filename
      extract_path = self.download_path / name
      extract_path.mkdir(parents=True, exist_ok=True)      
      self.__download_remote_file(local_file, download_file)
      self.__decompress(filename, download_file, download_path, extract_path)
      self.print_message(_('Completed download of {}.').format(filename))
    else:
      # check existing local version against download version
      (f_major, f_minor, f_build) = self.__detect_library_version(version)
      (d_major, d_minor, d_build) = self.__detect_download_version(filename)
      if (d_major > f_major or 
          d_minor > f_minor or
          d_build > f_build):
        # download replacement if newer
        self.print_message(_('Started downloading {} to replace earlier version').format(download_path, filename))
        download_file = download_path / filename
        extract_path = self.download_path / name
        extract_path.mkdir(parents=True, exist_ok=True)
        self.__download_remote_file(local_file, download_file)
        self.__decompress(filename, download_file, download_path, extract_path)
        self.print_message(_('Completed download of {} of replacement version.').format(filename))

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_existing_download(self, libname, download_path):
    if download_path.exists():
      for f in download_path.glob(libname + '*'):
        if f.exists():
          p = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
          m = p.search(f.name)
          version = m.group(1)
          return (version, True)
    
    return ('0.0.0', False) 

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_library_version(self, version):
    f_version = version.split('.')
    major_version = f_version[0]
    minor_version = f_version[1]
    build_version = f_version[2]
    return major_version, minor_version, build_version
  
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_download_version(self, filename):
    lib_re = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
    m = lib_re.search(filename)
    d_version = m.group(1).split('.')
    major_version = d_version[0]
    minor_version = d_version[1]
    build_version = d_version[2]
    return major_version, minor_version, build_version

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __decompress(self, filename, download_file, download_path, extract_path):
    self.print_message(_('Decompressing file {}.').format(filename))
    # decompress it
    compressed_filename = str(download_file)
    if zipfile.is_zipfile(compressed_filename):
      with zipfile.ZipFile(compressed_filename, 'r') as zip_file:
        zip_file.extract_all(str(extract_path))
        return extract_path
      
    else:
      try:
        tar_archive = tarfile.open(compressed_filename, 'r:*')
        tar_archive.extractall(path=str(download_path))
        root_dir = os.path.commonprefix(tar_archive.getnames())
        return Path(root_dir)
        
      except tarfile.ReadError as error:
        self.print_message(str(error))
        
      self.print_message(_('Decompressing file {} complete.').format(filename))

      
#= CloneProgress class ==================================================================
class CloneProgress(QObject, RemoteCallbacks):
  ''' Git progress tracing '''
  
  send_update_objects = Signal(int) #
  send_update_delta = Signal(int)
  send_start_delta = Signal(int)
  send_start_objects = Signal(int)
  
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self):
    """
    Constructor 
    """
    RemoteCallbacks.__init__(self)
    QObject.__init__(self)
    
    self.started_objects = False
    self.started_delta = False

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def transfer_progress(self, stats):
    """ Monitors transfer progress and sends messages with download progress. """
    
    if not self.started_objects and stats.total_objects > 0:
      self.send_start_objects.emit(stats.total_objects)
      self.started_objects = True

    if not self.started_delta and stats.total_deltas > 0:
      self.send_start_delta.emit(stats.total_deltas)
      self.started_delta = True
      
    if self.started_objects:
      self.send_update_objects.emit(stats.received_objects)
        
    if self.started_delta:
      self.send_update_delta.emit(stats.indexed_deltas)
      
    RemoteCallbacks.transfer_progress(self, stats)


#= GitRepository class ==================================================================
class GitRepository(QThread):
  """
    classdocs
  """

  """ Sends a message string signal """
  send_message = Signal(str)
  finished = Signal()
  send_repo_path = Signal(str, str)

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, remote=None):
    """
    Constructor
    """
    QThread.__init__(self)
    
    self.remote = remote
    self.running = True
    self.download_paths = []

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
    while self.running:
      ''''''
      if len(self.download_paths) > 0:
        data = self.download_paths.pop(0)
        repo_name = data[0]
        download_path = data[1]
        repo_url = data[2]
        exist_action = data[3]
        
        self.create_remote_repo(download_path, repo_name, repo_url, exist_action, self.remote)
        
    self.finished.emit()  

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def set_download_path(self, download_path, repo_name, repo_url, exist_action=ExistAction.NONE):
    '''''' 
    self.download_paths.append((repo_name, download_path, repo_url, exist_action))
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def stop(self):
    self.finished.emit()
    self.running = False
        
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def create_remote_repo(self, download_path, repo_name, repo_url, exist_action, remote = None):
    """ create a working directory from a remote url

    Creates a new working directory and clones the remote replository
    into that directory. If the directory already exists then the
    result will depend on the value of the exist_action flag.

    :param download_path - the download path in which to place the new repository
    :param repo_name - a string repository name to a new git working directory
    :param repo_url - the git url for the remote repositoty.
    :param exist_action - action to take if the repo already exists
    """
    try:
      if not download_path.exists():  # should already be
        download_path.mkdir(parents=True, exist_ok=True)

      repo_path = download_path / repo_name
      if repo_path.exists():
        
        # TODO check if it is an earlier/later version

        self.send_message.emit(_('Path {} already exists').format(str(repo_path)))
        if exist_action == ExistAction.SKIP:
          self.send_message.emit('exist_action == Skip - loading local repository')
          return

        elif exist_action == ExistAction.OVERWRITE:
          self.send_message.emit(_('exist_action == Overwrite - deleting existing directory'))
          shutil.rmtree(repo_path)

        elif exist_action == ExistAction.BACKUP:
          self.send_message.emit(_('exist_action == Backup - backing up existing directory'))
          destination = repo_path / '.old'
          if destination.exists():
            shutil.rmtree(destination)
          shutil.copytree(repo_path, destination)
          shutil.rmtree(repo_path)

        else:
          self.send_message.emit(_('Invalid exist_action - stopping process'))
          return

        repo = clone_repository(url=repo_url, path=repo_path, callbacks=remote)
#         self.create_local_repo(repo_path)

        if not repo.is_bare:
          self.send_message.emit(_('Remote repo at {} successfully loaded.').format(repo_url))
          self.remote_repo = repo
          
        self.send_repo_path.emit(repo_name, str(repo_path))

      else :
        """"""
        self.send_message.emit(_('Started downloading {} into {}').format(repo_name, repo_path))
        repo = clone_repository(url = repo_url, path = str(repo_path), callbacks = remote)
#         self.create_local_repo(repo_path)
        self.send_message.emit(_('Completed downloading of {}').format(repo_name))
        
        self.send_repo_path.emit(repo_name, str(repo_path))
        self.finished.emit()

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
