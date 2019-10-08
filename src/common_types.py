'''
Created on 21 Sep 2019

@author: simonmeaden
'''  

from enum import Enum,auto
from PySide2.QtCore import (
  Qt,
  )
from PySide2.QtGui import (
  QFont,
  QBrush,
  QColor,
  QPen,
  )
from PySide2.QtWidgets import (
    QStyledItemDelegate,
  )



#======================================================================================
class ExistAction(Enum):
  Skip = auto()
  Overwrite = auto()
  Backup = auto()

 
class CompilerOptions:
  use_mxe = False;
  compiler_flavour = 'Native'
  url = ''
  branch = ''
  path = ''
  exist_action = ExistAction.Skip

class FramePosition(Enum):
  TopLeft = auto()
  Centre = auto()
  
class MXEStyle(Enum):
  NONE = auto()
  Shared = auto()
  Static = auto()
  
class MXEType(Enum):
  NONE = auto()
  x86_64 = auto()
  i686 = auto()
  

CompilerType = Enum(
    value='Compiler',
#     names=itertools.chain.from_iterable(
#         itertools.product(v, [k]) for k, v in _COMPILERS.items()
    names = [ 
      ('No Compiler', 0),
      ('NONE', 0),
      ('Native g++', 1),
      ('GCC_Native', 1),
      ('MinGW Win32', 2),
      ('MinGW_32_Native', 2),
      ('MinGW Win64', 3),
      ('MinGW_64_Native', 3),
      ('MXE MinGW Win32 Shared', 4),
      ('MinGW_32_MXE_Shared', 4),
      ('MXE MinGW Win32 Static', 5),
      ('MinGW_32_MXE_Static', 5),
      ('MXE MinGW Win64 Shared', 6),
      ('MinGW_64_MXE_Shared', 6),
      ('MXE MinGW Win64 Static', 7),
      ('MinGW_64_MXE_Static', 7),
      # TODO Risc-V 64 and other cross compilers}
      ]
    )

    
#======================================================================================
class RequiredLibrary:
  name = ''
  min_version = ''
  
  
class LibraryType(Enum):
  NONE = auto()
  GIT = auto()
  CVS = auto()
  FILE = auto()
  WGET = auto()
      
class Library(object):
  name = ''
  url = ''
  type = LibraryType.NONE
  libname = ''
  required_libs = []

#======================================================================================
selected_role = Qt.UserRole
name_role = Qt.UserRole + 1
required_libs_role = Qt.UserRole + 2

class ItemDelegate(QStyledItemDelegate):
  ''' Defines the display colours of the library list.
  
  The ItemDelegate class arranges the colours that the library list
  displays when a library is selected.
  '''
  def __init__(self, widget, parent=None):
      QStyledItemDelegate.__init__(self)  
      self.list_widget = widget

  def paint(self, painter, option, index):
      painter.save()

      row = index.row()
      item = self.list_widget.item(row)
      selected = item.data(selected_role)
      text =  index.data(Qt.DisplayRole)
      
      if selected:
          font = painter.font()
          font.setWeight(QFont.Bold)
          painter.setFont(font)
          pen = painter.pen()
          pen.setColor(QColor('green')) 
          painter.setPen(pen)  
          painter.drawText(option.rect, Qt.AlignLeft, text)
      else:
          font = painter.font()
          font.setWeight(QFont.Normal)
          painter.setFont(font)
          pen = painter.pen()
          pen.setColor(QColor('black')) 
          painter.setPen(pen)  
          painter.drawText(option.rect, Qt.AlignLeft, text)

      painter.restore()