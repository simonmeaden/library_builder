'''
Created on 24 Sep 2019

@author: simonmeaden
'''

import os, argparse
from pathlib import Path, PurePosixPath

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

      self.__build_gui()
      self.__parse_arguments(params)
      self.__locate_mxe()
      self.__locate_compilers()

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
        self.exist_lbl.setText('Repositories will br skipped if it already exists.')
      elif self.exist_action == 'Overwrite':
        self.exist_lbl.setText('Repositories will br overwritten if it already exists.')
      elif self.exist_action == 'Backup':
        self.exist_lbl.setText('Repositories will br backed up to {} if it already exists.'.format(self.path))
      else:
        self.exist_lbl.setText("Repositories will br cloned if they don't exist.")

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
      compiler_types = list(self.compiler_dict)

      if not compiler_types:
        compiler_types.append(CompilerType.NONE)

      for compiler_type in compiler_types:
        self.compilers.addItem(compiler_type.value)
        
    #======================================================================================
    def __set_current_compiler_lbl(self):
      ''' Set the chosen compiler label.
      '''
      self.chosen_compiler_lbl.setText(self.current_compiler_type.name())

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
    def __compiler_selected(self, item):
      ''' Choose a compiler from available compilers.
      '''
      self.current_compiler_type = CompilerType[item.text()]
      self.__set_current_compiler_lbl()
      current_compiler = self.compiler_dict[self.current_compiler_type]
      fnlower = PurePosixPath(current_compiler).name

      if fnlower == 'g++':  # native
        self.use_mxe = True
        self.mxe_type = MXEType.NONE
        self.mxe_style = MXEStyle.NONE
        self.current_compiler_type = CompilerType.GCC_Native
#         TODO - work out clang options.
#       elif fnlower == 'clang++': # native clang
#         all_files['Native CLang'] = fn_path
      elif 'static' in fnlower:
        self.use_mxe = True
        self.mxe_style = MXEStyle.Static
        if fnlower.startswith('x86_64'):
          self.mxe_type = MXEType.x86_64
          self.current_compiler_type = CompilerType.MinGW_64_MXE_Static
        elif fnlower.startswith('i686'):
          self.mxe_type = MXEType.i686
          self.current_compiler_type = CompilerType.MinGW_32_MXE_Static
      elif 'shared' in fnlower:
        self.use_mxe = True
        self.mxe_style = MXEStyle.Shared
        if fnlower.startswith('x86_64'):
          self.mxe_type = MXEType.x86_64
          self.current_compiler_type = CompilerType.MinGW_64_MXE_Shared
        elif fnlower.startswith('i686'):
          self.mxe_type = MXEType.i686
          self.current_compiler_type = CompilerType.MinGW_32_MXE_Static
      elif 'mingw32' in fnlower:
        self.use_mxe = False
        self.mxe_style = MXEStyle.NONE
        if fnlower.startswith('x86_64'):
          self.mxe_type = MXEType.x86_64
          self.current_compiler_type = CompilerType.MinGW_64_Native
        elif fnlower.startswith('i686'):
          self.mxe_type = MXEType.i686
          self.current_compiler_type = CompilerType.MinGW_32_Native

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
    def __build(self):
      ''' build the libraries
      '''
      self.__build_output_directories()
      self.current_compiler = self.compiler_dict[self.current_compiler_type]
      
      self.__build_leptonica()
      self.__build_tesseract()

    #======================================================================================
    def __build_leptonica(self):
      ''''''
      self.__setup_leptonica_build()

    #======================================================================================
    def __setup_leptonica_build(self):
      ''' Set up the location and parameters of a Leptonica build.

      '''
      self.compile_args = ''
      self.compile_args += '-DCOMPILER='
      self.compile_args += self.current_compiler
      self.compile_args += ' '
      
      self.lib_name = 'leptonica'

    #======================================================================================
    def __build_tesseract(self):
      ''''''
      self.__setup_tesseract_build()
      
    #======================================================================================
    def __setup_tesseract_build(self):
      ''' Set up the location and parameters of a Leptonica build.

      '''
      self.compile_args = ''
      self.compile_args += '-DCOMPILER='
      self.compile_args += self.current_compiler
      self.compile_args += ' '
      
      self.lib_name = 'tesseract'

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
        root_path = self.root_path
        libs_path = os.path.join(root_path, 'lib')

        if self.current_compiler_type == CompilerType.GCC_Native:
          inc_path = os.path.join(libs_path, 'unix/include')
          lib_path = os.path.join(libs_path, 'unix/lib')

        elif self.current_compiler_type == CompilerType.GCC_MXE_Native:
          inc_path = os.path.join(libs_path, 'unix/include')
          lib_path = os.path.join(libs_path, 'unix/lib')

        elif self.current_compiler_type == CompilerType.MinGW_32_Native:
          inc_path = os.path.join(libs_path, 'mingw32/include')
          lib_path = os.path.join(libs_path, 'mingw32/lib')

        elif self.current_compiler_type == CompilerType.MinGW_64_Native:
          inc_path = os.path.join(libs_path, 'mingw64/include')
          lib_path = os.path.join(libs_path, 'mingw64/lib')

        elif self.current_compiler_type == CompilerType.MinGW_32_MXE_Shared:
          inc_path = os.path.join(libs_path, 'mingw32.shared/include')
          lib_path = os.path.join(libs_path, 'mingw32.shared/lib')

        elif self.current_compiler_type == CompilerType.MinGW_64_MXE_Shared:
          inc_path = os.path.join(libs_path, 'mingw64.shared/include')
          lib_path = os.path.join(libs_path, 'mingw64.shared/lib')

        elif self.current_compiler_type == CompilerType.MinGW_32_MXE_Static:
          inc_path = os.path.join(libs_path, 'mingw32.static/include')
          lib_path = os.path.join(libs_path, 'mingw32.static/lib')

        elif self.current_compiler_type == CompilerType.MinGW_64_MXE_Static:
          inc_path = os.path.join(libs_path, 'mingw64.static/include')
          lib_path = os.path.join(libs_path, 'mingw64.static/lib')

        Path(inc_path).mkdir(parents=True, exist_ok=True)
        Path(lib_path).mkdir(parents=True, exist_ok=True)
        self.print_message('Include path {} for {} created.'.format(inc_path, self.current_compiler_type.name))
        self.print_message('Library path {} for {} created.'.format(inc_path, self.current_compiler_type.name))

        self.include_path = inc_path
        self.library_path = lib_path

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
      self.compilers.itemDoubleClicked.connect(self.__compiler_selected)
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
      self.print_message("Root path        : {}".format(self.path))
      self.print_message("Tesseract URL    : {}".format(self.tesseract_url))
      self.print_message("Tesseract Branch : {}".format(self.tesseract_branch))
      self.print_message("Tesseract Path   : {}".format(self.tesseract_path))
      self.print_message("Leptonica URL    : {}".format(self.leptonica_url))
      self.print_message("Leptonica Branch : {}".format(self.leptonica_branch))
      self.print_message("Leptonica Path   : {}".format(self.leptonica_path))
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

      if (not self.mxe_path or
            (self.mxe_path and not os.path.exists(self.mxe_path))):
        # if either the --mxe_path was NOT set or it was but the path
        # doesn't exist then start searching in the other directories.
        srchpath = '/opt/mxe'

        # check /opt/mxe path first as this is recommended for system wide location
        if not self.mxe_path:
          if os.path.exists(srchpath):
            self.mxe_path = srchpath
        # if not there search in home directory for 'mxe' directory.
        if not self.mxe_path:
          srchpath = str(Path.home())
          for root, dirs, _ in os.walk(srchpath):
            for directory in dirs:
              dlower = str(directory).lower()
              if dlower == 'mxe':
                self.mxe_path = os.path.join(root, directory)
                break
            if self.mxe_path:
              break

      if self.mxe_path:
        # the file src/mxe-conf.mk should exist in the MXE directory so
        # check that it does. This should indicate a good MXE setup, hopefully.
        check_file = os.path.join(self.mxe_path, 'src/mxe-conf.mk')
        if os.path.exists(check_file) and os.path.isfile(check_file):
          mxe_exists = True
          self.print_message('MXE found at {}'.format(self.mxe_path))

      else:
        # check file was not found so probably a defunct MXE or a different setup.
        self.print_message("MXE not found.")
        self.print_message("Searched in '/opt' and your home directory for MXE")
        self.print_message("Use --mxe_path if you want to use MXE and it is not located in these locations.")

      self.mxe_exists = mxe_exists

    #======================================================================================
    def __locate_compilers(self):
      ''' Locate all gcc type compilers.

      Locates any existing gcc/g++ compilers in the usual Linux paths
      '/usr/bin' and '/usr/local/bin', plus if located in the MXE directory.
      '''
      compiler_list_by_path = {}
      usr_path = '/usr/bin'
      filenames = self.__find_compilers(usr_path)
      if filenames:
        compiler_list_by_path[usr_path] = filenames
      usr_path = '/usr/local/bin'
      filenames = self.__find_compilers(usr_path)
      if filenames:
        compiler_list_by_path[usr_path] = filenames

      if self.mxe_path:
        filenames = self.__find_compilers(self.mxe_path)
        if filenames:
          compiler_list_by_path[self.mxe_path] = filenames

      merged_dict = {}
      for path in compiler_list_by_path:
        compiler_map = compiler_list_by_path[path]
        merged_dict = {**merged_dict, **compiler_map}
        desc_list = list(compiler_map)
        for desc in desc_list:
          filename = compiler_map[desc]
          self.print_message("Compiler : {} called {}".format(desc, filename))
      self.compiler_dict = merged_dict

    #======================================================================================
    def __find_compilers(self, root_path):
      ''' Find any gcc/g++ compilers in the selected path.
      '''
      all_cpp = {}
      all_cc = {}
      all_librarians = {}
      all_ranlib = {}
      for _, _, files in os.walk(root_path):
          for filename in files:
              fnlower = filename.lower()
              fn_path = os.path.join(root_path, filename)
              # cpp
              if fnlower.endswith('g++'):
                if fnlower == 'g++':  # native
                  all_cpp[CompilerType.GCC_Native] = fn_path
                elif 'static' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_cpp[CompilerType.MinGW_64_MXE_Static] = fn_path
                  elif fnlower.startswith('i686'):
                    all_cpp[CompilerType.MinGW_32_MXE_Static] = fn_path
                elif 'shared' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_cpp[CompilerType.MinGW_64_MXE_Shared] = fn_path
                  elif fnlower.startswith('i686'):
                    all_cpp[CompilerType.MinGW_32_MXE_Shared] = fn_path
                elif 'mingw32' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_cpp[CompilerType.MinGW_64_Native] = fn_path
                  elif fnlower.startswith('i686'):
                    all_cpp[CompilerType.MinGW_32_Native] = fn_path
              # C
              if fnlower.endswith('gcc'):
                if fnlower == 'gcc':  # native
                  all_ranlib[CompilerType.GCC_Native] = fn_path
                elif 'static' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_ranlib[CompilerType.MinGW_64_MXE_Static] = fn_path
                  elif fnlower.startswith('i686'):
                    all_ranlib[CompilerType.MinGW_32_MXE_Static] = fn_path
                elif 'shared' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_ranlib[CompilerType.MinGW_64_MXE_Shared] = fn_path
                  elif fnlower.startswith('i686'):
                    all_ranlib[CompilerType.MinGW_32_MXE_Shared] = fn_path
                elif 'mingw32' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_ranlib[CompilerType.MinGW_64_Native] = fn_path
                  elif fnlower.startswith('i686'):
                    all_ranlib[CompilerType.MinGW_32_Native] = fn_path
              # ar
              if fnlower.endswith('ar'):
                if fnlower == 'ar':  # native
                  all_librarians[CompilerType.GCC_Native] = fn_path
                elif 'static' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_librarians[CompilerType.MinGW_64_MXE_Static] = fn_path
                  elif fnlower.startswith('i686'):
                    all_librarians[CompilerType.MinGW_32_MXE_Static] = fn_path
                elif 'shared' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_librarians[CompilerType.MinGW_64_MXE_Shared] = fn_path
                  elif fnlower.startswith('i686'):
                    all_librarians[CompilerType.MinGW_32_MXE_Shared] = fn_path
                elif 'mingw32' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_librarians[CompilerType.MinGW_64_Native] = fn_path
                  elif fnlower.startswith('i686'):
                    all_librarians[CompilerType.MinGW_32_Native] = fn_path              
              # ranlib
              if fnlower.endswith('ranlib'):
                if fnlower == 'ranlib':  # native
                  all_librarians[CompilerType.GCC_Native] = fn_path
                elif 'static' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_librarians[CompilerType.MinGW_64_MXE_Static] = fn_path
                  elif fnlower.startswith('i686'):
                    all_librarians[CompilerType.MinGW_32_MXE_Static] = fn_path
                elif 'shared' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_librarians[CompilerType.MinGW_64_MXE_Shared] = fn_path
                  elif fnlower.startswith('i686'):
                    all_librarians[CompilerType.MinGW_32_MXE_Shared] = fn_path
                elif 'mingw32' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_librarians[CompilerType.MinGW_64_Native] = fn_path
                  elif fnlower.startswith('i686'):
                    all_librarians[CompilerType.MinGW_32_Native] = fn_path
      return (all_cpp, all_cc, all_librarians, all_ranlib) 

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
                          dest='path',
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

        if args.path:
          self.path = args.path
          self.leptonica_path = os.path.join(self.path, 'leptonica')
          self.tesseract_path = os.path.join(self.path, 'tesseract')

        if args.lib_path:
          self.root_path = args.lib_path

        if args.exist_action == 'Skip':
          self.exist_action = ExistAction.Skip
        elif args.exist_action == 'Overwrite':
          self.exist_action = ExistAction.Overwrite
        elif args.exist_action == 'Backup':
          self.exist_action = ExistAction.Backup

        if args.mxe_path:
          self.mxe_path = args.mxe_path

        if args.position:
          if args.position == 'TL':
            self.position = FramePosition.TopLeft
          else:
            self.position = FramePosition.Centre
        else:
          self.position = FramePosition.Centre
    
    #======================================================================================

