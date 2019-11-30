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
#   QBrush,
  QColor,
#   QPen,
  )

from PySide2.QtCore import (
  QRect,
  QSize,
  )

from PySide2.QtWidgets import (
  QStyledItemDelegate,
  QDialog,
  QListWidget,
  QListWidgetItem,
  QGridLayout,
#   QCheckBox,
#   QComboBox,
#   QRadioButton,
  QPushButton,
#   QButtonGroup,
  QLabel,
  QSizePolicy,
  QAbstractItemView,
  QMessageBox, 
  QPlainTextEdit,
  )


#======================================================================================
class ExistAction(Enum):
  NONE = auto()
  SKIP = auto()
  OVERWRITE = auto()
  BACKUP = auto()
  UPDATE = auto()

# class FramePosition(Enum):
#   TopLeft = auto()
#   Centre = auto()


class LibraryStyle(Enum):
  SHARED = auto()
  STATIC = auto()
  SHARED_AND_STATIC = auto()


class CompileStyle(Enum):
  NONE = auto() ## No compiler sytle
  CONFIGURE = auto() ## has configure file
  AUTOGEN = auto() ## configure but autogen.sh will create.
  CMAKE = auto() ## CMake type

class BuildStyle(IntFlag):
  NONE = 0
  CREATE_MISSING = 1
  CREATE_MISSING_AND_COPY = 2
  CREATE_ALL = 4


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
    for unused, v in CompilerType.__members__.items():
        if v.str_name == name:
          return v

    raise ValueError('{} is not a valid compiler lib_type'.format(name))


#======================================================================================
class LibraryType(Enum):
  NONE = auto()
  GIT = auto()
  CVS = auto()
  MERCURIAL = auto()
  FILE = auto()
  WGET = auto()
  FTP = auto()


#======================================================================================
class Library():
  
  class RequiredLibrary:
    
    def __init__(self, name = '', version = 'latest'):
      self.name = name
      self.version = version
    
  class OptionalLibrary(RequiredLibrary):
    
    def __init__(self, name = '', version = 'latest', notes = ''):
      self.name = name
      self.version = version
      self.notes = notes
    
  def __init__(self, name='', search_name = '', url = '', lib_type = LibraryType.NONE, version = 'latest'):
    self.name = name
    self.url = url
    self.lib_type = lib_type
    self.search_name = search_name
    self.version = version
    self.required_libs = {}
    self.optional_libs = {}
  
  def add_required_library(self, name, version = 'latest'):
    library = self.RequiredLibrary(name, version)
    self.required_libs[name] = library
    
  def add_optional_library(self, name, version = 'latest', notes = ''):
    library = self.OptionalLibrary(name, version, notes)
    self.optional_libs[name] = library
    
  def required_library(self, name):
    if name in self.required_libs:
      return self.required_libs[name]
    return None
    
  def optional_library(self, name):
    if name in self.optional_libs:
      return self.optional_libs[name]
    return None
    
  def required_libraries(self):
    return self.required_libs
  
  def optional_libraries(self):
    return self.optional_libs
  
  def set_required_libs(self, required_libs):
    self.required_libs = required_libs

  def set_optional_libs(self, optional_libs):
    self.optional_libs = optional_libs


#= RequiredLibrariesDialog class =====================================================
class RequiredLibrariesDialog(QDialog):
  ##
  #
  
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, libraries = {}, required_list = [], optional_list = [], parent = None):
    ## Constructor
    #
    # \param libraries_list - the dict of already available libraries.
    # \param required_list - the list of required libraries that have already been selected for this name.
    # \param optional_list - the list of optional libraries that have already been selected.
    
    QDialog.__init__(parent)
    
    self.init_gui(parent)
    
    self.libraries_list = libraries.keys()
    for name in self.libraries_list:
      item = QListWidgetItem(name)
      if name in required_list:
        item.setData(optional_role, False)
        item.setData(selected_role, SelectionType.SELECTED)
      elif name in optional_list:
        item.setData(optional_role, True)
        # this overrides selected_role
        
      self.list.addItem(item)
      if name not in required_list:
        self.required_list.append(name)   
      
    self.optional_list = optional_list

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――  
  def selection_changed(self, item):
    name = item.text()
    if item.isSelected():
      if name not in self.required_list:
        if name in self.optional_list:
          if QMessageBox.warning(self,
                                 _("Library {}").format(name),
                                 _("Library  is already in the optional library set.\n"
                                   "Select Ok to move it to the required library list\n"
                                   "or Cancel to keep it as an optional library.",
                                   QMessageBox.Ok | QMessageBox.Cancel,
                                   QMessageBox.Cancel) == QMessageBox.Ok):
            self.required_list.append(name) 
            self.optional_list.remove(name)   
            item.setData(optional_role, False)
            item.setData(selected_role, SelectionType.SELECTED)
        else:
          self.required_list.append(name)
          item.setData(optional_role, False)
          item.setData(selected_role, SelectionType.SELECTED)
    else:
      self.required_list.remove(name)
      if self.optional_list:
        item.setData(optional_role, True)        
      else:
        item.setData(optional_role, False)
        item.setData(selected_role, SelectionType.NONE)


  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def selected_libraries(self):
    return (self.required_list, self.optional_list)
  
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def init_gui(self, parent):
    self.layout = QGridLayout()
    self.setLayout(self.layout)
    self.list = QListWidget(self)
    self.list.model().setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.list.itemClicked.connect(self.selection_changed)
    self.layout.addWidget(self.list, 0, 0, 1, 2)
    
    accept_btn = QPushButton(self)
    accept_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    accept_btn.setText(_("Accept"))
    accept_btn.clicked.connect(self.accept)
    self.layout.addWidget(accept_btn, 1, 0)
    
    cancel_btn = QPushButton(self)
    cancel_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    cancel_btn.setText(_("Cancel"))
    cancel_btn.clicked.connect(self.reject)
    self.layout.addWidget(cancel_btn, 1, 1)
    
    dw = 200
    dh = 100
    px = parent.x()
    py = parent.y()
    pw = parent.width()
    ph = parent.height()
    w2 = int((pw - dw) / 2.0)
    h2 = int((ph - dh) / 2.0)

    frame_geometry = QRect(px + w2, py + h2, dw, dh)
    self.setGeometry(frame_geometry)
    
      
#= OptionalLibrariesDialog class =====================================================
class OptionalLibrariesDialog(QDialog):
  ''''''
  
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, libraries = {}, optional_list = [], required_list = [], parent = None):
    ## Constructor
    #
    # \param libraries_list - the list of already available libraries.
    # \param optional_list - the list of optional libraries that have already been applied to this library.
    # \param required_list - the list of required libraries that have already been selected.
    QDialog.__init__(parent)
    QDialog.__init__(parent)
    
    self.init_gui(parent)
    
    self.libraries_list = libraries.keys()
    for name in self.libraries_list:
      item = QListWidgetItem(name)
      if name in optional_list:
        item.setData(optional_role, True)
        # this overrides selected_role
      elif name in required_list:
        item.setData(optional_role, False)
        item.setData(selected_role, SelectionType.SELECTED)
        
      self.list.addItem(item)
      if name in optional_list:
        self.required_list.append(name)   
      
    self.required_list = required_list
    self.current_library = None

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――  
  def notes_changed(self):
    notes = self.notes.toPlainText()
    optional_libraries = self.libraries_list.optional_libraries()
    if optional_libraries:
      library = optional_libraries[self.current_library]        
      if library:
        library.notes = notes
    
  
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――  
  def selection_changed(self, item):
    name = item.text()
    if item.isSelected():
      if name not in self.required_list:
        if name in self.required_list:
          if QMessageBox.warning(self,
                                 _("Library {}").format(name),
                                 _("Library  is already in the required library set.\n"
                                   "Select Ok to move it to the optional library list\n"
                                   "or Cancel to keep it as an required library.",
                                   QMessageBox.Ok | QMessageBox.Cancel,
                                   QMessageBox.Cancel) == QMessageBox.Ok):
            self.optional_list.append(name) 
            self.required_list.remove(name)   
            item.setData(optional_role, False)
            item.setData(selected_role, SelectionType.SELECTED)
        else:
          self.required_list.append(name)
          item.setData(optional_role, False)
          item.setData(selected_role, SelectionType.SELECTED)
          
      optional_libraries = self.libraries_list.optional_libraries()
      if optional_libraries:
        library = optional_libraries[name]        
        if library:
          notes = library.opt.notes
          self.notes.setPlainText(notes)
                  
    else:
      self.required_list.remove(name)
      if self.required_list:
        item.setData(optional_role, True)        
      else:
        item.setData(optional_role, False)
        item.setData(selected_role, SelectionType.NONE)
      self.notes.clear()
      self.current_library = None

    self.current_library = name

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def selected_libraries(self):
    return (self.required_list, self.required_list)
  
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def init_gui(self, parent):
    self.layout = QGridLayout()
    self.setLayout(self.layout)
    self.list = QListWidget(self)
    self.list.model().setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.list.itemClicked.connect(self.selection_changed)
    self.layout.addWidget(self.list, 0, 0, 1, 2)
    
    self.notes = QPlainTextEdit(self)
    self.notes.textChanged.connect(self.notes_changed)
    self.layout.addWidget(self.notes, 1, 0)
    
    accept_btn = QPushButton(self)
    accept_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    accept_btn.setText(_("Accept"))
    accept_btn.clicked.connect(self.accept)
    self.layout.addWidget(accept_btn, 2, 0)
    
    cancel_btn = QPushButton(self)
    cancel_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    cancel_btn.setText(_("Cancel"))
    cancel_btn.clicked.connect(self.reject)
    self.layout.addWidget(cancel_btn, 2, 1)
    
    dw = 200
    dh = 200
    px = parent.x()
    py = parent.y()
    pw = parent.width()
    ph = parent.height()
    w2 = int((pw - dw) / 2.0)
    h2 = int((ph - dh) / 2.0)

    frame_geometry = QRect(px + w2, py + h2, dw, dh)
    self.setGeometry(frame_geometry)    
  
#======================================================================================
## Library data selection roles
selected_role = Qt.UserRole ## The selected role NONE, SELECTED or REQUIRED
name_role = Qt.UserRole + 1 ## the library name
optional_role = Qt.UserRole + 2 ## The selection is actually optional (True/False value) 
required_libs_role = Qt.UserRole + 3 ## The list of required libraries
optional_libs_role = Qt.UserRole + 4 ## The list of optional libraries


class SelectionType(Enum):
  NONE = auto()     ## Unselected library
  SELECTED = auto() ## Manually selected library
  REQUIRED = auto() ## A required or optional library


class LibraryItemDelegate(QStyledItemDelegate):
  ## Defines the display colours of the library list and requirements list displays.
  #
  # The LibraryItemDelegate class arranges the colours that the library list
  # displays when a library is selected.
  #

  def __init__(self):
    ## Constructor
    QStyledItemDelegate.__init__(self)

  def paint(self, painter, option, index):
    ## Paint method
    painter.save()

    selection_type = index.data(selected_role)
    text = index.data(Qt.DisplayRole)
    optional = index.data(optional_role)

    if optional:
      # displays optional libraries colour
      font = painter.font()
      font.setWeight(QFont.Bold)
      painter.setFont(font)
      pen = painter.pen()
      pen.setColor(QColor('lightblue'))
      painter.setPen(pen)
      painter.drawText(option.rect, Qt.AlignLeft, text)
    elif selection_type == SelectionType.REQUIRED:
      # displays required libraries colour
      font = painter.font()
      font.setWeight(QFont.Bold)
      painter.setFont(font)
      pen = painter.pen()
      pen.setColor(QColor('blue'))
      painter.setPen(pen)
      painter.drawText(option.rect, Qt.AlignLeft, text)
    elif selection_type == SelectionType.SELECTED:
      # displays primary libraries colour
      font = painter.font()
      font.setWeight(QFont.Bold)
      painter.setFont(font)
      pen = painter.pen()
      pen.setColor(QColor('lightgreen'))
      painter.setPen(pen)
      painter.drawText(option.rect, Qt.AlignLeft, text)
    else:  # SelectionType.NONE
      # displays unselected libraries colour
      font = painter.font()
      font.setWeight(QFont.Normal)
      painter.setFont(font)
      pen = painter.pen()
      pen.setColor(QColor('black'))
      painter.setPen(pen)
      painter.drawText(option.rect, Qt.AlignLeft, text)

    painter.restore()


