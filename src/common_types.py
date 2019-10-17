'''
Created on 21 Sep 2019

@author: simonmeaden
'''  

# class classproperty(object):
#   def __init__(self, getter):
#     self.getter= getter
#        
#   def __get__(self, instance, owner):
#     return self.getter(owner)
#  

from enum import Enum, Flag, auto
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
  QButtonGroup,
  QLabel,
  )
from Cython.Compiler.Naming import self_cname
from Cython.Runtime.refnanny import result



#======================================================================================
class ExistAction(Enum):
  SKIP = auto()
  OVERWRITE = auto()
  BACKUP = auto()

class FramePosition(Enum):
  TopLeft = auto()
  Centre = auto()
  
class LibraryStyle(Enum):
  SHARED = auto()
  STATIC = auto()
  SHARED_AND_STATIC = auto()
    

class CompileStyle(Enum):
  NONE = auto(),
  CONFIGURE = auto(),
  
  
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
    for _, v in CompilerType.__members__.items():
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
  NONE = auto(), # Unselected
  SELECTED = auto(), # Selected manually
  REQUIRED = auto(), # Selected as a requirement
 
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
      text =  index.data(Qt.DisplayRole)
       
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
      else: # SelectionType.NONE
          font = painter.font()
          font.setWeight(QFont.Normal)
          painter.setFont(font)
          pen = painter.pen()
          pen.setColor(QColor('black')) 
          painter.setPen(pen)  
          painter.drawText(option.rect, Qt.AlignLeft, text)

      painter.restore()
      
class LibraryDlgResult(Flag):
  NONE = 0,
  STATIC_1 = 1,
  STATIC_2 = 2,
  STATIC_3 = 4,
  SHARED_1 = 8,
  SHARED_2 = 16,
  SHARED_3 = 32,
  
class LibraryTypeDialog(QDialog):
  
      def __init__(self,
                   library_style,
                   shared_libraries,
                   static_libraries,
                   required_libraries, 
                   destination_path,
                   parent = None):
        super(LibraryTypeDialog, self).__init__(parent)
        self.setWindowTitle("Confirm Library Build")
        self.library_style = library_style
        self.shared_libraries = shared_libraries
        self.static_libraries = static_libraries
        self.required_libraries = required_libraries
        self.destination_path = destination_path
        self.result = LibraryDlgResult.NONE
        self.shared_result = LibraryDlgResult.NONE
        self.static_result = LibraryDlgResult.NONE
        
        self.__init_gui()
        
        
      def __init_gui(self):
        main_layout = QGridLayout()
        self.setLayout(main_layout)
        
        common_text_lbl = QLabel(self)
        common_text_lbl.setText('Please select from one of the choices below.\n'
                    'The actual choices depended on your selection\n'
                    'of compiler type, library style and which libraries\n'
                    'you selected and which libraries of the correct style\n'
                    'already exist on the host computer.')
        main_layout.addWidget(common_text_lbl, 0, 0)
        common_text_2_lbl = QLabel(self)
        main_layout.addWidget(common_text_2_lbl, 1, 0)

        existing_shared = []
        required_shared = []
        existing_static = []
        required_static = []
        row = 2
        
        if self.library_style == LibraryStyle.SHARED or self.library_style == LibraryStyle.SHARED_AND_STATIC:
          ''''''
          for library in self.build_order:
            if library in self.shared_libraries:
              existing_shared.append(library)
            else:
              required_shared.append(library)
            if required_shared: # there are some libraries to be created.
              common_text_2_lbl.setText(
                'There are at least {} shared libraries\n'
                'to be built.You will need to select the\n'
                'possible actions from those below.'.format(len(required_shared)))
              text_1 = 'Create all missing shared libraries (and any missing\n' \
                       'requirements) and put then in the destination directory\n' \
                       '{}'
              text_2 = 'Create all missing shared libraries (and any missing\n' \
                       'requirements) and put then in the destination directory\n' \
                       '{}.\n' \
                       'Also copy any existing shared libraries into the same\n' \
                       'directory.'
              text_3 = 'Make completely new versions of all shared libraries ignoring\n' \
                       'existing libraries and store them in the destination directory\n' \
                       '{}'
            shared_grp = QButtonGroup(self)
            shared_grp.setExclusive(True)
            shared_grp.buttonClicked.connect(self.__shared_changed)
            choice_1 = QRadioButton(self)
            choice_1.setText(text_1.format(str(self.destination_path)))
            shared_grp.addButton(choice_1, 1)
            main_layout.addWidget(choice_1, row, 0)
            
            choice_2 = QRadioButton(self)
            choice_2.setText(text_2.format(str(self.destination_path)))
            shared_grp.addButton(choice_2, 2)
            main_layout.addWidget(choice_2, row + 1, 0)
            
            choice_3 = QRadioButton(self)
            choice_3.setText(text_3.format(str(self.destination_path)))
            shared_grp.addButton(choice_3, 3)
            main_layout.addWidget(choice_1, row + 2, 0)
            row += 3
                       
          
        if self.library_style == LibraryStyle.STATIC or self.library_style == LibraryStyle.SHARED_AND_STATIC:
          ''''''
          for library in self.build_order:
            if library in self.static_libraries:
              existing_static.append(library)
            else:
              required_static.append(library)
            if required_static: # there are some libraries to be created.
              common_text_2_lbl.setText(
                'There are at least {} static libraries\n'
                'to be built.You will need to select the\n'
                'possible actions from those below.'.format(len(required_shared)))
      
              text_1 = 'Create all missing static libraries (and any missing\n' \
                       'requirements) and put then in the destination directory\n' \
                       '{}'
              text_2 = 'Create all missing static libraries (and any missing\n' \
                       'requirements) and put then in the destination directory\n' \
                       '{}.\n' \
                       'Also copy any existing static libraries into the same\n' \
                       'directory.'
              text_3 = 'Make completely new versions of all static libraries ignoring\n' \
                       'existing libraries and store them in the destination directory\n' \
                       '{}'
            static_grp = QButtonGroup(self)
            static_grp.setExclusive(True)
            static_grp.buttonClicked.connect(self.__static_changed)
            choice_1 = QRadioButton(self)
            choice_1.setText(text_1.format(str(self.destination_path)))
            static_grp.addButton(choice_1, 4)
            main_layout.addWidget(choice_1, row, 0)
            
            choice_2 = QRadioButton(self)
            choice_2.setText(text_2.format(str(self.destination_path)))
            static_grp.addButton(choice_2, 5)
            main_layout.addWidget(choice_2, row + 1, 0)
            
            choice_3 = QRadioButton(self)
            choice_3.setText(text_3.format(str(self.destination_path)))
            static_grp.addButton(choice_3, 6)
            main_layout.addWidget(choice_1, row + 2, 0)
            row += 3
            
      def __static_changed(self, id):
        ''''''
        if id == 4:
          self.shared_result = LibraryDlgResult.STATIC_1
        elif id == 5:
          self.shared_result = LibraryDlgResult.STATIC_2
        elif id == 6:
          self.shared_result = LibraryDlgResult.STATIC_3
        
      def __shared_changed(self, id):
        ''''''
        if id == 4:
          self.static_result = LibraryDlgResult.STATIC_1
        elif id == 5:
          self.static_result = LibraryDlgResult.STATIC_2
        elif id == 6:
          self.static_result = LibraryDlgResult.STATIC_3
  
      def result(self):
        return self.shared_result | self.static_result
