'''
Created on 21 Sep 2019

@author: simonmeaden
'''

"""@package repository
Documentation for the repository module.
 
More details.
"""
import os, shutil
from datetime import datetime

from PySide.QtCore import (
    Signal,
#    Slot,
    QObject
  )

# from git import Repo
# # from git import Remote
# from git.exc import NoSuchPathError
import pygit2
from pygit2 import clone_repository
from pygit2 import init_repository

from common_types import ExistAction


class Repository(QObject):
  '''
    classdocs
  '''
  
  ''' Sends a message string signal '''
  send_message = Signal(str)

  def __init__(self):
    '''
    Constructor
    '''
    QObject.__init__(self)
      
  def print_commit(self, commit):
    '''
    print commit information to log
    '''
    self.send_message.emit('----')
    self.send_message.emit(str(commit.hexsha))
    self.send_message.emit("\"{}\" by {} ({})".format(commit.summary,
                                     commit.author.name,
                                     commit.author.email))
    self.send_message.emit(str(commit.authored_datetime))
    self.send_message.emit(str("count: {} and size: {}".format(commit.count(),
                                              commit.size)))
    
    
  def print_local_repository(self,):
    '''
    print repository information to log
    '''
    if not self.local_repo.is_bare:    
      self.send_message.emit('Repo path             : {}'.format(self.local_repo.path))
      self.send_message.emit('Repo working directory: {}'.format(self.local_repo.workdir))
      self.print_local_branches()
      self.print_remote_branches()
    
  def print_local_branches(self):
    ''' Send local branch info to log '''
    local_branches = self.get_local_branches()
    self.send_message.emit('Local Branches        : {}'.format(local_branches)) 

    
  def get_local_branches(self):
    ''' get a list of local branches '''
    if not self.local_repo.is_bare:
      local_branches = list(self.local_repo.branches.local)
      return local_branches 

    
  def print_remote_branches(self):
    ''' Send remote branch info to log '''
    remote_branches = self.get_remote_branches()
    self.send_message.emit('Remote Branches       : {}'.format(remote_branches)) 

    
  def get_remote_branches(self):
    ''' get a list of remote branches '''
    if not self.local_repo.is_bare:
      remote_branches = list(self.local_repo.branches.remote)
      return remote_branches

    
  def get_local_commits(self):
    ''' get a list of local commits '''
    if (not self.local_repo.is_bare):
      commits = []
   
      for commit in self.local_repo.walk(self.local_repo.head.oid, pygit2.GIT_SORT_TIME):
          commits.append({
              'hash': commit.hex,
              'message': commit.message,
              'commit_date': datetime.utcfromtimestamp(commit.commit_time).strftime('%Y-%m-%dT%H:%M:%SZ'),
              'author_name': commit.author.name,
              'author_email': commit.author.email,
              'parents': [c.hex for c in commit.parents],
          })
          
      print(commits)
          
      
  def create_local_repo(self, repo_path):
    """ Creates a local repository from a local path
    
    If you are cloning  remote repository via create_remote_repository(repo_path, repo_url)
    you will not need to call this as well as it will be called from create_remote_repository.
    Otherwise if you are not creating a remote repository, but need to interact solely
    with the local repository call this BEFORE you call any of the functions actioning the local 
    repository such as print_local_branches() or print_remote_branches().
    """
    try:
      repo = init_repository(repo_path.name)
      if not repo.is_bare:
        self.send_message.emit('Local repo at {} successfully loaded.'.format(repo_path))
        self.local_repo = repo
                
    except:
      self.send_message.emit('Local repo at {} failed to load : value error'.format(repo_path))
            
    
  def create_remote_repo(self, repo_path, repo_url, exist_action):
    """ create a working directory from a remote url
    
    Creates a new working directory and clones the remote replository
    into that directory. If the directory already exists then the 
    result will depend on the value of the exist_action flag.
    
    :param repo_path - a string path to a new git working directory
    :param repo_url - the git url for the remote repositoty.
    """
    try:
      if repo_path:
        if os.path.isdir(repo_path):
          self.send_message.emit('Path {} already exists'.format(repo_path))
          if exist_action == ExistAction.Skip:
            self.send_message.emit('exist_action == Skip - loading local repository')
            self.create_local_repo(repo_path)
            return 
          
          elif exist_action == ExistAction.Overwrite:
            self.send_message.emit('exist_action == Overwrite - deleting existing directory')
            shutil.rmtree(repo_path)
            
          elif exist_action == ExistAction.Backup:
            self.send_message.emit('exist_action == Backup - backing up existing directory')
            destination = repo_path + '.old'
            if os.path.exists(destination):
              shutil.rmtree(destination)
            shutil.copytree(repo_path, destination)
            
          else:
            self.send_message.emit('Invalid exist_action - stopping process')
            return
        
        repo = clone_repository(repo_url, repo_path)
        self.create_local_repo(repo_path)

        if not repo.is_bare:
          self.send_message.emit('Remote repo at {} successfully loaded.'.format(repo_url))
#             self.print_local_repository(repo)
          self.remote_repo = repo
          
    except ValueError:
      self.send_message.emit('Remote repo at {} failed to load : value error'.format(repo_url))
      raise


    def push(self):
      """
      """
      
    def pull(self):
      """
      """
 
