'''
Created on 21 Sep 2019

@author: simonmeaden
'''

from enum import Enum

class ExistAction(Enum):
  Skip = 1
  Overwrite = 2
  Backup = 3

 
class CompilerOptions:
  use_mxe = False;
  compiler_flavour = 'Native'
  url = ''
  branch = ''
  path = ''
  exist_action = ExistAction.Skip

class FramePosition(Enum):
  TopLeft = 1
  Centre = 2
  
class MXEStyle(Enum):
  NONE = 0
  Shared = 1
  Static = 2
  
class MXEType(Enum):
  NONE = 0
  x86_64 = 1
  i686 = 2
  
class CompilerType(Enum):
  NONE = 'No Comiler'
  GCC_Native = 'Native g++'
  GCC_MXE_Native = 'MXE Native g++'
  MinGW_32_Native = 'MinGW Win32'
  MinGW_64_Native = 'MinGW Win64'
  MinGW_32_MXE_Shared = 'MXE MinGW Win32 Shared'
  MinGW_32_MXE_Static = 'MXE MinGW Win32 Static'
  MinGW_64_MXE_Shared = 'MXE MinGW Win64 Shared'
  MinGW_64_MXE_Static = 'MXE MinGW Win64 Static'
  CLang_Native = 'Native Clang'
  
  
    
