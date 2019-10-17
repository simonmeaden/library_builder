'''
Created on 24 Sep 2019

@author: simonmeaden
'''

import argparse, os
import subprocess
from pathlib import Path
from ruamel.yaml import YAML
from builtins import FileExistsError
from urllib.request import urlsplit
import urlgrabber
import zipfile, tarfile
import re
from collections import OrderedDict, deque

from PySide2.QtCore import (
    Qt,
#     Signal,
    Slot,
    QRect,
    QResource,
  )
from PySide2.QtGui import (
  QPixmap,
  QIcon,
  QFont,
#   QStandardItemModel,
#   QStandardItem,
#   QBrush,
#   QColor,
#   QPen,
  )
from PySide2.QtWidgets import (
    QDesktopWidget,
    QMainWindow,
    QFrame,
    QPushButton,
    QLabel,
    QComboBox,
#     QListView,
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QPlainTextEdit,
#     QTextEdit,
    QLineEdit,
    QGridLayout,
#     QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
#     QDialog,
#     QStyledItemDelegate,
    QInputDialog,
    QSizePolicy,
    QMessageBox,
  )

from common_types import (
  ExistAction,
  FramePosition,
  LibraryStyle,
  CompilerType,
  CompileStyle,
  Library,
  LibraryType,
  RequiredLibrary,
  selected_role,
  name_role,
  required_libs_role,
  SelectionType,
  ItemDelegate,
  LibraryTypeDialog,
  )
from repository import Repository
from _ast import Or


#======================================================================================
class MainWindow(QMainWindow):
    '''
    classdocs
    '''

    width = 1300
    height = 800

    #======================================================================================
    def __init__(self, params, parent=None):
      '''
      Constructor
      '''
      super(MainWindow, self).__init__(parent)

      self.use_mxe = False
      self.mxe_path = Path()
      self.source_path = Path()
      self.dest_path = Path()
      
      self.current_compiler_type = CompilerType.NONE
      self.current_library_style = LibraryStyle.SHARED
      self.current_include_dest = Path()
      self.current_lib_static = Path()
      self.current_lib_shared = Path()
      self.compiler_selected = False
      self.libraries_selected = False
      self.prepared = False

      self.cpp_list = {}
      self.cc_list = {}
      self.ar_list = {}
      self.ranlib_list = {}
      self.include_list = {}
      self.ld_list = {}
      self.strip_list = {}
      self.shared_list = {}
      self.static_list = {}
      self.build_style = {}
      self.build_order = deque()
      self.shared_libraries = {}
      self.static_libraries = {}
      
      self.requirements_list = OrderedDict()
 
      self.__init_gui()
      self.__parse_arguments(params)
      self.__load_yaml_file()

      self.__load_libraries()

      self.__locate_mxe()
      self.__locate_compiler_apps()

      self.repo = Repository()
      self.repo.send_message[str].connect(self.print_message)

      self.__print_options()
      self.__set_exist_action_lbl()
      self.__set_mxe_lbl()
      self.__set_compilers_list()

      screen_centre = QDesktopWidget().availableGeometry().center()
      widget_width = self.width
      widget_height = self.height
      position = self.position
      frame_geometry = QRect(0, 0, widget_width, widget_height)

      if position == FramePosition.Centre:
        frame_geometry.moveCenter(screen_centre)

      self.setGeometry(frame_geometry)

    def __load_libraries(self):
      self.library_items = {}
      if self.libraries:
        for name in self.libraries:
          item = QListWidgetItem(name)

          library = self.libraries[name]
          item.setData(selected_role, SelectionType.NONE)
          item.setData(name_role, name)
          item.setData(required_libs_role, library.required_libs)
          self.library_list.addItem(item)

    def __load_yaml_file(self):

      yaml = YAML(typ='safe')
      yaml.default_flow_style = False
      yaml_file = Path("libraries.yaml")
      data = yaml.load(yaml_file)

      self.libraries = {}
      libraries = data.get('libraries', {})
      if libraries:
        for lib in libraries:
          l = lib['library']
          if l:
            library = Library()
            library.name = l.get('name')
            library.url = l.get('url')
            library.type = LibraryType[l.get('type')]
            library.libname = l.get('libname')
            rl = l.get('required_libraries')
            if rl:
              req_libs = []
              for r in rl:
                req_lib = RequiredLibrary()
                req_lib.name = r['name']
                req_lib.min_version = r['version']
                req_libs.append(req_lib)
              library.required_libs = req_libs

            self.libraries[library.name] = library

    #======================================================================================
    @Slot()
    def __help(self):
      '''
      '''

    #======================================================================================
    @Slot(str)
    def print_message(self, message):
      self.msg_edit.appendPlainText(message)

    #======================================================================================
    def __set_exist_action_lbl(self):
      if self.exist_action == 'Skip':
        self.exist_lbl.setText('Repositories will be skipped if it already exists.')
      elif self.exist_action == 'Overwrite':
        self.exist_lbl.setText('Repositories will be overwritten if it already exists.')
      elif self.exist_action == 'Backup':
        self.exist_lbl.setText('Repositories will be backed up to {} if it already exists.'.format(self.dest_path))
      else:
        self.exist_lbl.setText("Repositories will be cloned if they don't exist.")

    #======================================================================================
    def __set_mxe_lbl(self):
      if self.mxe_exists:
        if self.mxe_path:
          if not self.use_mxe:
            self.usemxe_lbl.setText("MXE on {} will be used if an MXE compiler is specified".format(self.mxe_path))
          else:
            self.usemxe_lbl.setText("MXE on {} will be used by {}".format(self.mxe_path, self.compiler_type.name()))
        else:
          self.usemxe_lbl.setText("MXE MXE will not be used")
      else:
        self.usemxe_lbl.setText("MXE cannot be found in normal paths,\n"
                                "\u23FA /opt/mxe\n"
                                "\u23FA under users home directory\n"
                                "specify --mxe_path for other locations")

    #======================================================================================
    def __set_compilers_list(self):
      if self.cpp_list:
        compiler_types = list(self.cpp_list)
      else:
        compiler_types.append(str(CompilerType.NONE))

      
      for compiler_type in compiler_types:
        self.compilers.addItem(str(compiler_type))

    #======================================================================================
    def __set_current_compiler_lbl(self):
      ''' Set the chosen compiler label.
      '''
      compiler_type = self.current_compiler_type
      self.chosen_compiler_lbl.setText(str(compiler_type))
      
      include_paths = self.include_list[compiler_type]
      inc_path = ''
      for path in include_paths:
        p = str(path)
        if len(inc_path) > 0:
          inc_path = p + '\n'
        inc_path = inc_path + p
        
      self.include_paths_lbl.setText(inc_path)

      static_paths = self.static_list[compiler_type]
      static_path = ''
      for path in static_paths:
        p = str(path)
        if len(static_path) > 0:
          inc_path = p + '\n'
        static_path = static_path + p
        
      if static_path:
        self.static_paths_lbl.setText(static_path)
      else:
        self.static_paths_lbl.setText('No static libraries')

      shared_paths = self.shared_list[compiler_type]
      shared_path = ''
      for path in shared_paths:
        p = str(path)
        if len(shared_path) > 0:
          inc_path = p + '\n'
        shared_path = shared_path + p
      
      if shared_path:
        self.shared_paths_lbl.setText(shared_path)
      else:
        self.shared_paths_lbl.setText('No shared libraries')


    #======================================================================================
    def __select_compiler_clicked(self, item):
      ''' Choose a compiler from available compilers.
      '''
      self.current_compiler_type = CompilerType.from_name(item.text())
      type = self.current_compiler_type

      self.current_cpp = self.cpp_list[type]
      self.current_cc = self.cc_list[type]
      self.current_ar = self.ar_list[type]
      self.current_ranlib = self.ranlib_list[type]
      self.current_includes = self.include_list[type]
      self.current_static = self.static_list[type]
      self.current_shared = self.shared_list[type]
      
      if (type == CompilerType.GCC_NATIVE or 
          type == CompilerType.MINGW_32_NATIVE or 
          type == CompilerType.MINGW_64_NATIVE):
        self.library_style_box.clear()
        self.library_style_box.addItems(['Shared', 'Static', 'Shared and Static'])
        self.current_library_style = LibraryStyle.SHARED_AND_STATIC
        self.chosen_style_lbl.setText('Shared and Static Libraries available')

      elif (type == CompilerType.MINGW_32_MXE_SHARED or 
            type == CompilerType.MINGW_64_MXE_SHARED):
        self.library_style_box.clear()
        self.library_style_box.addItems(['Shared',])
        self.current_library_style = LibraryStyle.SHARED
        self.chosen_style_lbl.setText('Only Shared Libraries available')

      elif (type == CompilerType.MINGW_32_MXE_STATIC or 
            type == CompilerType.MinGW_64_MXE_STATIC):
        self.library_style_box.clear()
        self.library_style_box.addItems(['Static',])
        self.current_library_style = LibraryStyle.STATIC
        self.chosen_style_lbl.setText('Only Static Libraries available')

      if type != CompilerType.NONE:
        self.compiler_selected = True;
      else:
        self.compiler_selected = False

      self.__set_current_compiler_lbl()
      self.__check_prepared() 
      
      
      
    def __check_selection(self):
      if self.current_compiler_type == CompilerType.NONE:
        if not self.build_order:
          QMessageBox.warning(
            self, 
            "Compiler Error", 
            'You have not selected either a compiler,\n'
            'or a library!\n'
            'Choose a compiler and one or more libraries and try again!', 
            QMessageBox.Ok
            )
          return False
        else:
          QMessageBox.warning(
            self, 
            "Compiler Error", 
            'You have not selected a compiler,\n'
            'Choose a compiler and try again!', 
            QMessageBox.Ok
            )
          return False
      elif not self.build_order:
        QMessageBox.warning(
          self, 
          "Compiler Error", 
          'You have not selected a library to build,\n'
          'Choose one or more libraries and try again!', 
          QMessageBox.Ok
          )
        return False
      return True
  
  
      

    def __update_existing_library_tbl(self, shared_libraries, static_libraries):
      if (self.current_library_style == LibraryStyle.STATIC or 
        self.current_library_style == LibraryStyle.SHARED_AND_STATIC):
        for n, p in static_libraries.items():
          row = self.static_library_tbl.rowCount()
          self.static_library_tbl.insertRow(row)
          self.static_library_tbl.setItem(row, 0, QTableWidgetItem(n))
          item = QTableWidgetItem(str(p))
          item.setToolTip(str(p))
          self.static_library_tbl.setItem(row, 1, item)
      
      if (self.current_library_style == LibraryStyle.SHARED or 
        self.current_library_style == LibraryStyle.SHARED_AND_STATIC):
        for n, p in shared_libraries.items():
          row = self.shared_library_tbl.rowCount()
          self.shared_library_tbl.insertRow(row)
          self.shared_library_tbl.setItem(row, 0, QTableWidgetItem(n))
          item = QTableWidgetItem(str(p))
          item.setToolTip(str(p))
          self.shared_library_tbl.setItem(row, 1, item)



    def __prepare_libraries(self):
      '''
      '''
      if not self.__check_selection():
        return
      
      if self.build_order:
        self.shared_library_tbl.setRowCount(0)
        self.static_library_tbl.setRowCount(0)
        
        for lib_name in self.build_order:
          library = self.libraries[lib_name]
          lib_type = library.type
          url = library.url
          name = library.name
          libname = library.libname
          
          self.print_message('Working on {}'.format(libname))

          # download to special directory
          download_path = self.dest_path / 'library_builder' / 'downloads'
          download_path.mkdir(parents=True, exist_ok=True)
          
          exists, shared_libraries, static_libraries = self.__detect_existing_library(name, libname)
          
          if exists:
            self.shared_libraries = {**self.shared_libraries, **shared_libraries}
            self.static_libraries = {**self.static_libraries, **static_libraries}
            self.__update_existing_library_tbl(shared_libraries, static_libraries)
            
      if self.prepared:
        self.build_btn.setEnabled(True)

#           else:
#             
#             self.__download_library_sources(name, libname, lib_type, url, download_path)
            # Detect configure style                                      
                
#             fname = ''
#             lib_path = Path()
#             
#             for fname in dirs:
#               f_path = download_path / fname
#               if f_path.exists(): 
#                 lib_path = f_path
#                 break
#                                     
#             configure = lib_path / 'configure'
#             if configure.exists() and configure.is_file():
#               # configure file exists
#               self.build_style[name] = (CompileStyle.CONFIGURE, configure)



    def __build_libraries(self):
      ''' build the libraries
      '''
        
      self.__create_output_directories()
      
      dlg = LibraryTypeDialog(self.current_library_style,
                              self.shared_libraries,
                              self.static_libraries,
                              self.build_order,
                              self.dest_path,
                              self)
      dlg.show()
      result = dlg.result()
      
        
      # TODO


#       for lib_name in self.build_order:
#         build_data = self.build_style[lib_name]
#         if build_data:
#           style = build_data[0]
#           if style == CompileStyle.CONFIGURE:
#             path = build_data[1]
#             self.__configure(path)
      print()
      # TODO More shit


    
    def __configure(self, path):
      ''' '''
      parent_path = path.parent
      os.chdir(parent_path)
      type = self.current_compiler_type
      
      if type == CompilerType.GCC_NATIVE:
        configure_str = './configure'
        
      elif type == CompilerType.MINGW_32_NATIVE:
        ''''''
        configure_str = './configure'
        configure_str += ' --host={}'.format('i686-w64-mingw32')
        dest_path = self.dest_path
        configure_str += ' --prefix={}'.format(dest_path)
        configure_str += ' -I{}'.format(self.include_list[CompilerType.MINGW_32_NATIVE])
        configure_str += ' -L{}'.format(self.library_list[CompilerType.MINGW_32_NATIVE])
 
      elif type == CompilerType.MINGW_64_NATIVE:
        ''''''
        configure_str = './configure'
        configure_str += ' --host={}'.format('x86_64-w64-mingw32')
        dest_path = self.dest_path
        configure_str += ' --prefix={}'.format(dest_path)
        configure_str += ' -I{}'.format(self.include_list[CompilerType.MINGW_64_NATIVE])
        configure_str += ' -L{}'.format(self.library_list[CompilerType.MINGW_64_NATIVE])

      elif type == CompilerType.MINGW_32_MXE_SHARED:
        ''''''
        configure_str = './configure'
        configure_str += ' --host={}'.format('i686-w64-mingw32')
        dest_path = self.dest_path
        configure_str += ' --prefix={}'.format(dest_path)
        configure_str += ' -I{}'.format(self.include_list[CompilerType.MINGW_32_MXE_SHARED])
        configure_str += ' -L{}'.format(self.library_list[CompilerType.MINGW_32_MXE_SHARED])
      
      elif type == CompilerType.MINGW_32_MXE_STATIC:
        ''''''
        configure_str = './configure'
        configure_str += ' --host={}'.format('i686-w64-mingw32')
        dest_path = self.dest_path
        configure_str += ' --prefix={}'.format(dest_path)
        configure_str += ' -I{}'.format(self.include_list[CompilerType.MINGW_32_MXE_STATIC])
        configure_str += ' -L{}'.format(self.library_list[CompilerType.MINGW_32_MXE_STATIC])
      
      elif type == CompilerType.MinGW_64_MXE_STATIC:
        ''''''
        configure_str = './configure'
        configure_str += ' --host={}'.format('x86_64-w64-mingw32')
        dest_path = self.dest_path
        configure_str += ' --prefix={}'.format(dest_path)
        configure_str += ' -I{}'.format(self.include_list[CompilerType.MinGW_64_MXE_STATIC])
        configure_str += ' -L{}'.format(self.library_list[CompilerType.MinGW_64_MXE_STATIC])

      elif type == CompilerType.MINGW_64_MXE_SHARED:
        ''''''
        configure_str = './configure'
        configure_str += ' --host={}'.format('x86_64-w64-mingw32')
        dest_path = self.dest_path
        configure_str += ' --prefix={}'.format(dest_path)
        configure_str += ' -I{}'.format(self.include_list[CompilerType.MINGW_64_MXE_SHARED])
        configure_str += ' -L{}'.format(self.library_list[CompilerType.MINGW_64_MXE_SHARED])
       
      completed = subprocess.run(configure_str)
      self.print_message('Configure completed with returncode {}'.format(completed.returncode))
        

   #======================================================================================
    def __create_output_directories(self):
      '''Creates necessary paths for the library.

      Creates the paths dependant on the specified compiler, whether
      static or shared libraries are chosen, and creates
      lib and include directories based on the supplied and required --dest_path.

      libpath mingw32.static      + lib      # Native MinGw32 i686
                                  + include
              mingw64.static      + lib      # Native MinGw32 x86_64
                                  + include
      libpath mingw32.shared      + lib      # Native MinGw32 i686
                                  + include
              mingw64.shared      + lib      # Native MinGw32 x86_64
                                  + include
              mxe.mingw32.shared  + lib      # Shared MXS MinGw32 i686
                                  + include
              mxe.mingw64.shared  + lib      # Shared MXS MinGw32 x86_64
                                  + include
              mxe.mingw32.static  + lib      # Static MXS MinGw32 i686
                                  + include
              mxe.mingw64.static  + lib      # Static MXS MinGw32 x86_64
                                  + include
              unix.static         + lib      # Native g++ x86_64
                                  + include

              unix.shared         + lib      # Native g++ x86_64
                                  + include

      Note that if mxe is used either .static or .shared libraries are created.
      the associated current_lib_static or current_lib_shared will hanve a
      Path value, the other will have None.
      '''
      if self.dest_path:
        out_lib_path = Path(self.dest_path) / 'lib'

        if self.current_compiler_type == CompilerType.GCC_NATIVE:
          inc_path = out_lib_path / 'unix/include'          
          dest_static = out_lib_path / 'unix.static/lib'          
          dest_shared = out_lib_path / 'unix.shared/lib'          

        elif self.current_compiler_type == CompilerType.MINGW_32_NATIVE:
          inc_path = out_lib_path / 'mingw32/include'          
          dest_static = out_lib_path / 'mingw32.static/lib'
          dest_shared = out_lib_path / 'mingw32.shared/lib'          

        elif self.current_compiler_type == CompilerType.MINGW_64_NATIVE:
          inc_path = out_lib_path / 'mingw64/include'
          dest_static = out_lib_path / 'mingw64.static/lib'
          dest_shared = out_lib_path / 'mingw64.shared/lib'          

        elif self.current_compiler_type == CompilerType.MINGW_32_MXE_SHARED:
          inc_path = out_lib_path / 'mxe.mingw32.shared/include'
          dest_static = None
          dest_shared = out_lib_path / 'mxe.mingw32.shared/lib'          

        elif self.current_compiler_type == CompilerType.MINGW_64_MXE_SHARED:
          inc_path = out_lib_path / 'mxe.mingw64.shared/include'
          dest_static = None
          dest_shared = out_lib_path / 'mxe.mingw64.shared/lib'          

        elif self.current_compiler_type == CompilerType.MINGW_32_MXE_STATIC:
          inc_path = out_lib_path / 'mxe.mingw32.static/include'
          dest_static = out_lib_path / 'mxe.mingw32.static/lib'   
          dest_shared = None       

        elif self.current_compiler_type == CompilerType.MinGW_64_MXE_STATIC:
          inc_path = out_lib_path / 'mxe.mingw64.static/include'
          dest_static = out_lib_path / 'mxe.mingw64.static/lib'
          dest_shared = None       

        # create the actual paths if they don't already exist
        inc_path.mkdir(parents=True, exist_ok=True)
        if dest_shared:
          dest_shared.mkdir(parents=True, exist_ok=True)
        if dest_static:
          dest_static.mkdir(parents=True, exist_ok=True)

        # send created message to log
        self.print_message('Include path {} for {} created.'.format(inc_path, self.current_compiler_type.name))
        self.print_message('Library path {} for {} created.'.format(inc_path, self.current_compiler_type.name))

        # save paths to self
        self.current_include_dest = inc_path
        self.current_lib_static = dest_static
        self.current_lib_shared = dest_shared

    #======================================================================================
    def __check_prepared(self):
      self.prepared = (self.compiler_selected and self.libraries_selected)
      if (self.prepared):
        self.prepare_btn.setEnabled(True)
        
      else:
        self.prepare_btn.setEnabled(False)



    def __select_libraries_clicked(self, item):
      ''' Select a library to build.

      Selects a library, and recurses through it's required libraries,
      marking those that are required to build the requested library
      and creating a build order list to make certain that all required
      libraries are built first. If a library is removed then all required
      libraries are also removed unless required by a different selection.
      
      Also defines a build order for the libraries, required libraries first.
      '''
      selection_type = item.data(selected_role)
      required_libs = item.data(required_libs_role)
      lib_name = item.data(name_role)
      
      if selection_type == SelectionType.SELECTED:
        selection_type = SelectionType.NONE
        item.setToolTip('Library not selected')
      elif selection_type == SelectionType.NONE:
        selection_type = SelectionType.SELECTED
        item.setToolTip('Library was selected by user')
      elif selection_type == SelectionType.REQUIRED:
        QMessageBox.warning(self, 
                            'Deletion Warning', 
                            'You are attempting to remove {},\n'
                            'which is a required library.\n'
                            'This is not allowed.'.format(lib_name), 
                            QMessageBox.Ok)
        return
        
      item.setData(selected_role, selection_type)
      if lib_name not in self.requirements_list:
        self.requirements_list[lib_name] = []
        
      if lib_name not in self.build_order:
        self.build_order.append(lib_name)
        
      required_by = []

      if selection_type == SelectionType.SELECTED:
        # select it.
        # set requirement for this library.
        required_by.append(lib_name)
        
        for req_lib in required_libs:
          for req_item in self.library_list.findItems(req_lib.name, Qt.MatchExactly):  # should only be one
            req_lib_name = req_item.data(name_role)
            
            # add required library to the requirement list
            if lib_name in list(self.requirements_list):
              if req_lib_name not in self.requirements_list.get(lib_name, []):
                self.requirements_list[lib_name].append(req_lib_name)
            else:
              self.requirements_list[lib_name] = [req_lib_name,]
              
            if req_item.text() == req_lib_name:
              req_item.setData(selected_role, SelectionType.REQUIRED)
              req_item.setToolTip('Library was selected as a required library')

            self.__recurse_required_libraries(lib_name, req_item)
                    
      else:
        # remove non-required libraries
        if lib_name in list(self.requirements_list):          
          requirements = self.requirements_list.pop(lib_name)
          # First set all required libraries to not required.
          for req_lib in requirements:
            for req_item in self.library_list.findItems(req_lib, Qt.MatchExactly):
              req_item.setData(selected_role, SelectionType.NONE)
        # Unfortunately they may be required by some other library.
        # so possible reset them
        for _, requirements in  self.requirements_list.items():
          for req_lib in requirements:
            for req_item in self.library_list.findItems(req_lib, Qt.MatchExactly):
              req_item.setData(selected_role, SelectionType.REQUIRED)
                    
      self.requirements_tree.clear()
      for required in list(self.requirements_list):      
        item = self.__add_primary_library_to_tree(required)
        for requirement in self.requirements_list[required]:
          self.__add_library_requirements_to_tree(item, requirement)
        
      self.requirements_tree.expandAll()
        
      self.build_order_list.clear()
      for lib in self.build_order:
        self.build_order_list.addItem(lib)
        
      # if build order list is not empty then some libraries have been selected
      if self.build_order: 
        self.libraries_selected = True
      else:
        self.libraries_selected = False
       
      self.__check_prepared() 
            
                
    def __add_primary_library_to_tree(self, name):
      ''' Adds primary libraries to the library tree '''
      item = QTreeWidgetItem(self.requirements_tree);
      item.setText(0, name);
      return item
      
      
      
    def __add_library_requirements_to_tree(self, parent_item, name):
      ''' Adds required libraries to the library tree. '''
      item = QTreeWidgetItem()
      item.setText(0, name)
      parent_item.addChild(item)



    def __recurse_required_libraries(self, lib_name, item):
      selection_type = item.data(selected_role)
      required_libs = item.data(required_libs_role)
      name = item.data(name_role)
      
      # this will make the required lib earlier in the build queue
      if lib_name in self.build_order:
        self.build_order.remove(lib_name)
      self.build_order.appendleft(name)
      
      if selection_type == SelectionType.REQUIRED:
        for req_lib in required_libs:
          for req_item in self.library_list.findItems(req_lib.name, Qt.MatchExactly):  # should only be one
            req_lib_name = req_item.data(name_role)
            
            # add required library to the requirements list
            if lib_name in list(self.requirements_list):
              if req_lib_name not in self.requirements_list.get(lib_name, []):
                self.requirements_list[lib_name].append(req_lib_name)
            else:
              self.requirements_list[lib_name] = [req_lib_name,]

            if req_item.text() == req_lib_name:
              req_item.setData(selected_role, SelectionType.REQUIRED)
              req_item.setToolTip('Library was selected as a required library')
              
            self.__recurse_required_libraries(req_lib_name, req_item)
       
       
            
    def __clear_libraries(self):
      ''' Clears all library selections.
      '''
      self.build_order_list.clear()
      for row in range(self.library_list.count()):
        item = self.library_list.item(row)
        item.setText(item.data(name_role))
        item.setData(selected_role, SelectionType.NONE) 
      
      

    #= Initialise the GUI =================================================================
    def __init_btn_frame(self):
      exit_icon = QIcon(QPixmap(":/exit"))
      help_icon = QIcon(QPixmap(":/help"))
      build_icon = QIcon(QPixmap(":/build"))

      btn_frame = QFrame(self)
      btn_layout = QHBoxLayout()
      btn_frame.setLayout(btn_layout)
            
      help_btn = QPushButton(self)
      help_btn.setIcon(help_icon)
      help_btn.setToolTip("Help")
      btn_layout.addWidget(help_btn)
      help_btn.clicked.connect(self.__help)
      
      prepare_btn = QPushButton(self)
#       prepare_btn.setIcon(prepare_icon)
      prepare_btn.setText("Prepare Libraries")
      prepare_btn.setEnabled(False)
      prepare_btn.setToolTip("Prepare Libraries")
      btn_layout.addWidget(prepare_btn)
      prepare_btn.clicked.connect(self.__prepare_libraries)
      self.prepare_btn = prepare_btn
      
      build_btn = QPushButton(self)
      build_btn.setIcon(build_icon)
      build_btn.setText("Build Libraries")
      build_btn.setEnabled(False)
      build_btn.setToolTip("Build Libraries")
      btn_layout.addWidget(build_btn)
      build_btn.clicked.connect(self.__build_libraries)
      self.build_btn = build_btn
      
      close_btn = QPushButton(self)
      close_btn.setIcon(exit_icon)
      close_btn.setToolTip("Close the application")
      btn_layout.addWidget(close_btn)
      close_btn.clicked.connect(self.close)
      
      return btn_frame


    def __init_source_frame(self):
      source_frame = QFrame(self)
      source_frame.setContentsMargins(0, 0, 0, 0)
      source_layout = QGridLayout()
      source_layout.setContentsMargins(0, 0, 0, 0)
      source_layout.setColumnStretch(0, 3)
      source_layout.setColumnStretch(1, 1)
      source_frame.setLayout(source_layout)
      
      self.source_path_lbl = QLabel(self)
      self.source_path_lbl.setToolTip('The base directory in which the library source files\n'
        'will be built. Library source files will be created in\n'
        'directory trees underneath this directory.')
      source_layout.addWidget(self.source_path_lbl, 0, 0)
      
      source_btn = QPushButton('Modify', self)
      source_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      source_btn.clicked.connect(self.__source_path_clicked)
      source_layout.addWidget(source_btn, 0, 1)
      
      return source_frame


    def __init_destination_frame(self):
      dest_frame = QFrame(self)
      dest_frame.setContentsMargins(0, 0, 0, 0)
      dest_layout = QGridLayout()
      dest_layout.setContentsMargins(0, 0, 0, 0)
      dest_layout.setColumnStretch(0, 3)
      dest_layout.setColumnStretch(1, 1)
      dest_frame.setLayout(dest_layout)
      
      self.dest_path_lbl = QLabel(self)
      self.dest_path_lbl.setToolTip('The base directory in which the library files will be stored\n'
        'after the build. Library files files will be placed in\n'
        'directory trees underneath this directory, dependant on\n'
        'the build type e.g. "dest_path/unix/lib" and "dest_path/unix/include.')
      dest_layout.addWidget(self.dest_path_lbl, 0, 0)
      
      dest_btn = QPushButton('Modify', self)
      dest_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      dest_btn.clicked.connect(self.__dest_path_clicked)
      dest_layout.addWidget(dest_btn, 0, 1)
      return dest_frame

    def __init_compiler_frame(self):
      frame_1 = QFrame(self)
      layout_1 = QFormLayout()
      frame_1.setLayout(layout_1)

      source_frame = self.__init_source_frame()
      layout_1.addRow("Source Path:", source_frame)

      dest_frame = self.__init_destination_frame()
      layout_1.addRow("Destination Path:", dest_frame)
      
      self.exist_lbl = QLabel(self)
      layout_1.addRow("Repository Exists Action:", self.exist_lbl)
      
      self.usemxe_lbl = QLabel(self)
      layout_1.addRow("Use MXE:", self.usemxe_lbl)
      
      self.compilers = QListWidget(self)
      self.compilers.itemClicked.connect(self.__select_compiler_clicked)
      layout_1.addRow("Available Compilers:", self.compilers)
      
      self.chosen_compiler_lbl = QLabel(self)
      layout_1.addRow("Chosen Compiler:", self.chosen_compiler_lbl)
      
      self.library_style_box = QComboBox(self)
      self.library_style_box.addItems(['Shared', 'Static', 'Shared and Static'])
      self.library_style_box.currentTextChanged.connect(self.__choose_library_style)
      layout_1.addRow("Library Style's:", self.library_style_box)
      
      self.chosen_style_lbl = QLabel(self)
      layout_1.addRow("Chosen Library Style:", self.chosen_style_lbl)
      
      self.include_paths_lbl = QLabel(self)
      layout_1.addRow("Include Paths:", self.include_paths_lbl)
      
      self.static_paths_lbl = QLabel(self)
      layout_1.addRow("Static Library Paths:", self.static_paths_lbl)
      
      self.shared_paths_lbl = QLabel(self)
      layout_1.addRow("Shared Library Paths:", self.shared_paths_lbl)
      
      headers = ['Library', 'Path']
      self.shared_library_tbl = QTableWidget(self)
      self.shared_library_tbl.setColumnCount(2)
      self.shared_library_tbl.setSelectionMode(QAbstractItemView.NoSelection)
      self.shared_library_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
      self.shared_library_tbl.horizontalHeader().setStretchLastSection(True)
      self.shared_library_tbl.setHorizontalHeaderLabels(headers);
      layout_1.addRow("Shared Library Paths:", self.shared_library_tbl)
      
      self.static_library_tbl = QTableWidget(self)
      self.static_library_tbl.setColumnCount(2)
      self.static_library_tbl.setSelectionMode(QAbstractItemView.NoSelection)
      self.static_library_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
      self.static_library_tbl.horizontalHeader().setStretchLastSection(True)
      self.static_library_tbl.setHorizontalHeaderLabels(headers);
      layout_1.addRow("Static Library Paths:", self.static_library_tbl)
      
      
      return frame_1

    def __choose_library_style(self, text):
      ''' '''
      if text == 'Shared':
        self.current_library_style = LibraryStyle.SHARED
        self.chosen_style_lbl.setText('Shared Libraries')
      elif text == 'Static':
        self.current_library_style = LibraryStyle.STATIC
        self.chosen_style_lbl.setText('Static Libraries')
      elif text == 'Shared and Static':
        self.current_library_style = LibraryStyle.SHARED_AND_STATIC
        self.chosen_style_lbl.setText('Both Shared and Static Libraries')
      
      

    def __init_libraries_frame(self):
      libraries_frame = QFrame(self)
      lib_layout = QGridLayout()
      libraries_frame.setLayout(lib_layout)

      library_lbl = QLabel("Available Libraries :", self)
      library_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      lib_layout.addWidget(library_lbl, 0, 0)
      
      library_list = QListWidget(self)
      item_delegate = ItemDelegate(library_list, self)
      library_list.setItemDelegate(item_delegate)
      library_list.itemClicked.connect(self.__select_libraries_clicked)
      lib_layout.addWidget(library_list, 1, 0)
      self.library_list = library_list
      
      requirements_lbl = QLabel("Requirements :", self)
      requirements_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      lib_layout.addWidget(requirements_lbl, 0, 1)
      requirements_tree = QTreeWidget(self)
      requirements_tree.setColumnCount(1)
      headers = ['Library']
      requirements_tree.setHeaderLabels(headers);
      lib_layout.addWidget(requirements_tree, 1, 1, 2, 1)
      self.requirements_tree = requirements_tree
      
      clear_btn = QPushButton('Clear Libraries', self)
      clear_btn.clicked.connect(self.__clear_libraries)
      lib_layout.addWidget(clear_btn, 2, 0)
      
      build_order_lbl = QLabel("Build Order :", self)
      build_order_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      lib_layout.addWidget(build_order_lbl, 0, 2)
      
      build_order_list = QListWidget(self)
      self.build_order_list = build_order_list
      lib_layout.addWidget(build_order_list, 1, 2, 2, 1)
      
      msg_edit = QPlainTextEdit(self)
      msg_edit.setFont(QFont("Courier", 10))
      lib_layout.addWidget(msg_edit, 3, 0, 1, 3)
      self.msg_edit = msg_edit
      
      lib_layout.setRowStretch(0, 1)
      lib_layout.setRowStretch(1, 4)
      lib_layout.setRowStretch(3, 4)
      lib_layout.setColumnStretch(0, 1)
      lib_layout.setColumnStretch(1, 2)
      lib_layout.setColumnStretch(2, 1)
      
      return libraries_frame
    

    def __init_gui(self):
      ''' initialise the gui.
      '''

      main_frame = QFrame(self)
      main_layout = QGridLayout()
      main_frame.setLayout(main_layout)
      self.setCentralWidget(main_frame)

      """
      Compiler frame. Holds data like source/destination paths
      list of available compilers, displays library and include
      paths etc.
      """
      compiler_frame = self.__init_compiler_frame()
      main_layout.addWidget(compiler_frame, 0, 0)

      """ Libraries frame. Holds the list of available libraries and allows
      the user to select the libraries that they want to install.
      Required libraries will be selecte automatically
      """
      libraries_frame = self.__init_libraries_frame()
      main_layout.addWidget(libraries_frame, 0, 1)

      """ main buttons, help, quit etc. """
      btn_frame = self.__init_btn_frame()
      main_layout.addWidget(btn_frame, 1, 0, 1, 2)

      main_layout.setColumnStretch(0, 2)
      main_layout.setColumnStretch(1, 5)

 
    #======================================================================================
    def __check_path_permission(self, path):

      try:
        path.mkdir(parents=True)
      except FileExistsError:
        self.print_message("Path exists")

      filepath = path / 'test_file_permission'
      try:
        filehandle = open(filepath, 'w')
      except IOError:
        self.print_message('You do not have permission to write to {}'.format(str(self.source_path)))
        self.print_message(
          'Either change this directory to one that you do have\n'
          'permission for or Library Builder will ask you for\n'
          'your sudo password later.')

    def __source_path_clicked(self):
      ''''''
      input_text, ok = QInputDialog.getText(self,
                                       'Change Source Path',
                                       'Enter new source path',
                                       QLineEdit.EchoMode.Normal,
                                       str(self.source_path))
      if ok:
        self.source_path = Path(input_text)
        self.__check_path_permission(self.source_path)

    def __dest_path_clicked(self):
      ''''''
      input_text, ok = QInputDialog.getText(self,
                                       'Change Destination Path',
                                       'Enter new destination path',
                                       QLineEdit.EchoMode.Normal,
                                       str(self.dest_path))
      if ok:
        self.source_path = Path(input_text)
        self.__check_path_permission(self.dest_path)

    #======================================================================================
    def __print_options(self):
      ''' Prints a list of command line arguments.
      '''
      self.print_message("Library source : {}".format(self.dest_path.name))
      self.print_message("Library destination : {}".format(self.source_path.name))
      self.print_message("Exist action     : {}".format(self.exist_action))
      self.print_message("Supplied MXE path: {}".format(self.mxe_path))

    #======================================================================================
    def __locate_mxe(self):
      ''' Attempt to find the MXE cross compiler libraries.

      Searches the suggested paths for the MXE cross compiler system.

      Paths searched by default are 'opt/mxe' for a system wide setup or
      under the users home directory. This second option can take a
      significant time, depending on the size of the home directory so
      this action can be overridden by supplying a path in the --mxe_path
      command line argument.

      '''

      mxe_exists = False
      mxe_path = self.mxe_path

      # Check if --mxe_path was set and was a vialble MXE path
      if not mxe_path.name:  # default value is an empty path

        # if either the --mxe_path was NOT set or it was but the path
        # doesn't exist then start searching in the other directories.
        # check /opt/mxe_path first as this is recommended for system wide location
        srchpath = Path('/opt/mxe')

        if srchpath.exists():
          mxe_path = srchpath  # /opt/mxe exists

        # if not there search in home directory for 'mxe' directory.
        # Last preferable option as this search takes a fair amount of time.
        else:
          srchpath = Path.home()
          for p in list(srchpath.rglob('mxe')):
            mxe_path = p

      if mxe_path.exists():
        # the file src/mxe-conf.mk should exist in the MXE directory so
        # check that it does. This should indicate a good MXE setup, hopefully.
        check_file = mxe_path / 'src' / 'mxe-conf.mk'
        if check_file.exists() and check_file.is_file():
          mxe_exists = True
          self.print_message('MXE found at {}'.format(self.mxe_path))

      else:
        # check file was not found so probably a defunct MXE or a different setup.
        self.print_message("MXE not found.")
        self.print_message("Searched in '/opt' and your home directory for MXE")
        self.print_message("Use --mxe_path if you want to use MXE and it is not located in these locations.")

      self.mxe_path = mxe_path
      self.mxe_exists = mxe_exists

    #======================================================================================
    def __detect_app_type(self, app_name, filename, app_list):
      fnlower = filename.name.lower()
      base_path = filename.parent.parent
      compiler_type = CompilerType.NONE
      
      if filename.name.endswith(app_name):
        if fnlower == app_name:  # native
          compiler_type = CompilerType.GCC_NATIVE
          
        elif 'static' in fnlower:
          if fnlower.startswith('x86_64'):
            compiler_type = CompilerType.MinGW_64_MXE_STATIC

          elif fnlower.startswith('i686'):
            compiler_type = CompilerType.MINGW_32_MXE_STATIC

        elif 'shared' in fnlower:
          if fnlower.startswith('x86_64'):
            compiler_type = CompilerType.MINGW_64_MXE_SHARED

          elif fnlower.startswith('i686'):
            compiler_type = CompilerType.MINGW_32_MXE_SHARED

        elif 'mingw32' in fnlower:
          if fnlower.startswith('x86_64'):
            compiler_type = CompilerType.MINGW_64_NATIVE

          elif fnlower.startswith('i686'):
            compiler_type = CompilerType.MINGW_32_NATIVE            
            
      if compiler_type != CompilerType.NONE:
        app_list[compiler_type] = filename
        
      return (compiler_type, base_path)
    

    def __merge_apps_to_app_list(self, apps, app_list):
      new_list = {}
      if apps:
        for name in apps:
          new_list[name] = apps[name]
      return {**app_list, **new_list}

    def __detect_compiler_apps_in_path(self, root_path):
      ''' Find any gcc/g++ compilers in the selected path.
      '''
      all_cpp = {}
      all_cc = {}
      all_ar = {}
      all_ranlib = {}
      all_ld = {}
      all_strip = {}
      all_include = {}
      all_static = {}
      all_shared = {}

      if root_path.name == 'bin':
          bin_path = root_path
      else:
        if root_path == self.mxe_path:
          bin_path = root_path / 'usr' / 'bin'
        else:  # probably never happen
          bin_path = root_path / 'bin'

      filelist = list(bin_path.glob('*g++'))
      if filelist:
        for filename in filelist:          
          compiler_type = CompilerType.NONE
          compiler_type, base_path = self.__detect_app_type('g++', filename, all_cpp)
          if compiler_type == CompilerType.NONE:
            continue

          includes = []
          shared_libs = []
          static_libs = []
          if compiler_type == CompilerType.GCC_NATIVE:
            
            includes.append(base_path / 'include')
            shared_libs.append(base_path / 'lib')
            shared_libs.append(base_path / 'lib64')
            static_libs = shared_libs      
                
          elif (compiler_type == CompilerType.MINGW_32_NATIVE or 
                compiler_type == CompilerType.MINGW_64_NATIVE):
            
            base_path = base_path / filename.name[:-4]
            includes.append(base_path / 'include')
            shared_libs.append(base_path / 'sys-root/mingw/lib')
            static_libs.append(base_path / 'sys-root/mingw/lib')
            
          elif (compiler_type == CompilerType.MINGW_32_MXE_SHARED or
                compiler_type == CompilerType.MINGW_64_MXE_SHARED):
            
            base_path = base_path / filename.name[:-4]
            includes.append(base_path / 'include')
            shared_libs.append(base_path / 'lib')
            
          elif (compiler_type == CompilerType.MINGW_32_MXE_STATIC or
                compiler_type == CompilerType.MinGW_64_MXE_STATIC):
            
            base_path = base_path / filename.name[:-4]
            includes.append(base_path / 'include')
            static_libs.append(base_path / 'lib')
            
          else:
            ''' Others??? '''
            
          all_include[compiler_type] = includes
          all_static[compiler_type] = static_libs
          all_shared[compiler_type] = shared_libs

            
      filelist = list(bin_path.glob('*gcc'))
      if filelist:
        for filename in filelist:
          self.__detect_app_type('gcc', filename, all_cc)

      filelist = list(bin_path.glob('*ar'))
      if filelist:
        for filename in filelist:
          self.__detect_app_type('ar', filename, all_ar)

      filelist = list(bin_path.glob('*ranlib'))
      if filelist:
        for filename in filelist:
          self.__detect_app_type('ranlib', filename, all_ranlib)

      filelist = list(bin_path.glob('*ld'))
      if filelist:
        for filename in filelist:
          self.__detect_app_type('ld', filename, all_ld)

      filelist = list(bin_path.glob('*strip'))
      if filelist:
        for filename in filelist:
          self.__detect_app_type('strip', filename, all_strip)

      return (all_cpp,
              all_cc, 
              all_ar, 
              all_ranlib, 
              all_ld,
              all_strip, 
              all_include, 
              all_shared, 
              all_static)

    def __locate_compiler_apps(self):
      ''' Locate all gcc type compilers.

      Locates any existing gcc/g++ compilers in the usual Linux PurePaths
      '/usr/bin' and '/usr/local/bin', plus if located in the MXE directory.
      '''
      cpp_list = {}
      cc_list = {}
      ar_list = {}
      ranlib_list = {}
      ld_list = {}
      strip_list = {}
      include_list = {}
      shared_list = {}
      static_list = {}
      usr_paths = [Path('/usr/bin'), 
                   Path('usr/local/bin'), 
                   self.mxe_path]

      for usr_path in usr_paths:
        if usr_path:
          cpps, ccs, ars, ranlibs, lds, strips, include_sublist, shared_sublist, static_sublist = self.__detect_compiler_apps_in_path(usr_path)
          cpp_list = self.__merge_apps_to_app_list(cpps, cpp_list)
          cc_list = self.__merge_apps_to_app_list(ccs, cc_list)
          ar_list = self.__merge_apps_to_app_list(ars, ar_list)
          ranlib_list = self.__merge_apps_to_app_list(ranlibs, ranlib_list)
          ld_list = self.__merge_apps_to_app_list(lds, ld_list)
          strip_list = self.__merge_apps_to_app_list(strips, strip_list)
          include_list = self.__merge_apps_to_app_list(include_sublist, include_list)
          shared_list = self.__merge_apps_to_app_list(shared_sublist, shared_list)
          static_list = self.__merge_apps_to_app_list(static_sublist, static_list)

      self.cpp_list = cpp_list
      self.cc_list = cc_list
      self.ar_list = ar_list
      self.ranlib_list = ranlib_list
      self.ld_list = ld_list
      self.strip_list = strip_list
      self.shared_list = shared_list
      self.static_list = static_list
      self.include_list = include_list

    #======================================================================================
    def __parse_arguments(self, params):
      ''' Parses any supplied command line arguments and stores them for later use.
      '''
      parser = argparse.ArgumentParser(description='Tesseract library compiler.')
      # MXE specific arguments
      parser.add_argument('--mxe_path',
                          dest='mxe_path',
                          action='store',
                          help='The path to your MXE installation, required if --use_mxe is set.')
      parser.add_argument('-a', '--exist_action',
                          dest='exist_action',
                          choices=['Skip', 'Overwrite', 'Backup'],
                          action='store',
                          default='Skip',
                          help='Action on existance of working directory')

      # Build specific arguments
      parser.add_argument('-l', '--dest_path',
                          dest='dest_path',
                          action='store',
                          required=False,
                          help='Set the root library path to which the libraries will be stored.\n'
                               'various directories will be built on top of this as required by\n'
                               'the various architectures.')
      parser.add_argument('-w', '--source_path',
                          dest='source_path',
                          action='store',
                          required=False,
                          help='Set the root workspace path to which the source files will be stored.\n'
                               'in various directories which will be built on top of this as required by\n'
                               'the various libraries.')

      # Application specific arguments.
      parser.add_argument('--width',
                          dest='width',
                          action='store',
                          default='1200',
                          help='Set the width of the application, default 1200 pixels')
      parser.add_argument('--height',
                          dest='height',
                          action='store',
                          default='800',
                          help='Set the height of the application, default 800 pixels')
      parser.add_argument('--position',
                          dest='position',
                          choices=['TL', 'C'],
                          action='store',
                          default='C',
                          help='Default position of the application, TL(top left), C(Centre), default centred.')
      args = parser.parse_args()

      if args is not None:

        if args.source_path:
          self.source_path = Path(args.source_path)
          self.source_path_lbl.setText(str(self.source_path))

        if args.dest_path:
          self.dest_path = Path(args.dest_path)
          self.dest_path_lbl.setText(str(self.dest_path))

        if args.exist_action == 'Skip':
          self.exist_action = ExistAction.SKIP
        elif args.exist_action == 'Overwrite':
          self.exist_action = ExistAction.OVERWRITE
        elif args.exist_action == 'Backup':
          self.exist_action = ExistAction.BACKUP

        if args.mxe_path:
          self.mxe_path = Path(args.mxe_path)

        if args.position:
          if args.position == 'TL':
            self.position = FramePosition.TopLeft
          else:
            self.position = FramePosition.Centre
        else:
          self.position = FramePosition.Centre

    #======================================================================================
    def __detect_existing_download(self, libname, download_path):
      if download_path.exists():
        for f in download_path.glob(libname + '*'):
          if f.exists():
            p = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
            m = p.search(f.name)
            version = m.group(1)
            return (f, version, True)

      return (None, '0.0.0', False)
 

    def __detect_library_version(self, version):
      f_version = version.split('.')
      major_version = f_version[0]
      minor_version = f_version[1]
      build_version = f_version[2]
      return major_version, minor_version, build_version



    def __detect_download_version(self, filename):
      lib_re = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
      m = lib_re.search(filename)
      d_version = m.group(1).split('.')
      major_version = d_version[0]
      minor_version = d_version[1]
      build_version = d_version[2]
      return major_version, minor_version, build_version



    def __detect_libraries(self, name, libname, libpath):
      static_libraries = {}
      shared_libraries = {}
      static = []
      shared = []
      libs_found = False
      for path in libpath:
        for f in path.glob(libname + '.so'): # G++ native shared libraries
          shared.append(f)
          libs_found = True
        
        for f in path.glob(libname + '.a'): # G++ static libraries
          static.append(f)
          libs_found = True
        
        for f in path.glob(libname + '.dll'): # MinGW shared library
          shared.append(f)
          libs_found = True
        
        for f in path.glob(libname + '.dll.a'): # MinGW shared library
          shared.append(f)
          libs_found = True
          
      
      
      static_libraries[name] = static
      shared_libraries[name] = shared
      return libs_found, shared_libraries, static_libraries

    def __detect_existing_library(self, name, libname):
      ''' '''
      lib_style = self.current_library_style
      comp_type = self.current_compiler_type
      destpath = []
      libpath = []
      
      if lib_style == LibraryStyle.SHARED:
        destpath.append(self.current_lib_shared)
        libpath.extend(self.shared_list[comp_type])
      elif lib_style == LibraryStyle.STATIC:
        destpath.append(self.current_lib_static)
        libpath.extend(self.static_list[comp_type])
      elif lib_style == LibraryStyle.SHARED_AND_STATIC:
        destpath.append(self.current_lib_shared)
        destpath.append(self.current_lib_static)
        libpath.extend(self.shared_list[comp_type])
        libpath.extend(self.static_list[comp_type])
        
      return (self.__detect_libraries(name, libname, libpath))
    
    
    
    def __download_library_sources(self, name, libname, lib_type, url, download_path):
                
      if 'github' in url or 'gitlab' in url:
        ''''''
        self.repo.create_remote_repo(name, url, self.exist_action)
        
      elif lib_type == LibraryType.FILE :
      #           elif 'https://sourceforge.net/projects/' in url:
      #             ''' 
      #             Sourceforge projects redirect to the actual file so a different
      #             method must be used to get the filename.
      #             '''
        
        # try to detect already downloaded file
        file, version, exists = self.__detect_existing_download(libname, download_path)
        
        if not exists:
          try:
            # urlgrabber follows redirects better
            local_file = urlgrabber.urlopen(url) # use urlgrabber to open the url
            actual_url = local_file.url # detects the actual filename of the redirected url
            values = urlsplit(actual_url) # split the url up into bits
            filepath = Path(values[2].decode('UTF-8')) # part 2 is the file section of the url
            filename = filepath.name # just extract the file name.
            
          except urlgrabber.grabber.URLGrabError as error:
            self.print_message(str(error))       
      
          f_major, f_minor, f_build = self.__detect_library_version(version)
          d_major, d_minor, d_build = self.__detect_download_version(filename)
           
          if (not exists or 
              d_major < f_major or 
              d_minor < f_minor or 
              d_build < f_build):              
           
            self.print_message('Downloading {} at {}'.format(download_path, filename))
            download_file = download_path / filename
            data = local_file.read() # read the file data for later reuse
              
            # save the file.
            with open(str(download_file), 'wb') as f:
              f.write(data)
            local_file.close()
             
            extract_path = self.dest_path / 'library_builder' / name
            extract_path.mkdir(parents=True, exist_ok=True)
             
          else:
            download_file = file
            
          self.print_message('Download of {} complete.'.format(filename))
          self.print_message('Decompressing file {}.'.format(filename))
             
          # decompress it
          compressed_filename = str(download_file)
          if zipfile.is_zipfile(compressed_filename):
            with zipfile.ZipFile(compressed_filename, 'r') as zip_file:
              zip_file.extract_all(str(extract_path))
              
          else:
            try:
              tar = tarfile.open(compressed_filename, 'r:*')
              
#               dirs = []
#               members = tar.getmembers()
#               for member in members:
#                 if member.isdir():
#                   splits = member.name.split('/')
#                   if len(splits) == 1: # only bottom layer directories
#                     dirs.append(member.name)
              tar.extractall(path=str(download_path))
                
                                
            except tarfile.ReadError as error:       
              self.print_message(str(error))       
                    
      
            self.print_message('Decompressing file {} complete.'.format(filename))
            return download_path

    #======================================================================================

