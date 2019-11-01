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

from enum import Enum, IntFlag, auto
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
  QDialog,
  QFrame,
  QGridLayout,
  QCheckBox,
  QComboBox,
  QRadioButton,
  QPushButton,
  QButtonGroup,
  QLabel,
  )


#======================================================================================
class ExistAction(Enum):
  SKIP = auto()
  OVERWRITE = auto()
  BACKUP = auto()

# class FramePosition(Enum):
#   TopLeft = auto()
#   Centre = auto()


class LibraryStyle(Enum):
  SHARED = auto()
  STATIC = auto()
  SHARED_AND_STATIC = auto()


class CompileStyle(Enum):
  NONE = auto(),
  CONFIGURE = auto(),


class BuildStyle(IntFlag):
  NONE = 0,
  CREATE_MISSING = 1,
  CREATE_MISSING_AND_COPY = 2,
  CREATE_ALL = 4,


class CompilerType(Enum) :
  NONE = 0, 'No Compiler'
  GCC_NATIVE = 1, 'Native g++',
  MINGW_32_NATIVE = 2, 'MinGW Win32'
  MINGW_64_NATIVE = 3, 'MinGW Win64'
  MINGW_32_MXE_SHARED = 4, 'MXE MinGW Win32 Shared'
  MINGW_32_MXE_STATIC = 5, 'MXE MinGW Win32 Static'
  MINGW_64_MXE_SHARED = 6, 'MXE MinGW Win64 Shared'
  MinGW_64_MXE_STATIC = 7, 'MXE MinGW Win64 Static'

  def __new__(cls, value, str_name):
    obj = object.__new__(cls)
    obj._value_ = value
    obj.str_name = str_name
    return obj

  def __str__(self):
    return self.str_name

  @classmethod
  def from_name(cls, name):
    for k, v in CompilerType.__members__.items():
        if v.str_name == name:
          return v

    raise ValueError('{} is not a valid compiler type'.format(name))


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
  FTP = auto()


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
# required_role = Qt.UserRole + 3


class SelectionType(Enum):
  NONE = auto(),  # Unselected
  SELECTED = auto(),  # Selected manually
  REQUIRED = auto(),  # Selected as a requirement


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
      selection_type = item.data(selected_role)
      text = index.data(Qt.DisplayRole)

      if selection_type == SelectionType.REQUIRED:
          font = painter.font()
          font.setWeight(QFont.Bold)
          painter.setFont(font)
          pen = painter.pen()
          pen.setColor(QColor('blue'))
          painter.setPen(pen)
          painter.drawText(option.rect, Qt.AlignLeft, text)
      elif selection_type == SelectionType.SELECTED:
          font = painter.font()
          font.setWeight(QFont.Bold)
          painter.setFont(font)
          pen = painter.pen()
          pen.setColor(QColor('lightgreen'))
          painter.setPen(pen)
          painter.drawText(option.rect, Qt.AlignLeft, text)
      else:  # SelectionType.NONE
          font = painter.font()
          font.setWeight(QFont.Normal)
          painter.setFont(font)
          pen = painter.pen()
          pen.setColor(QColor('black'))
          painter.setPen(pen)
          painter.drawText(option.rect, Qt.AlignLeft, text)

      painter.restore()


