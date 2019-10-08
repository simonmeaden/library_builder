'''
Created on 24 Sep 2019

@author: simonmeaden
'''

import argparse
from pathlib import Path, PurePath
from ruamel.yaml import YAML
from builtins import FileExistsError
from urllib.request import urlsplit
import urlgrabber
import zipfile, gzip, bz2

from PySide2.QtCore import (
    Qt,
#     Signal,
    Slot,
    QRect
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
#     QComboBox,
#     QListView,
#     QAbstractItemView,
    QListWidget,
    QListWidgetItem,
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
#   MXEType,
#   MXEStyle,
  CompilerType,
  Library,
  LibraryType,
  RequiredLibrary,
  selected_role,
  name_role,
  required_libs_role,
  ItemDelegate,
  )
from repository import Repository
from django.core.handlers.exception import response_for_exception



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
      self.build_order = []
      self.source_path = Path()
      self.dest_path = Path()
      self.current_compiler_type = CompilerType['NONE']

      self.__build_gui()
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
          item.setData(selected_role, False)
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
      compiler_types = list(self.cpp_list)

      if not compiler_types:
        compiler_types.append(CompilerType['NONE'])

      for compiler_type in compiler_types:
        self.compilers.addItem(CompilerType(compiler_type.value).name)

    #======================================================================================
    def __set_current_compiler_lbl(self, compiler_type):
      ''' Set the chosen compiler label.
      '''
      self.chosen_compiler_lbl.setText(CompilerType(compiler_type.value).name)

    #======================================================================================
    def __select_compiler(self, item):
      ''' Choose a compiler from available compilers.
      '''
      self.current_compiler_type = CompilerType[item.text()]

      self.current_cpp = self.cpp_list[self.current_compiler_type]
      self.current_cc = self.cc_list[self.current_compiler_type]
      self.current_ar = self.ar_list[self.current_compiler_type]
      self.current_ranlib = self.ranlib_list[self.current_compiler_type]
      self.current_includes = self.include_list[self.current_compiler_type]

      self.print_message('Current g++ compiler           : {}'.format(self.current_cpp))
      self.print_message('Current gcc compiler           : {}'.format(self.current_cc))
      self.print_message('Current ar library creator     : {}'.format(self.current_ar))
      self.print_message('Current ranlib library indexer : {}'.format(self.current_ranlib))
#       self.print_message('Current ld library loader      : {}'.format(self.current_ld))

      self.__set_current_compiler_lbl(self.current_compiler_type)

    def __build_library(self):
      ''' build the libraries
      '''
      if self.current_compiler_type == CompilerType['NONE']:
        QMessageBox.warning(
          self, 
          "Compiler Error", 
          'You have not selected a compiler,\n'
          'Choose a compiler and try again!', 
          QMessageBox.Ok
          )
        return
        
      self.__build_output_directories()
      self.current_cpp = self.cpp_list[self.current_compiler_type]
      self.__get_library_sources()

      
      # TODO

   #======================================================================================
    def __build_output_directories(self):
      '''Creates necessary paths for the library.

      Creates the paths dependant on the specified compiler and creates
      lib and include directories based on the supplied and required --dest_path.

      libpath mingw32         + lib      # Native MinGw32 i686
                              + include
              mingw64         + lib      # Native MinGw32 x86_64
                              +  include
              mingw32.shared  +lib      # Shared MXS MinGw32 i686
                              + include
              mingw64.shared  + lib      # Shared MXS MinGw32 x86_64
                              + include
              mingw32.static  + lib      # Static MXS MinGw32 i686
                              + include
              mingw64.static  + lib      # Static MXS MinGw32 x86_64
                              + include
              unix            + lib      # Native g++ x86_64
                              + include

      '''
      if self.dest_path:
        out_lib_path = PurePath(self.dest_path) / 'lib'

        if self.current_compiler_type == CompilerType['GCC_Native']:
          inc_path = out_lib_path / 'unix/include'
          dest_path = out_lib_path / 'unix/lib'

        elif self.current_compiler_type == CompilerType['MinGW_32_Native']:
          inc_path = out_lib_path / 'mingw32/include'
          dest_path = out_lib_path / 'mingw32/lib'

        elif self.current_compiler_type == CompilerType['MinGW_64_Native']:
          inc_path = out_lib_path / 'mingw64/include'
          dest_path = out_lib_path / 'mingw64/lib'

        elif self.current_compiler_type == CompilerType['MinGW_32_MXE_Shared']:
          inc_path = out_lib_path / 'mingw32.shared/include'
          dest_path = out_lib_path / 'mingw32.shared/lib'

        elif self.current_compiler_type == CompilerType['MinGW_64_MXE_Shared']:
          inc_path = out_lib_path / 'mingw64.shared/include'
          dest_path = out_lib_path / 'mingw64.shared/lib'

        elif self.current_compiler_type == CompilerType['MinGW_32_MXE_Static']:
          inc_path = out_lib_path / 'mingw32.static/include'
          dest_path = out_lib_path / 'mingw32.static/lib'

        elif self.current_compiler_type == CompilerType['MinGW_64_MXE_Static']:
          inc_path = out_lib_path / 'mingw64.static/include'
          dest_path = out_lib_path / 'mingw64.static/lib'

        # create the actual paths if they don't already exist
        Path(inc_path).mkdir(parents=True, exist_ok=True)
        Path(dest_path).mkdir(parents=True, exist_ok=True)

        # send created message to log
        self.print_message('Include path {} for {} created.'.format(inc_path, self.current_compiler_type.name))
        self.print_message('Library path {} for {} created.'.format(inc_path, self.current_compiler_type.name))

        # save paths to self
        self.current_include_path = inc_path
        self.current_library_path = dest_path

    #======================================================================================
    def __library_list_item_clicked(self, item):
      ''' Select a library to build.

      Selects a library, and recurses through it's required libraries,
      marking those that are required to build the requested library
      and creating a build order list to make certain that all required
      libraries are built first.
      '''
      self.build_order_list.clear()
      self.build_order.clear()

      selected = item.data(selected_role)
      required_libs = item.data(required_libs_role)
      name = item.data(name_role)

      self.build_order.append(name)

      selected = not selected

      if selected:
        for req_lib in required_libs:
          for req_item in self.library_list.findItems(req_lib.name, Qt.MatchExactly):  # should only be one
            req_lib_name = req_item.data(name_role)
            if req_item.text() == req_lib_name:
              req_item.setText('{} required by {}'.format(req_lib_name, name))
              req_item.setData(selected_role, True)
            else:
              req_item.setText('{}, {}'.format(req_item.text(), name))
              req_item.setData(selected_role, True)
            self.__recurse_required_libraries(req_item)

      item.setData(selected_role, selected)
      self.build_order_list.clear()
      for b in self.build_order:
        self.build_order_list.addItem(b)

    def __recurse_required_libraries(self, item):
      selected = item.data(selected_role)
      required_libs = item.data(required_libs_role)
      name = item.data(name_role)
      self.build_order.insert(0, name)
      if selected:
        for req_lib in required_libs:
          for req_item in self.library_list.findItems(req_lib.name, Qt.MatchExactly):  # should only be one
            req_lib_name = req_item.data(name_role)
            if req_item.text() == req_lib_name:
              req_item.setText('{} required by {}'.format(req_lib_name, name))
              req_item.setData(selected_role, True)
            else:
              req_item.setText('{}, {}'.format(req_item.text(), name))
              req_item.setData(selected_role, True)
            self.__recurse_required_libraries(req_item)

    def __build_gui(self):
      ''' initialise the gui.
      '''

      exit_icon = QIcon(QPixmap(":/exit"))
      help_icon = QIcon(QPixmap(":/help"))
      build_icon = QIcon(QPixmap(":/build"))

      main_frame = QFrame(self)
      main_layout = QGridLayout()
      main_frame.setLayout(main_layout)
      self.setCentralWidget(main_frame)

      frame_1 = QFrame(self)
      layout_1 = QFormLayout()
      frame_1.setLayout(layout_1)
      main_layout.addWidget(frame_1, 0, 0)

      source_frame = QFrame(self)
      source_frame.setContentsMargins(0, 0, 0, 0)
      source_layout = QGridLayout()
      source_layout.setContentsMargins(0, 0, 0, 0)
      source_layout.setColumnStretch(0, 3)
      source_layout.setColumnStretch(1, 1)
      source_frame.setLayout(source_layout)
      self.source_path_lbl = QLabel(self)
      self.source_path_lbl.setToolTip(
        'The base directory in which the library source files\n'
        'will be built. Library source files will be created in\n'
        'directory trees underneath this directory.')
      source_layout.addWidget(self.source_path_lbl, 0, 0)
      source_btn = QPushButton('Modify', self)
      source_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      source_btn.clicked.connect(self.__source_path_clicked)
      source_layout.addWidget(source_btn, 0, 1)
      layout_1.addRow("Source Path:", source_frame)

      dest_frame = QFrame(self)
      dest_frame.setContentsMargins(0, 0, 0, 0)
      dest_layout = QGridLayout()
      dest_layout.setContentsMargins(0, 0, 0, 0)
      dest_layout.setColumnStretch(0, 3)
      dest_layout.setColumnStretch(1, 1)
      dest_frame.setLayout(dest_layout)
      self.dest_path_lbl = QLabel(self)
      self.dest_path_lbl.setToolTip(
        'The base directory in which the library files will be stored\n'
        'after the build. Library files files will be placed in\n'
        'directory trees underneath this directory, dependant on\n'
        'the build type e.g. "dest_path/unix/lib" and "dest_path/unix/include.')
      dest_layout.addWidget(self.dest_path_lbl, 0, 0)
      dest_btn = QPushButton('Modify', self)
      dest_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      dest_btn.clicked.connect(self.__dest_path_clicked)
      dest_layout.addWidget(dest_btn, 0, 1)
      layout_1.addRow("Destination Path:", dest_frame)

      self.exist_lbl = QLabel(self)
      layout_1.addRow("Repository Exists Action:", self.exist_lbl)

      self.usemxe_lbl = QLabel(self)
      layout_1.addRow("Use MXE:", self.usemxe_lbl)

      self.compilers = QListWidget(self)
      self.compilers.itemClicked.connect(self.__select_compiler)
      layout_1.addRow("Available Compilers:", self.compilers)

      self.chosen_compiler_lbl = QLabel(self)
      layout_1.addRow("Chosen Compiler:", self.chosen_compiler_lbl)

      frame_2 = QFrame(self);
      layout_2 = QGridLayout()
      frame_2.setLayout(layout_2)
      main_layout.addWidget(frame_2, 0, 1)

      btn_frame = QFrame(self)
      btn_layout = QHBoxLayout()
      btn_frame.setLayout(btn_layout)
      main_layout.addWidget(btn_frame, 1, 0, 1, 2)

      help_btn = QPushButton(self)
      help_btn.setIcon(help_icon)
      help_btn.setToolTip("Help")
      btn_layout.addWidget(help_btn)
      help_btn.clicked.connect(self.__help)

      build_btn = QPushButton(self)
      build_btn.setIcon(build_icon)
      build_btn.setToolTip("Build Libraries")
      btn_layout.addWidget(build_btn)
      build_btn.clicked.connect(self.__build_library)

      close_btn = QPushButton(self)
      close_btn.setIcon(exit_icon)
      close_btn.setToolTip("Close the application")
      btn_layout.addWidget(close_btn)
      close_btn.clicked.connect(self.close)

      library_lbl = QLabel("Available Libraries :", self)
      layout_2.addWidget(library_lbl, 0, 0)

      library_list = QListWidget(self)
      item_delegate = ItemDelegate(library_list, self)
      library_list.setItemDelegate(item_delegate)
      library_list.itemClicked.connect(self.__library_list_item_clicked)
      layout_2.addWidget(library_list, 1, 0)
      self.library_list = library_list

      build_order_lbl = QLabel("Build Order :", self)
      layout_2.addWidget(build_order_lbl, 0, 1)

      build_order_list = QListWidget(self)
      self.build_order_list = build_order_list
      layout_2.addWidget(build_order_list, 1, 1)

      msg_edit = QPlainTextEdit(self)
      msg_edit.setFont(QFont("Courier", 10))
      layout_2.addWidget(msg_edit, 2, 0, 1, 2)
      self.msg_edit = msg_edit

      main_layout.setColumnStretch(0, 2)
      main_layout.setColumnStretch(1, 5)

      layout_2.setRowStretch(0, 1)
      layout_2.setRowStretch(1, 4)
      layout_2.setRowStretch(2, 4)

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
    def __find_app_type(self, app_name, filename, all_cc):
      fnlower = filename.name.lower()
      if filename.name.endswith(app_name):
        if fnlower == app_name:  # native
          all_cc[CompilerType['GCC_Native']] = filename
        elif 'static' in fnlower:
          if fnlower.startswith('x86_64'):
            all_cc[CompilerType['MinGW_64_MXE_Static']] = filename
          elif fnlower.startswith('i686'):
            all_cc[CompilerType['MinGW_32_MXE_Static']] = filename
        elif 'shared' in fnlower:
          if fnlower.startswith('x86_64'):
            all_cc[CompilerType['MinGW_64_MXE_Shared']] = filename
          elif fnlower.startswith('i686'):
            all_cc[CompilerType['MinGW_32_MXE_Shared']] = filename
        elif 'mingw32' in fnlower:
          if fnlower.startswith('x86_64'):
            all_cc[CompilerType['MinGW_64_Native']] = filename
          elif fnlower.startswith('i686'):
            all_cc[CompilerType['MinGW_32_Native']] = filename

    def __merge_apps_to_app_list(self, apps, app_list):
      new_list = {}
      if apps:
        for name in apps:
          new_list[name] = apps[name]
      return {**app_list, **new_list}

    def __find_compiler_apps_in_path(self, root_path):
      ''' Find any gcc/g++ compilers in the selected path.
      '''
      all_cpp = {}
      all_cc = {}
      all_ar = {}
      all_ranlib = {}
      all_ld = {}

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
          self.__find_app_type('g++', filename, all_cpp)

      filelist = list(bin_path.glob('*gcc'))
      if filelist:
        for filename in filelist:
          self.__find_app_type('gcc', filename, all_cc)

      filelist = list(bin_path.glob('*ar'))
      if filelist:
        for filename in filelist:
          self.__find_app_type('ar', filename, all_ar)

      filelist = list(bin_path.glob('*ranlib'))
      if filelist:
        for filename in filelist:
          self.__find_app_type('ranlib', filename, all_ranlib)

      filelist = list(bin_path.glob('*ld'))
      if filelist:
        for filename in filelist:
          self.__find_app_type('ld', filename, all_ld)

      return (all_cpp, all_cc, all_ar, all_ranlib, all_ld)

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
      include_list = {}
      usr_paths = [Path('/usr/bin'), Path('usr/local/bin'), self.mxe_path]

      for usr_path in usr_paths:
        if usr_path:
          cpps, ccs, ars, ranlibs, lds = self.__find_compiler_apps_in_path(usr_path)
          cpp_list = self.__merge_apps_to_app_list(cpps, cpp_list)
          cc_list = self.__merge_apps_to_app_list(ccs, cc_list)
          ar_list = self.__merge_apps_to_app_list(ars, ar_list)
          ranlib_list = self.__merge_apps_to_app_list(ranlibs, ranlib_list)
          ld_list = self.__merge_apps_to_app_list(lds, ld_list)

          # Locate possible include paths
          if usr_path.name == 'bin':  # should only be /usr/bin or /usr/local/bin
            parent_path = usr_path.parent
            inc_path = parent_path / 'include'

            # the AND option should match either /usr/bin OR /usr/local/bin NOT both
            if (CompilerType['GCC_Native'] in cpp_list and
                str(usr_path) in str(cpp_list[CompilerType['GCC_Native']])):
              include_list[CompilerType['GCC_Native']] = inc_path

            if (CompilerType['MinGW_32_Native'] in cpp_list and
                str(usr_path) in str(cpp_list[CompilerType['MinGW_32_Native']].parent)):
              include_list[CompilerType['MinGW_32_Native']] = inc_path

            if (CompilerType['MinGW_64_Native'] in cpp_list and
                str(usr_path) in str(cpp_list[CompilerType['MinGW_64_Native']].parent)):
              include_list[CompilerType['MinGW_64_Native']] = inc_path

          elif usr_path == self.mxe_path:
            if CompilerType['MinGW_64_MXE_Static'] in cpp_list:
              inc_path = usr_path / 'usr' / 'x86_64-w64-mingw32.static' / 'include'
              include_list[CompilerType['MinGW_64_MXE_Static']] = inc_path
            if CompilerType['MinGW_32_MXE_Static'] in cpp_list:
              inc_path = usr_path / 'usr' / 'i686-w64-mingw32.static' / 'include'
              include_list[CompilerType['MinGW_32_MXE_Static']] = inc_path
            if CompilerType['MinGW_64_MXE_Shared'] in cpp_list:
              inc_path = usr_path / 'usr' / 'x86_64-w64-mingw32.shared' / 'include'
              include_list[CompilerType['MinGW_64_MXE_Shared']] = inc_path
            if CompilerType['MinGW_64_MXE_Static'] in cpp_list:
              inc_path = usr_path / 'usr' / 'i686-w64-mingw32.shared' / 'include'
              include_list[CompilerType['MinGW_64_MXE_Static']] = inc_path

      self.cpp_list = cpp_list
      self.cc_list = cc_list
      self.ar_list = ar_list
      self.ranlib_list = ranlib_list
      self.ld_list = ld_list
      self.include_list = include_list

    #======================================================================================
    def __get_library_sources(self):
      # TODO change to build order list.
      if self.build_order:
        for lib_name in self.build_order:
          library = self.libraries[lib_name]
          lib_type = library.type
          url = library.url
          name = library.name
          libname = library.libname

          # download to special directory
          download_path = self.dest_path / 'library_builder' / 'downloads'
          download_path.mkdir(parents=True, exist_ok=True)
          
          
          if 'github' in url:
            ''''''
            self.repo.create_remote_repo(name, url, self.exist_action)
            
          elif 'sourceforge' in url:
            '''
            '''
            # try to detect already downloaded file
            version = ''
            if download_path.exists():
              for f in download_path.glob(libname + '*'):
                if f.exists():
                  print(str(f))
            
            try:
              # urlgrabber follows redirects better
              local_file = urlgrabber.urlopen(url) # use urlgrabber to open the url
              data = local_file.read() # read the file data for later reuse
              actual_url = local_file.url # detects the actual filename of the redirected url
              values = urlsplit(actual_url) # split the url up into bits
              filepath = Path(str(values[2])) # part 2 is the file section of the url
              filename = filepath.name # just extract the file name.
              self.print_message('Downloading {} at {}'.format(download_path, filename))
              download_file = download_path / filename
                            
              # save the file.
              with open(str(download_file), 'wb') as f:
                f.write(data)
              local_file.close()
              
              extract_path = self.dest_path / name
              extract_path.mkdir(parents=True, exist_ok=True)
              
              # decompress it
              compressed_filename = str(download_file)
              if zipfile.is_zipfile(compressed_filename):
               with zipfile.ZipFile(compressed_filename, 'r') as zip_file:
                  zip_file.extract_all_(str(extract_path))
              else:
                try:
                  with bz2.open(compressed_filename, 'wb') as f:
                    print(f)
                except Exception as error:
                  print(error)
                  try:
                    with gzip.open(compressed_filename, 'wb') as f:
                      print(f)
                  except Exception as error:
                    print(error)
              
              print("") 
            except urlgrabber.grabber.URLGrabError as error:
              self.print_message(error)              


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
          self.exist_action = ExistAction.Skip
        elif args.exist_action == 'Overwrite':
          self.exist_action = ExistAction.Overwrite
        elif args.exist_action == 'Backup':
          self.exist_action = ExistAction.Backup

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

