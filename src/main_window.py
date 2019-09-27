'''
Created on 24 Sep 2019

@author: simonmeaden
'''

import os, argparse
from pathlib import Path

# from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import (
    Signal,
    Slot
  )
from PySide2.QtGui import (
  QPixmap,
  QIcon
  )
from PySide2.QtWidgets import (
    QMainWindow,
    QFrame,
    QPushButton,
    QLabel,
#     QComboBox,
#     QListWidget,
    QPlainTextEdit,
    QGridLayout,
#     QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDialog
  )


from common_types import ExistAction, CompilerOptions
from repository import Repository
from choose_compiler_dialog import ChooseCompilerDialog
import icons


class TesseractBuildOptions:
  """ A structure to hold options for the build. """
  use_mxe = False;
  mxe_path = ''
  mxe_exists = False
  compiler_flavour = 'Native'
  compiler_list = {}
  leptonica_url = ''
  leptonica_branch = ''
  tesseract_url = ''
  tesseract_branch = ''
  path = ''
  exist_action = 'Stop'



class MainWindow(QMainWindow):
    '''
    classdocs
    '''


    def __init__(self, params, parent=None):
      '''
      Constructor
      '''
      super(MainWindow, self).__init__(parent)
      self.__build_gui()
      
      options = self.parse_arguments(params)
      self.locate_mxe(options)
      self.locate_compilers(options)
      
      self.repo = Repository()
      self.repo.send_message[str].connect(self.print_message)
  
      self.clone_repositories(options)
      
      self.options = options
      self.print_options(options)
      self.set_tesseract_url_lbl(options.tesseract_url)
      self.set_leptonica_url_lbl(options.leptonica_url)
      self.set_exist_action_lbl(options)
      self.set_mxe_lbl(options)
      
    @Slot()
    def help(self):
      """
      """
      
    @Slot(str)
    def print_message(self, message):
      self.msg_edit.appendPlainText(message)
      
      
    def set_exist_action_lbl(self, options):
      if options.exist_action == 'Skip':
        self.exist_lbl.setText('Repositories will br skipped if it already exists.')
      elif options.exist_action == 'Overwrite':
        self.exist_lbl.setText('Repositories will br overwritten if it already exists.')
      elif options.exist_action == 'Backup':
        self.exist_lbl.setText('Repositories will br backed up to {} if it already exists.'.format(options.path))
      else:
        self.exist_lbl.setText("Repositories will br cloned if they don't exist.")
        
        
    def set_tesseract_url_lbl(self, url):
      self.tess_lbl.setText(url)
      
      
    def set_leptonica_url_lbl(self, url):
      self.lep_lbl.setText(url)
      
      
    def set_mxe_lbl(self, options):
      if options.mxe_exists:
        if options.mxe_path:
          if not options.use_mxe:
            self.usemxe_lbl.setText("MXE on {} will be used if an MXE compiler is specified".format(options.mxe_path))
          else:
            self.usemxe_lbl.setText("MXE on {} will be used by {}".format(options.mxe_path, options.compiler_flavour))
        else:
          self.usemxe_lbl.setText("MXE MXE will not be used")
      else:
        self.usemxe_lbl.setText("MXE cannot be found in normal paths,\n"
                                "\u23FA /opt/mxe\n"
                                "\u23FA under users home directory\n"
                                "specify --mxe_path for other locations")
        
    
    def choose_compiler_flavour(self):
      """ Choose a compiler from available compilers.
      """
      dlg = QDialog(self)
      
         
    def __build_gui(self):
      """ initialise the gui.
      """
      
      exit_pix = QPixmap("application-exit.png")
      exit_icon = QIcon(exit_pix)
      help_pix = QPixmap("help-contextual.png")
      help_icon = QIcon(help_pix) 
      
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
      self.lep_lbl = QLabel(self)
      layout_1.addRow("Leptonica URL:", self.lep_lbl)
      self.exist_lbl = QLabel(self)
      layout_1.addRow("Repository Exists Action:",self.exist_lbl)
      self.usemxe_lbl = QLabel(self)
      layout_1.addRow("Use MXE:",self.usemxe_lbl)
      
      
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
      help_btn.clicked.connect(help)
      
      compiler_btn = QPushButton(self)
      compiler_btn.setIcon(exit_icon)
      compiler_btn.setToolTip("Choose Compiler Flavour")
      btn_layout.addWidget(compiler_btn)
      compiler_btn.clicked.connect(self.close)
      
      close_btn = QPushButton(self)
      close_btn.setIcon(exit_icon)
      close_btn.setToolTip("Close the application")
      btn_layout.addWidget(close_btn)
      close_btn.clicked.connect(self.close)
      
      msg_edit = QPlainTextEdit(self)
      layout_2.addWidget(msg_edit)
      self.msg_edit = msg_edit
     
      

    def print_options(self, options):
      """ Prints a list of command line arguments.
      """
      if options is not None:
        self.print_message("Root path        : {}".format(options.path))
        self.print_message("Tesseract URL    : {}".format(options.tesseract_url))
        self.print_message("Tesseract Branch : {}".format(options.tesseract_branch))
        self.print_message("Tesseract Path   : {}".format(options.tesseract_path))
        self.print_message("Leptonica URL    : {}".format(options.leptonica_url))
        self.print_message("Leptonica Branch : {}".format(options.leptonica_branch))
        self.print_message("Leptonica Path   : {}".format(options.leptonica_path))
        self.print_message("Exist action     : {}".format(options.exist_action))
        self.print_message("Supplied MXE path: {}".format(options.mxe_path))

    def locate_mxe(self, options):
      """ Attempt to find the MXE cross compiler libraries.
      
      Searches the suggested paths for the MXE cross compiler system.
      
      Paths searched by default are 'opt/mxe' for a system wide setup or
      under the users home directory. This second option can take a 
      significant time, depending on the size of the home directory so
      this action can be overridden by supplying a path in the --mxe_path
      command line argument.
      
      /param options - the options list
      """
      if options.mxe_path:
        if os.path.exists(options.mxe_path):
          return 
      else:
        srchpath = '/opt/mxe'
        mxe_exists = False
         
        # check /opt path first as this is recommended for sytem wide location
        if not options.mxe_path:
          if os.path.exists(srchpath):
            options.mxe_path = srchpath
        # if not there search in home directory for 'mxe' directory.
        if not options.mxe_path:
          srchpath = str(Path.home())
          for root, dirs, files in os.walk(srchpath):
            for directory in dirs:
              dlower = str(directory).lower()
              if dlower == 'mxe':
                options.mxe_path = os.path.join(root, directory)
                break
            if options.mxe_path:
              break
               
      if options.mxe_path:
        check_file = os.path.join(options.mxe_path, 'src/mxe-conf.mk')
        if os.path.exists(check_file) and os.path.isfile(check_file):
          mxe_exists = True
          self.print_message('MXE found at {}'.format(options.mxe_path))
      else:
        self.print_message("MXE not found.") 
        self.print_message("Searched in '/opt' and your home directory for MXE")
        self.print_message("Use --mxe_path if you want to use MXE and it is not located in these locations.")
      
      options.mxe_exists = mxe_exists

    def locate_compilers(self, options):
      """ Locate all gcc type compilers.
      
      Locates any existing gcc/g++ compilers in the usual Linux paths
      '/usr/bin' and '/usr/local/bin', plus if located in the MXE directory.
      """
      compiler_list_by_path = {}
      usr_path = '/usr/bin'
      filenames =  self.__find_compilers(usr_path)
      compiler_list_by_path[usr_path] = filenames
      usr_path = '/usr/local/bin'
      filenames =  self.__find_compilers(usr_path)
      compiler_list_by_path[usr_path] = filenames
      
      if options.mxe_exists:
        filenames =  self.__find_compilers(os.path.join(options.mxe_path, options.mxe_path))
        compiler_list_by_path[options.mxe_path] = filenames
      
      for path in compiler_list_by_path:
        compiler_map = compiler_list_by_path[path]
        desc_list = list(compiler_map)
        for desc in desc_list:
          filename = compiler_map[desc]
          self.print_message("Compiler : {} called {}".format(desc, filename))
      options.compiler_list = compiler_list_by_path
    
    
    
            
    def __find_compilers(self, root_path):
      """ Find any gcc/g++ compilers in the selected path.
      """
      all_files = {}
      for root, dirs, files in os.walk(root_path):
          for filename in files:
              fnlower = filename.lower()
              fn_path = os.path.join(root_path, filename)
              if fnlower.endswith('g++'):
                if fnlower == 'g++':
                  all_files['Native'] = fn_path
                elif 'static' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_files['MXE MinGW Win64 Shared'] = fn_path
                  elif fnlower.startswith('i686'):
                    all_files['MXE MinGW Win32 Shared'] = fn_path
                elif 'shared' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_files['MXE MinGW Win64 Static'] = fn_path
                  elif fnlower.startswith('i686'):
                    all_files['MXE MinGW Win32 Static'] = fn_path
                elif 'mingw32' in fnlower:
                  if fnlower.startswith('x86_64'):
                    all_files['MinGW Win64'] = fn_path
                  elif fnlower.startswith('i686'):
                    all_files['MinGW Win32'] = fn_path
      return all_files 
    
    def clone_repositories(self, options):
      self.repo.create_remote_repo(options.leptonica_path, options.leptonica_url, options.exist_action)
      self.repo.create_remote_repo(options.tesseract_path, options.tesseract_url, options.exist_action)

    def parse_arguments(self, params):
      """ Parses any supplied command line arguments and stores them for later use.
      """
      parser = argparse.ArgumentParser(description='Tesseract library compiler.')
      parser.add_argument('--mxe_path',
                          dest='mxe_path',
                          action='store',
                          help='The path to your MXE installation, required if --use_mxe is set.')
      parser.add_argument('-lu', '--leptonica_url', 
                          dest='leptonica_url', 
                          action='store',
                          default='https://github.com/DanBloomberg/leptonica.git',
                          help='Set the Leptonica git url, defaults to git clone https://github.com/DanBloomberg/leptonica.git')
#       parser.add_argument('-lb', '--leptonica_branch', 
#                           dest='leptonica_branch', 
#                           action='store',
#                           default='master',
#                           help='Set the Leptonica git branch, defaults to master')
      parser.add_argument('-tu', '--tesseract_url',
                          dest='tesseract_url',
                          action='store',
                          default='https://github.com/tesseract-ocr/tesseract.git',
                          help='Set the Tesseract git url, defaults to https://github.com/tesseract-ocr/tesseract.git')
#       parser.add_argument('-tb', '--tesseract_branch', 
#                           dest='tesseract_branch', 
#                           action='store',
#                           default='master',
#                           help='Set the Tesseract git branch, defaults to master')
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
      args = parser.parse_args()
      
      options = TesseractBuildOptions()
    
      if args is not None:
        options.tesseract_url = args.tesseract_url      
        options.leptonica_url = args.leptonica_url
    #     options.compiler_flavour = args.compiler_flavour
        if args.path:
          options.path = args.path
          options.leptonica_path = os.path.join(options.path, 'leptonica') 
          options.tesseract_path = os.path.join(options.path, 'tesseract') 
        if args.exist_action == 'Skip':
          options.exist_action = ExistAction.Skip
        elif args.exist_action == 'Overwrite':
          options.exist_action = ExistAction.Overwrite
        elif args.exist_action == 'Backup':
          options.exist_action = ExistAction.Backup
         
        if args.mxe_path:
          options.mxe_path = args.mxe_path
    
      return options

