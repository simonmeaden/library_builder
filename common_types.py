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

# class classproperty(object):
#   def __init__(self, getter):
#     self.getter= getter
#
#   def __get__(self, instance, owner):
#     return self.getter(owner)
#

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
          pen.setColor(QColor('green'))
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

# class LibraryTypeDialog(QDialog):
#
#       def __init__(self,
#                    library_style,
#                    shared_libraries,
#                    static_libraries,
#                    required_libraries,
#                    destination_path,
#                    parent = None):
#         super(LibraryTypeDialog, self).__init__(parent)
#         self.setWindowTitle("Confirm Library Build")
#         self.library_style = library_style
#         self.shared_libraries = shared_libraries
#         self.static_libraries = static_libraries
#         self.required_libraries = required_libraries
#         self.destination_path = destination_path
#         self._result = BuildStyle.NONE
#         self._shared_result = BuildStyle.SHARED_CREATE_MISSING
#         self._static_result = BuildStyle.STATIC_CREATE_MISSING
#
#         self.__init_gui()
#
#
#       def __init_gui(self):
#         main_layout = QGridLayout()
#         self.setLayout(main_layout)
#
#         common_text_1_lbl = QLabel(self)
#         common_text_1_lbl.setText('Please select from one of the choices below.\n'
#                     'The actual choices depended on your selection\n'
#                     'of compiler type, library style and which libraries\n'
#                     'you selected and which libraries of the correct style\n'
#                     'already exist on the host computer.')
#         main_layout.addWidget(common_text_1_lbl, 0, 0, 1, 2)
#
#         existing_shared = []
#         required_shared = []
#         existing_static = []
#         required_static = []
#         text_1 = ''
#         text_2 = ''
#         text_3 = ''
#         row = 1
#
#         if self.library_style == LibraryStyle.SHARED or self.library_style == LibraryStyle.SHARED_AND_STATIC:
#           ''''''
#           for library in self.required_libraries:
#             if library in self.shared_libraries and self.shared_libraries[library]:
#               existing_shared.append(library)
#             else:
#               required_shared.append(library)
#           if required_shared: # there are some libraries to be created.
#             req_count = len(required_shared)
#             substr = ''
#             if req_count > 0:
#               substr = 'There are at least {} shared libraries'.format(req_count)
#             else:
#               substr = 'There are no shared libraries'
#             common_text_2_lbl = QLabel(self)
#             main_layout.addWidget(common_text_2_lbl, row, 0, 1, 2)
#             common_text_2_lbl.setText(
#               '{}n'
#               'to be built.You will need to select the\n'
#               'possible actions from those below.'.format(substr))
#             text_1 = 'Create all missing shared libraries (and any missing\n' \
#                      'requirements) and put then in the destination directory\n' \
#                      '{}'
#             text_2 = 'Create all missing shared libraries (and any missing\n' \
#                      'requirements) and put then in the destination directory\n' \
#                      '{}.\n' \
#                      'Also copy any existing shared libraries into the same\n' \
#                      'directory.'
#             text_3 = 'Make completely new versions of all shared libraries ignoring\n' \
#                      'existing libraries and store them in the destination directory\n' \
#                      '{}'
#
#             shared_grp = QButtonGroup(self)
#             shared_grp.setExclusive(True)
#
#             choice_1 = QRadioButton(self)
#             choice_1.setChecked(True)
#             choice_1.setText(text_1.format(str(self.destination_path)))
#             shared_grp.addButton(choice_1, 1)
#             main_layout.addWidget(choice_1, row + 1, 0, 1, 2)
#
#             choice_2 = QRadioButton(self)
#             choice_2.setText(text_2.format(str(self.destination_path)))
#             shared_grp.addButton(choice_2, 2)
#             main_layout.addWidget(choice_2, row + 2, 0, 1, 2)
#
#             choice_3 = QRadioButton(self)
#             choice_3.setText(text_3.format(str(self.destination_path)))
#             shared_grp.addButton(choice_3, 3)
#             main_layout.addWidget(choice_3, row + 3, 0, 1, 2)
#             row += 4
#
#             shared_grp.buttonClicked.connect(self.__shared_changed)
#             self.shared_grp = shared_grp
#           else:
#             common_text_2_lbl = QLabel(self)
#             common_text_2_lbl.setText('There are no shared libraries to build.')
#             main_layout.addWidget(common_text_2_lbl, row, 0, 1, 2)
#             row += 2
#
#         if self.library_style == LibraryStyle.STATIC or self.library_style == LibraryStyle.SHARED_AND_STATIC:
#           ''''''
#           for library in self.required_libraries:
#             if library in self.shared_libraries and self.static_libraries[library]:
#               existing_static.append(library)
#             else:
#               required_static.append(library)
#           if required_static: # there are some libraries to be created.
#             req_count = len(required_static)
#             substr = ''
#             if req_count > 0:
#               substr = 'There are at least {} static libraries'.format(req_count)
#             else:
#               substr = 'There are no static libraries'
#             common_text_3_lbl = QLabel(self)
#             main_layout.addWidget(common_text_3_lbl, row, 0, 1, 2)
#             common_text_3_lbl.setText(
#               '{}\n'
#               'to be built.You will need to select the\n'
#               'possible actions from those below.'.format(substr))
#
#             text_1 = 'Create all missing static libraries (and any missing\n' \
#                      'requirements) and put then in the destination directory\n' \
#                      '{}'
#             text_2 = 'Create all missing static libraries (and any missing\n' \
#                      'requirements) and put then in the destination directory\n' \
#                      '{}.\n' \
#                      'Also copy any existing static libraries into the same\n' \
#                      'directory.'
#             text_3 = 'Make completely new versions of all static libraries ignoring\n' \
#                      'existing libraries and store them in the destination directory\n' \
#                      '{}'
#             static_grp = QButtonGroup(self)
#             static_grp.setExclusive(True)
#
#             choice_1 = QRadioButton(self)
#             choice_1.setChecked(True)
#             choice_1.setText(text_1.format(str(self.destination_path)))
#             static_grp.addButton(choice_1, 4)
#             main_layout.addWidget(choice_1, row + 1, 0, 1, 2)
#
#             choice_2 = QRadioButton(self)
#             choice_2.setText(text_2.format(str(self.destination_path)))
#             static_grp.addButton(choice_2, 5)
#             main_layout.addWidget(choice_2, row + 2, 0, 1, 2)
#
#             choice_3 = QRadioButton(self)
#             choice_3.setText(text_3.format(str(self.destination_path)))
#             static_grp.addButton(choice_3, 6)
#             main_layout.addWidget(choice_3, row + 3, 0, 1, 2)
#             row += 4
#
#             static_grp.buttonClicked.connect(self.__static_changed)
#             self.static_grp = static_grp
#
#           else:
#             common_text_3_lbl = QLabel(self)
#             common_text_3_lbl.setText('There are no shared libraries to build.')
#             main_layout.addWidget(common_text_3_lbl, row, 0, 1, 2)
#             row += 2
#
#
#         ok_btn = QPushButton('OK')
#         ok_btn.clicked.connect(self.accept)
#         main_layout.addWidget(ok_btn, row, 0)
#
#         cancel_btn = QPushButton('Cancel')
#         cancel_btn.clicked.connect(self.reject)
#         main_layout.addWidget(cancel_btn, row, 1)
#
#       def __static_changed(self, _):
#         ''''''
#         btn_id = self.static_grp.checkedId()
#         if btn_id == 4:
#           self._static_result = BuildStyle.STATIC_CREATE_MISSING
#         elif btn_id == 5:
#           self._static_result = BuildStyle.STATIC_CREATE_MISSING_AND_COPY
#         elif btn_id == 6:
#           self._static_result = BuildStyle.STATIC_CREATE_ALL
#         print(self._static_result)
#
#       def __shared_changed(self, _):
#         ''''''
#         btn_id = self.shared_grp.checkedId()
#         if btn_id == 1:
#           self._shared_result = BuildStyle.SHARED_CREATE_MISSING
#         elif btn_id == 2:
#           self._shared_result = BuildStyle.SHARED_CREATE_MISSING_AND_COPY
#         elif btn_id == 3:
#           self._shared_result = BuildStyle.SHARED_CREATE_ALL
#         print(self._shared_result)
#
#       def result(self):
#         return (self._shared_result | self._static_result)
#
#       def is_in(self, value):
#         return value & (self._shared_result | self._static_result)

