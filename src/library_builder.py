'''
Created on 21 Sep 2019

@author: simonmeaden
'''

import argparse

from repository import Repository
from common_types import ExistAction, CompilerOptions

__version__ = '0.1.0'
__author__ = u'Simon Meaden'


def __print_options(options):
  if options is not None:
    print("Root path        : {}".format(options.path))
    print("Compiler flavour : {}".format(options.compiler_flavour))
    print("URL              : {}".format(options.url))
    print("Branch           : {}".format(options.branch))
    print("Use MXE          : {}".format(options.use_mxe))
    print("Exist action     : {}".format(options.exist_action))

def __parse_arguments():
  parser = argparse.ArgumentParser(description='Tesseract compiler.')
  parser.add_argument('-f', '--flavour',
                      dest='compiler_flavour',
                      choices=['Win32', 'Win64', 'OSX', 'Android', 'Native'],
                      action='store',
                      default='Native',
                      __help='Destination Compiler Flavour')
  parser.add_argument('-use_mxe',
                      dest='use_mxe',
                      action='store_true',
                      __help='Whether to use MXE for Win32/Win64 builds, ')
  parser.add_argument('-u', '-url',
                      dest='url',
                      action='store',
#                      default='https://github.com/tesseract-ocr/tesseract.git',
                      __help='Set the git url')
  parser.add_argument('-b', '--branch', 
                      dest='branch', 
                      action='store',
                      default='master',
                      __help='Set the git branch, defaults to master')
  parser.add_argument('-p', '--path', 
                      dest='path', 
                      action='store',
                      __help='Set the root working path to which GIT stores repository, including the repository directory name.')
  parser.add_argument('-a', '--action',
                      dest='exist_action',
                      choices=['Skip', 'Overwrite', 'Backup'],
                      action='store',
                      default='Skip',
                      __help='Action on existance of working directory')
  args = parser.parse_args()
  return args

if __name__ == '__main__':
  args = __parse_arguments()

  options = CompilerOptions()
  
  if args is not None:
    options.url = args.url      
    options.branch = args.branch
    options.compiler_flavour = args.compiler_flavour
    if args.path:
      options.path = args.path
    if args.exist_action == 'Skip':
      options.exist_action = ExistAction.Skip
    elif args.exist_action == 'Overwrite':
      options.exist_action = ExistAction.Overwrite
    elif args.exist_action == 'Backup':
      options.exist_action = ExistAction.Backup
   
    if args.use_mxe is not None:
      if options.compiler_flavour == "Win32" or options.compiler_flavour == "Win64":
        options.use_mxe = True

  __print_options(options)
   
  repo = Repository()
  repo.create_remote_repo(options.path, options.url, options.exist_action)
  
  repo.print_local_repository()

  
  