'''
Created on 24 Sep 2019

@author: simonmeaden
'''

import argparse
from pathlib import Path, PurePath, PurePosixPath

# from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import (
    Qt,
    Signal,
    Slot,
    QRect
  )
from PySide2.QtGui import (
  QPixmap,
  QIcon
  )
from PySide2.QtWidgets import (
    QDesktopWidget,
    QMainWindow,
    QFrame,
    QPushButton,
    QLabel,
#     QComboBox,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QGridLayout,
#     QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
#     QDialog
  )

from common_types import (
  ExistAction,
  FramePosition,
  MXEType,
  MXEStyle,
  CompilerType
  )
from repository import Repository
# from choose_compiler_dialog import ChooseCompilerDialog
import icons
from lxml import includes


#======================================================================================
class MainWindow(QMainWindow):
    '''
    classdocs
    '''

    width = 1200
    height = 800

    #======================================================================================
    def __init__(self, params, parent=None):
      '''
      Constructor
      '''
      super(MainWindow, self).__init__(parent)

      self.use_mxe = False
      self.tesseract_branch = ''
      self.leptonica_branch = ''
      self.mxe_path = Path()

      self.__build_gui()
      self.__parse_arguments(params)
      self.__locate_mxe()
      self.__locate_compiler_apps()

      self.repo = Repository()
      self.repo.send_message[str].connect(self.print_message)

      self.__clone_repositories()

      self.__print_options()
      self.__set_tesseract_url_lbl(self.tesseract_url)
      self.__set_leptonica_url_lbl(self.leptonica_url)
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
        self.exist_lbl.setText('Repositories will be backed up to {} if it already exists.'.format(self.root_path))
      else:
        self.exist_lbl.setText("Repositories will be cloned if they don't exist.")

    #======================================================================================
    def __set_tesseract_url_lbl(self, url):
      self.tess_lbl.setText(url)

    #======================================================================================
    def __set_leptonica_url_lbl(self, url):
      self.lep_lbl.setText(url)

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
    def __set_chosen_lep_branch_lbl(self):
      ''' Set the chosen compiler label.
      '''
      self.lep_branch_lbl.setText(self.leptonica_branch)

    #======================================================================================
    def __set_chosen_tess_branch_lbl(self):
      ''' Set the chosen compiler label.
      '''
      self.tess_branch_lbl.setText(self.tesseract_branch)

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
      
      self.__set_current_compiler_lbl(self.current_compiler_type)

    #======================================================================================
    def __tess_branch_selected(self, item):
      ''' Choose a compiler from available compilers.
      '''
      self.tesseract_branch = item.text()
      self.__set_chosen_tess_branch_lbl()
      # TODO checkout selected branch

    #======================================================================================
    def __lep_branch_selected(self, item):
      ''' Choose a compiler from available compilers.
      '''
      self.leptonica_branch = item.text()
      self.__set_chosen_lep_branch_lbl()
      # TODO checkout selected branch

    #======================================================================================
    def __build_tesseract(self):
      ''''''
      self.__setup_tesseract_build()

    def __setup_tesseract_build(self):
      ''' Set up the location and parameters of a Leptonica build.

      '''
      self.compile_args = ''
      self.compile_args += '-DCOMPILER='
      self.compile_args += self.current_cpp
      self.compile_args += ' '

      self.lib_name = 'tesseract'

    def __setup_leptonica_build(self):
      ''' Set up the location and parameters of a Leptonica build.

      '''
      self.compile_args = ''
      self.compile_args += '-DCOMPILER='
      self.compile_args += self.current_cpp
      self.compile_args += ' '

      self.lib_name = 'leptonica'

    def __build_leptonica(self):
      ''''''
      self.__setup_leptonica_build()

    def __build(self):
      ''' build the libraries
      '''
      self.__build_output_directories()
      self.current_cpp = self.cpp_list[self.current_compiler_type]

      self.__build_leptonica()
      self.__build_tesseract()

   #======================================================================================
    def __build_output_directories(self):
      '''Creates necessary paths for the library.

      Creates the paths dependant on the specified compiler and creates
      lib and include directories based on the supplied and required --lib_path.

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
      if self.root_path:
        out_root = PurePath(self.root_path)

        out_lib_path = out_root / "lib"

        if self.current_compiler_type == CompilerType['GCC_Native']:
          inc_path = out_lib_path / 'unix/include'
          lib_path = out_lib_path / 'unix/lib'

        elif self.current_compiler_type == CompilerType['MinGW_32_Native']:
          inc_path = out_lib_path / 'mingw32/include'
          lib_path = out_lib_path / 'mingw32/lib'

        elif self.current_compiler_type == CompilerType['MinGW_64_Native']:
          inc_path = out_lib_path / 'mingw64/include'
          lib_path = out_lib_path / 'mingw64/lib'

        elif self.current_compiler_type == CompilerType['MinGW_32_MXE_Shared']:
          inc_path = out_lib_path / 'mingw32.shared/include'
          lib_path = out_lib_path / 'mingw32.shared/lib'

        elif self.current_compiler_type == CompilerType['MinGW_64_MXE_Shared']:
          inc_path = out_lib_path / 'mingw64.shared/include'
          lib_path = out_lib_path / 'mingw64.shared/lib'

        elif self.current_compiler_type == CompilerType['MinGW_32_MXE_Static']:
          inc_path = out_lib_path / 'mingw32.static/include'
          lib_path = out_lib_path / 'mingw32.static/lib'

        elif self.current_compiler_type == CompilerType['MinGW_64_MXE_Static']:
          inc_path = out_lib_path / 'mingw64.static/include'
          lib_path = out_lib_path / 'mingw64.static/lib'

        # create the actual paths if they don't already exist
        Path(inc_path).mkdir(parents=True, exist_ok=True)
        Path(lib_path).mkdir(parents=True, exist_ok=True)

        # send created message to log
        self.print_message('Include path {} for {} created.'.format(inc_path, self.current_compiler_type.name))
        self.print_message('Library path {} for {} created.'.format(inc_path, self.current_compiler_type.name))

        # save paths to self
        self.current_include_path = inc_path
        self.current_library_path = lib_path

    #======================================================================================
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

      self.tess_lbl = QLabel(self)
      layout_1.addRow("Tesseract URL:", self.tess_lbl)

      self.tess_list = QListWidget(self)
      self.tess_list.itemDoubleClicked.connect(self.__tess_branch_selected)
      layout_1.addRow("Tesseract Branches:", self.tess_list)

      self.tess_branch_lbl = QLabel(self)
      layout_1.addRow("Tesseract Chosen Branch:", self.tess_branch_lbl)

      self.lep_lbl = QLabel(self)
      layout_1.addRow("Leptonica URL:", self.lep_lbl)

      self.lep_list = QListWidget(self)
      self.lep_list.itemDoubleClicked.connect(self.__lep_branch_selected)
      layout_1.addRow("Leptonica Branches:", self.lep_list)

      self.lep_branch_lbl = QLabel(self)
      layout_1.addRow("Leptonica Chosen Branch:", self.lep_branch_lbl)

      self.exist_lbl = QLabel(self)
      layout_1.addRow("Repository Exists Action:", self.exist_lbl)

      self.usemxe_lbl = QLabel(self)
      layout_1.addRow("Use MXE:", self.usemxe_lbl)

      self.compilers = QListWidget(self)
      self.compilers.itemDoubleClicked.connect(self.__select_compiler)
      layout_1.addRow("Available Compilers:", self.compilers)

      self.chosen_compiler_lbl = QLabel(self)
      layout_1.addRow("Chosen Compiler:", self.chosen_compiler_lbl)

      frame_2 = QFrame(self);
      layout_2 = QHBoxLayout()
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
      build_btn.clicked.connect(self.__build)

      close_btn = QPushButton(self)
      close_btn.setIcon(exit_icon)
      close_btn.setToolTip("Close the application")
      btn_layout.addWidget(close_btn)
      close_btn.clicked.connect(self.close)

      msg_edit = QPlainTextEdit(self)
      layout_2.addWidget(msg_edit)
      self.msg_edit = msg_edit

    #======================================================================================
    def __print_options(self):
      ''' Prints a list of command line arguments.
      '''
      self.print_message("Root path        : {}".format(self.root_path.name))
      self.print_message("Tesseract URL    : {}".format(self.tesseract_url))
      if self.tesseract_branch:
        self.print_message("Tesseract Branch : {}".format(self.tesseract_branch))
      self.print_message("Tesseract path   : {}".format(self.tesseract_path))
      self.print_message("Leptonica URL    : {}".format(self.leptonica_url))
      if self.leptonica_branch:
        self.print_message("Leptonica Branch : {}".format(self.leptonica_branch))
      self.print_message("Leptonica path   : {}".format(self.leptonica_path))
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
      if not mxe_path.name: # default value is an empty path
        
        # if either the --mxe_path was NOT set or it was but the path
        # doesn't exist then start searching in the other directories.        
        # check /opt/mxe_path first as this is recommended for system wide location
        srchpath = Path('/opt/mxe') 
        
        if srchpath.exists():
          mxe_path = srchpath # /opt/mxe exists
          
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

      if root_path.name == 'bin':
          bin_path = root_path
      else:
        if root_path == self.mxe_path:
          bin_path = root_path / 'usr' / 'bin'
        else: # probably never happen
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
      
      return (all_cpp, all_cc, all_ar, all_ranlib)

    def __locate_compiler_apps(self):
      ''' Locate all gcc type compilers.

      Locates any existing gcc/g++ compilers in the usual Linux PurePaths
      '/usr/bin' and '/usr/local/bin', plus if located in the MXE directory.
      '''
      cpp_list = {}
      cc_list = {}
      ar_list = {}
      ranlib_list = {}
      include_list = {}
      usr_paths = [Path('/usr/bin'), Path('usr/local/bin'), self.mxe_path]

      for usr_path in usr_paths:
        if usr_path:
          cpps, ccs, ars, ranlibs = self.__find_compiler_apps_in_path(usr_path)
          cpp_list = self.__merge_apps_to_app_list(cpps, cpp_list)
          cc_list = self.__merge_apps_to_app_list(ccs, cc_list)
          ar_list = self.__merge_apps_to_app_list(ars, ar_list)
          ranlib_list = self.__merge_apps_to_app_list(ranlibs, ranlib_list)
          
          # Locate possible include paths
          if usr_path.name == 'bin': # should only be /usr/bin or /usr/local/bin
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
      self.include_list = include_list

    #======================================================================================
    def __clone_repositories(self):
      self.repo.create_remote_repo(self.leptonica_path, self.leptonica_url, self.exist_action)
      lep_branches = self.repo.get_local_branches()
      for branch in lep_branches:
        self.lep_list.addItem(branch)
      if len(lep_branches) == 1:
        self.leptonica_branch = lep_branches[0]
        self.__set_chosen_lep_branch_lbl()

      self.repo.create_remote_repo(self.tesseract_path, self.tesseract_url, self.exist_action)
      tess_branches = self.repo.get_local_branches()
      for branch in tess_branches:
        self.tess_list.addItem(branch)
      if len(tess_branches) == 1:
        self.tesseract_branch = tess_branches[0]
        self.__set_chosen_tess_branch_lbl()

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

      # Leptonica / Tesseract specific arguments
      parser.add_argument('-lu', '--leptonica_url',
                          dest='leptonica_url',
                          action='store',
                          default='https://github.com/DanBloomberg/leptonica.git',
                          help='Set the Leptonica git url, defaults to git clone https://github.com/DanBloomberg/leptonica.git')
      parser.add_argument('-tu', '--tesseract_url',
                          dest='tesseract_url',
                          action='store',
                          default='https://github.com/tesseract-ocr/tesseract.git',
                          help='Set the Tesseract git url, defaults to https://github.com/tesseract-ocr/tesseract.git')
      parser.add_argument('-p', '--repo_path',
                          dest='repo_path',
                          action='store',
                          help='Set the root working path to which GIT stores repository')
      parser.add_argument('-a', '--exist_action',
                          dest='exist_action',
                          choices=['Skip', 'Overwrite', 'Backup'],
                          action='store',
                          default='Skip',
                          help='Action on existance of working directory')

      # Build specific arguments
      parser.add_argument('-l', '--lib_path',
                          dest='lib_path',
                          action='store',
                          required=True,
                          help='Set the root library path to which the libraries will be stored.\n'
                               'various directories will be built on top of this as required by\n'
                               'the various architectures.')

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
        self.tesseract_url = args.tesseract_url
        self.leptonica_url = args.leptonica_url

        if args.repo_path:
          self.repo_path = Path(args.repo_path)
          self.leptonica_path = self.repo_path / 'leptonica'
          self.tesseract_path = self.repo_path / 'tesseract'

        if args.lib_path:
          self.root_path = Path(args.lib_path)

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

