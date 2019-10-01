'''
Created on 21 Sep 2019

@author: simonmeaden
'''

from enum import Enum
import itertools

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
  
# class CompilerType(Enum):
#   NONE = 'No Compiler'
#   GCC_Native = 'Native g++'
#   MinGW_32_Native = 'MinGW Win32'
#   MinGW_64_Native = 'MinGW Win64'
#   MinGW_32_MXE_Shared = 'MXE MinGW Win32 Shared'
#   MinGW_32_MXE_Static = 'MXE MinGW Win32 Static'
#   MinGW_64_MXE_Shared = 'MXE MinGW Win64 Shared'
#   MinGW_64_MXE_Static = 'MXE MinGW Win64 Static'
#   
  # TODO Risc-V 64
_COMPILERS = {
    0: ['No Compiler',            'NONE'],
    1: ['Native g++',             'GCC_Native'],
    2: ['MinGW Win32',            'MinGW_32_Native'],
    3: ['MinGW Win64',            'MinGW_64_Native'],
    4: ['MXE MinGW Win32 Shared', 'MinGW_32_MXE_Shared'],
    5: ['MXE MinGW Win32 Static', 'MinGW_32_MXE_Static'],
    6: ['MXE MinGW Win64 Shared', 'MinGW_64_MXE_Shared'],
    7: ['MXE MinGW Win64 Static', 'MinGW_64_MXE_Static'],
     # TODO Risc-V 64 and other cross compilers
}
CompilerType = Enum(
    value='Compiler',
    names=itertools.chain.from_iterable(
        itertools.product(v, [k]) for k, v in _COMPILERS.items()
    )
)  
    
