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

class FramePosition(Enum):
  TopLeft = 1,
  Centre = 2
  
class MXEStyle(Enum):
  NONE = 0,
  Shared = 1,
  Static = 2
  
class MXEType(Enum):
  NONE = 0,
  x86_64 = 1,
  i686 = 2
  
class CompilerType(Enum):
  NONE = 0,
  GCC_Native = 1,
  GCC_MXE_Native = 2,
  MinGW_32_Native = 3,
  MinGW_64_Native = 4,
  MinGW_32_MXE_Shared = 5,
  MinGW_32_MXE_Static = 6,
  MinGW_64_MXE_Shared = 7,
  MinGW_64_MXE_Static = 8,
  
    
