'''
Created on 21 Sep 2019

@author: simonmeaden
'''

from enum import Enum

class ExistAction(Enum):
  Skip = 1,
  Overwrite = 2,
  Backup = 3

 
class CompilerOptions:
  use_mxe = False;
  compiler_flavour = 'Native'
  url = ''
  branch = ''
  path = ''
  exist_action = ExistAction.Skip
