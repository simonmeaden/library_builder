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

import os, shutil  # , argparse
import subprocess
from pathlib import Path
from ruamel.yaml import YAML
from builtins import FileExistsError
from collections import OrderedDict, deque
import gettext

from PySide2.QtCore import (
    Qt,
    Signal,
    Slot,
    QRect,
#     QResource,
#     QEvent,
#     QThread,
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
#   QResizeEvent,
  QTextCursor,
  )
from PySide2.QtWidgets import (
#     QDesktopWidget,
    QMainWindow,
    QFrame,
    QPushButton,
    QLabel,
    QComboBox,
    QTabWidget,
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
    QCheckBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
#     QDialog,
#     QStyledItemDelegate,
    QInputDialog,
    QSizePolicy,
    QMessageBox,
    QProgressBar,
#     QDialog,
  )

from common_types import (
  ExistAction,
#   FramePosition,
  LibraryStyle,
  CompilerType,
  CompileStyle,
  Library,
  LibraryType,
  selected_role,
  name_role,
  required_libs_role,
  optional_libs_role,
  optional_role,
  SelectionType,
  LibraryItemDelegate,
  BuildStyle)

from download_classes import FileTransfer
from git_reader import GitReader, GitProgress
from mercurial_reader import ConfigureBuilder
from base_builder import BaseBuilder
from common_types import ExistAction


gb = gettext.translation('main_window', localedir='locales', languages=['en_GB'])
gb.install()
_ = gb.gettext  # English (United Kingdom)
# _ = lambda s: s


#======================================================================================
class MainWindow(QMainWindow, BaseBuilder):
  # # classdocs

  set_git_path = Signal(Path, str, str)  # , ExistAction)
  set_mercurial_path = Signal(Path, str, str)  # , ExistAction)
  
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self, params, parent=None):
    # # Constructor

    super(MainWindow, self).__init__(parent)
    super(BaseBuilder, self).__init__()

    self._x = 0
    self._y = 0
    self._width = 1200
    self._height = 800

    self.working_dir = Path().cwd()
    self.home = Path().home()
    self.config = self.home / '.config' / 'LibraryBuilder'
    self.config.mkdir(parents=True, exist_ok=True)
    self.dest_path = self.working_dir.parent
    self.download_path = self.working_dir.parent / 'downloads'
    self.mxe_path = Path("/opt/mxe")
    self.exist_action = ExistAction.SKIP

    # detect the libraries file
    libraries_file = self.config / "libraries.yaml"
    if not libraries_file.exists():
      src_file = self.working_dir / 'libraries.yaml'
      if src_file.exists():
        shutil.copy(str(src_file), str(libraries_file))

  #       self.data_path = self.home / '.local' / 'share' / 'LibraryBuilder'
  #       self.data_path.mkdir(parents=True, exist_ok=True)

    self.use_mxe = False
    self.compiler_selected = False
    self.libraries_selected = False
    self.prepared = False
    self._config_changed = False
    self.build_optional = True

    self.cpp_list = {}
    self.cc_list = {}
    self.ar_list = {}
    self.ranlib_list = {}
    self.include_list = {}
    self.ld_list = {}
    self.strip_list = {}
    self.shared_list = {}
    self.static_list = {}
  #       self.build_style = {}
    self.build_order = deque()
    self.static_build_order = []
    self.static_copy_order = []
    self.shared_build_order = []
    self.shared_copy_order = []

    self.download_list = []
    self.shared_libraries = {}
    self.static_libraries = {}
    self.download_paths = {}
    
    self.git_repo = None
    self.mercurial_repo = None
    self.file_repo = None

    self.requirements_list = OrderedDict()
    self.optional_list = OrderedDict()

    self.download_count = 0
    self.transfer_deltas = 0
    self.transfer_objects = 0

    self.downloading_str = _('Downloading : {} of {} ({}).\n'
                             'Please wait, there will be a small delay\n'
                             'while we contact the online GIT repository.')

    self.current_compiler_type = CompilerType.NONE
    self.current_library_style = LibraryStyle.SHARED
    self.current_build_style = BuildStyle.CREATE_MISSING
    # current destination paths. These will be set up and created later.
    self.current_include_dest = Path()
    self.current_bin_dest = Path()
    self.current_lib_static_dest = Path()
    self.current_lib_shared_dest = Path()

    self.__load_config_file()

    self.__init_gui()
  #       self.__parse_arguments(params)
    self.source_path_lbl.setText(str(self.dest_path))
    self.dest_path_lbl.setText(str(self.download_path))
    self.mxe_path_lbl.setText(str(self.mxe_path))

    self.load_libraries_file()
    self.load_libraries()

    self.__locate_mxe()
    self.__locate_compiler_apps()
    
    self.log_cursor = None

  #       self.__print_options()
    self.__set_compilers_list()

    frame_geometry = QRect(self._x, self._y, self._width, self._height)

    self.setGeometry(frame_geometry)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def moveEvent(self, event):
    p = event.pos()

    self._x = p.x()
    self._y = p.y()

    self._config_changed = True

    return super(MainWindow, self).moveEvent(event)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def resizeEvent(self, event):
    s = event.size()

    self._width = s.width()
    self._height = s.height()

    self._config_changed = True

    return super(MainWindow, self).resizeEvent(event)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def closeEvent(self, event):

    if self._config_changed:
      self.__save_config_file()
      
    if self.git_repo:
      self.git_repo.stop()
    if self.mercurial_repo:
      self.mercurial_repo.stop()

    return super(MainWindow, self).closeEvent(event)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def eventFilter(self, obj, event):
  #         if event.lib_type() == QEvent.Close and self.window is obj:
  #             self.window.removeEventFilter(self)
  #         elif event.lib_type() == QEvent.Resize and self.window is obj:
  #             print("resize")
  #         return super(MainWindow, self).eventFilter(obj, event)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def load_libraries(self):
    self.library_items = {}
    if self.libraries:
      for name in self.libraries:
        item = QListWidgetItem(name)

        library = self.libraries[name]
        item.setData(selected_role, SelectionType.NONE)
        item.setData(name_role, name)
        item.setData(required_libs_role, library.required_libs)
        item.setData(optional_libs_role, library.optional_libs)
        self.library_list.addItem(item)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __set_default_config_values(self):
    self.dest_path = self.working_dir.parent
    self.download_path = self.working_dir.parent / 'downloads'
    self.mxe_path = Path("/opt/mxe")
    self.exist_action = ExistAction.SKIP
    self._x = 0
    self._y = 0
    self._width = 1200
    self._height = 800

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __load_config_file(self):
    yaml = YAML(typ='safe', pure=True)
    yaml.default_flow_style = False
    yaml_file = self.config / "config.yaml"

    if not yaml_file.exists():
      self.__set_default_config_values()
    else:
      data = yaml.load(yaml_file)

      if data == None:
        self.__set_default_config_values()
      else:
        self.dest_path = Path(data.get("destination", str(Path.home())))
        self.download_path = Path(data.get("downloads", ""))
        self.mxe_path = Path(data.get("mxe", "/opt/mxe"))
        self.__exist_type_changed(data.get("exist-action", 'SKIP'))
        self._x = data.get("x", 0)
        self._y = data.get("y", 0)
        self._width = data.get("width", 1200)
        self._height = data.get("height", 800)
        self.build_optional = data.get("build_optional", True)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __save_config_file(self):
    yaml = YAML(typ='safe', pure=True)
    yaml.default_flow_style = False
    yaml_file = self.config / "config.yaml"

    data = {}
    data["destination"] = str(self.dest_path)
    data["downloads"] = str(self.download_path)
    data["exist-action"] = self.exist_action.name
    data["mxe"] = str(self.mxe_path)
    data["x"] = self._x
    data["y"] = self._y
    data["width"] = self._width
    data["height"] = self._height
    data["build_optional"] = self.build_optional

    yaml.dump(data, yaml_file)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def set_library_tbl_values(self, library):
    row = self.libraries_tbl.rowCount()
    for name in self.libraries:
      library = self.libraries[name]
      self.libraries_tbl.insertRow(row)
      self.libraries_tbl.setItem(row, 0, QTableWidgetItem(library.name))
      self.libraries_tbl.setItem(row, 1, QTableWidgetItem(library.libname))
      self.libraries_tbl.setItem(row, 2, QTableWidgetItem(library.lib_type.name))
      self.libraries_tbl.setItem(row, 3, QTableWidgetItem(library.url))
 
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  @Slot()
  def __help(self):
    """
    """

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  @Slot(str)
  def print_message(self, message):
    self.msg_edit.appendPlainText(message)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  @Slot(str)
  def print_same_line_message(self, message):
    if not self.log_cursor:
      self.log_cursor = self.msg_edit.textCursor()
    else:
      self.msg_edit.setTextCursor(self.log_cursor)
      self.msg_edit.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
    self.msg_edit.appendPlainText(message)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def __set_exist_action_lbl(self):
  #       if self.exist_action == ExistAction.SKIP:
  #         self.exist_lbl.setText('Repositories will be skipped if it already exists.')
  #       elif self.exist_action == ExistAction.OVERWRITE:
  #         self.exist_lbl.setText('Repositories will be overwritten if it already exists.')
  #       elif self.exist_action == ExistAction.BACKUP:
  #         self.exist_lbl.setText('Repositories will be backed up to {} if it already exists.'.format(self.download_path))
  #       else:
  #         self.exist_lbl.setText("Repositories will be cloned if they don't exist.")

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def __set_mxe_lbl(self):
  #       if self.mxe_exists:
  #         if self.mxe_path:
  #           if not self.use_mxe:
  #             self.usemxe_lbl.setText(
  #               "MXE on {} will be used if an MXE compiler is specified".format(self.mxe_path))
  #           else:
  #             self.usemxe_lbl.setText("MXE on {} will be used by {}".format(self.mxe_path, self.compiler_type.name()))
  #         else:
  #           self.usemxe_lbl.setText("MXE MXE will not be used")
  #       else:
  #         self.usemxe_lbl.setText("MXE cannot be found in normal paths,\n"
  #                                 "\u23FA /opt/mxe\n"
  #                                 "\u23FA under users home directory\n"
  #                                 "specify --mxe_path for other locations")

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __set_compilers_list(self):
    if self.cpp_list:
      compiler_types = list(self.cpp_list)
    else:
      compiler_types.append(str(CompilerType.NONE))

    for compiler_type in compiler_types:
      self.compilers.addItem(str(compiler_type))

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __setup_current_compiler(self):
    """ Set the chosen compiler label.
    """
    compiler_type = self.current_compiler_type

    include_paths = self.include_list[compiler_type]
    inc_path = ''
    for path in include_paths:
      p = str(path)
      if len(inc_path) > 0:
        inc_path = p + '\n'
      inc_path = inc_path + p

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_compiler(self, item):
    """ Choose a compiler from available compilers.
    """
    self.current_compiler_type = CompilerType.from_name(item.text())
    comp_type = self.current_compiler_type

    self.current_cpp = self.cpp_list[comp_type]
    self.current_cc = self.cc_list[comp_type]
    self.current_ar = self.ar_list[comp_type]
    self.current_ranlib = self.ranlib_list[comp_type]
    self.current_includes = self.include_list[comp_type]
    self.current_static = self.static_list[comp_type]
    self.current_shared = self.shared_list[comp_type]

    if (comp_type == CompilerType.GCC_NATIVE or
        comp_type == CompilerType.MINGW_32_NATIVE or
        comp_type == CompilerType.MINGW_64_NATIVE):
      self.library_style_box.clear()
      self.library_style_box.addItems([
        _('Shared'),
        _('Static'),
        _('Shared and Static')])
      self.current_library_style = LibraryStyle.SHARED

    elif (comp_type == CompilerType.MINGW_32_MXE_SHARED or
          comp_type == CompilerType.MINGW_64_MXE_SHARED):
      self.library_style_box.clear()
      self.library_style_box.addItems([_('Shared'), ])
      self.current_library_style = LibraryStyle.SHARED

    elif (comp_type == CompilerType.MINGW_32_MXE_STATIC or
          comp_type == CompilerType.MinGW_64_MXE_STATIC):
      self.library_style_box.clear()
      self.library_style_box.addItems([_('Static'), ])
      self.current_library_style = LibraryStyle.STATIC

    if comp_type != CompilerType.NONE:
      self.compiler_selected = True;
    else:
      self.compiler_selected = False

    self.__setup_current_compiler()
    self.__check_prepared()

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __check_compiler_selection(self):
    if self.current_compiler_type == CompilerType.NONE:
      if not self.build_order:
        QMessageBox.warning(
          self,
          _("Compiler Error"),
          _('You have not selected either a compiler,\n'
                  'or a library!\n'
                  'Choose a compiler and one or more libraries and try again!'),
          QMessageBox.Ok
          )
        return False
      else:
        QMessageBox.warning(
          self,
          _("Compiler Error"),
          _('You have not selected a compiler,\n'
                  'Choose a compiler and try again!'),
          QMessageBox.Ok
          )
        return False
    elif not self.build_order:
      QMessageBox.warning(
        self,
        _("Compiler Error"),
        _('You have not selected a library to build,\n'
                'Choose one or more libraries and try again!'),
        QMessageBox.Ok
        )
      return False
    return True

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __update_existing_library_tbl(self, shared_libraries, static_libraries):
    if (self.current_library_style == LibraryStyle.STATIC or
      self.current_library_style == LibraryStyle.SHARED_AND_STATIC):
      for n, paths in static_libraries.items():
        for path in paths:
          row = self.static_library_tbl.rowCount()
          self.static_library_tbl.insertRow(row)
          self.static_library_tbl.setItem(row, 0, QTableWidgetItem(n))
          self.static_library_tbl.setItem(row, 1, QTableWidgetItem(path.name))
          self.static_library_tbl.setItem(row, 2, QTableWidgetItem(str(path.parent)))

    if (self.current_library_style == LibraryStyle.SHARED or
      self.current_library_style == LibraryStyle.SHARED_AND_STATIC):
      for n, paths in shared_libraries.items():
        for path in paths:
          row = self.shared_library_tbl.rowCount()
          self.shared_library_tbl.insertRow(row)
          self.shared_library_tbl.setItem(row, 0, QTableWidgetItem(n))
          self.shared_library_tbl.setItem(row, 1, QTableWidgetItem(path.name))
          self.shared_library_tbl.setItem(row, 2, QTableWidgetItem(str(path.parent)))

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――

  def __prepare_build_order_list(self, static_build_order, shared_build_order):
    self.build_order_list.clear()
    static_builds = []
    shared_builds = []
    for lib in self.build_order:
      if static_build_order:
        if lib in static_build_order:
          static_builds.append(lib)
        else:
          static_builds.append(_('{} is not to be built'.format(lib)))
      if shared_build_order:
        if lib in shared_build_order:
          shared_builds.append(lib)
        else:
          shared_builds.append(_('{} is not to be built'.format(lib)))

    if static_builds:
      self.build_order_list.addItem(_('== Static Libraries =='))
      for lib in static_builds:
        self.build_order_list.addItem(lib)

    if shared_builds:
      self.build_order_list.addItem(_('== Shared Libraries =='))
      for lib in shared_builds:
        self.build_order_list.addItem(lib)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __prepare_static_and_shared_build_order(self):
    static_copy_order = []
    shared_copy_order = []
    static_build_order = []
    shared_build_order = []

    if self.current_build_style == BuildStyle.CREATE_MISSING:
      if self.current_library_style == LibraryStyle.SHARED:
        shared_build_order = self.__remove_existing_from_build(self.shared_libraries)

      elif self.current_library_style == LibraryStyle.STATIC:
        static_build_order = self.__remove_existing_from_build(self.static_libraries)

      elif self.current_library_style == LibraryStyle.SHARED_AND_STATIC:
        static_build_order = self.__remove_existing_from_build(self.static_libraries)
        shared_build_order = self.__remove_existing_from_build(self.shared_libraries)

    elif self.current_build_style == BuildStyle.CREATE_MISSING_AND_COPY:
      if self.current_library_style == LibraryStyle.SHARED:
        shared_build_order = self.__remove_existing_from_build(self.shared_libraries)
        shared_copy_order = self.__transfer_existing_to_copy(self.static_libraries)

      elif self.current_library_style == LibraryStyle.STATIC:
        static_build_order = self.__remove_existing_from_build(self.static_libraries)
        static_copy_order = self.__transfer_existing_to_copy(self.static_libraries)

      elif self.current_library_style == LibraryStyle.SHARED_AND_STATIC:
        static_build_order = self.__remove_existing_from_build(self.static_libraries)
        static_copy_order = self.__transfer_existing_to_copy(self.static_libraries)
        shared_build_order = self.__remove_existing_from_build(self.shared_libraries)
        shared_copy_order = self.__transfer_existing_to_copy(self.static_libraries)

    elif self.current_build_style == BuildStyle.CREATE_ALL:
      if self.current_library_style == LibraryStyle.SHARED:
        shared_build_order = self.__remove_existing_from_build(self.shared_libraries)
        shared_copy_order = self.__transfer_existing_to_copy(self.static_libraries)

      elif self.current_library_style == LibraryStyle.STATIC:
        static_build_order = self.__remove_existing_from_build(self.static_libraries)
        static_copy_order = self.__transfer_existing_to_copy(self.static_libraries)

      elif self.current_library_style == LibraryStyle.SHARED_AND_STATIC:
        static_build_order = self.build_order
        shared_build_order = self.build_order

    return static_build_order, shared_build_order, static_copy_order, shared_copy_order

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __prepare_libraries_for_build(self):
    """
    """
    if not self.__check_compiler_selection():
      return

    if self.build_order:
      self.shared_library_tbl.setRowCount(0)
      self.static_library_tbl.setRowCount(0)

      for lib_name in self.build_order:
        library = self.libraries[lib_name]
  #           lib_type = library.lib_type
  #           url = library.url
        name = library.name
        libname = library.libname

        self.print_message(_('Preparing {}').format(libname))

        # download to special directory
        download_path = self.download_path
        download_path.mkdir(parents=True, exist_ok=True)

        exists, shared_libraries, static_libraries = self.__detect_existing_library(name, libname)

        if exists:
          self.shared_libraries = {**self.shared_libraries, **shared_libraries}
          self.static_libraries = {**self.static_libraries, **static_libraries}
          self.__update_existing_library_tbl(shared_libraries, static_libraries)

    if self.prepared:
      self.download_btn.setEnabled(True)

    static_build_order, shared_build_order, static_copy_order, shared_copy_order = \
        self.__prepare_static_and_shared_build_order()
    self.__prepare_build_order_list(static_build_order, shared_build_order)

    self.static_build_order = static_build_order
    self.static_copy_order = static_copy_order
    self.shared_build_order = shared_build_order
    self.shared_copy_order = shared_copy_order

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __remove_existing_from_build(self, libraries):
    build_order = []
    for library in self.build_order:
      if library not in libraries:
        build_order.append(library)
    return build_order

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __transfer_existing_to_copy(self, libraries):
    copy_order = []
    for library in self.build_order:
      if library in libraries:
        copy_order.append(library)
    return copy_order

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __download_required_library_sources(self, download_path):
    required_libs = set(self.static_build_order + self.shared_build_order)
    self.download_list = required_libs
#     self.__set_downloading_lbl(0, '')
    lib_count = 0

    for lib_name in required_libs:
      lib_count += 1
#       self.__set_downloading_lbl(lib_count, lib_name)

      library = self.libraries[lib_name]
      lib_type = library.lib_type
      url = library.url
      name = library.name
      libname = library.libname
      self.__download_library_sources(name, libname, lib_type, url, download_path)
      
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __download_library_sources(self, name, libname, lib_type, url, download_path):

    if lib_type == LibraryType.GIT:  # 'github' in url or 'gitlab' in url:
      """"""
      # Create git thread only once
      # set up git progress tracking
      if not self.git_repo:
        remote = GitProgress()
        remote.send_start_delta[int].connect(self.__receive_deltas_start)
        remote.send_start_objects[int].connect(self.__receive_objects_start)
        remote.send_update_delta[int].connect(self.__receive_transfer_deltas)
        remote.send_update_objects[int].connect(self.__receive_transfer_objects)
  
        # set up git repository with error and result tracking.
        self.git_repo = GitReader(remote, self.exist_action)
        self.git_repo.send_message[str].connect(self.print_message)
        self.git_repo.send_repo_path[str, str].connect(self.__receive_repo_path)
        self.set_git_path[Path, str, str].connect(self.git_repo.set_clone_paths)
        self.git_repo.finished.connect(self.git_repo.deleteLater)
        self.git_repo.start()
  
      self.git_repo.set_git_path.emit(download_path, name, url)
  
    elif lib_type == LibraryType.MERCURIAL:
      if not self.mercurial_repo:
        self.mercurial_repo = ConfigureBuilder(self.exist_action)
        self.mercurial_repo.send_message[str].connect(self.print_message)
        self.mercurial_repo.send_same_line_message[str].connect(self.print_same_line_message)
        self.mercurial_repo.send_repo_path[str, str].connect(self.__receive_repo_path)
        self.set_mercurial_path[Path, str, str].connect(self.mercurial_repo.set_clone_paths)
        self.mercurial_repo.finished.connect(self.mercurial_repo.deleteLater)
        self.mercurial_repo.start()
          
      self.set_mercurial_path.emit(download_path, name, url)

    elif lib_type == LibraryType.FILE or lib_type == LibraryType.FTP:

      if not self.file_repo:
        self.file_repo = FileTransfer()
        self.file_repo.send_message[str].connect(self.print_message)
        self.file_repo.send_repo_path[str, str].connect(self.__receive_repo_path)
        self.file_repo.start()

      self.file_repo.set_clone_paths(name, libname, url, download_path)
  #         self.download_paths.append((name, download_path, url, self.exist_action))
  #         extract_path = self.__download_file(name, libname, url, download_path)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_compile_type(self, library):
    """ detect exactly which types of build each library has. """
    style = CompileStyle.NONE
    if library in self.download_paths:
      path = self.download_paths[library]
      configure = path / 'configure' # This is normally the starting point of the make
      if configure.exists() and configure.is_file():
        style = CompileStyle.CONFIGURE
      else:
        # autotools creates the configure file
        # requires autotools. Normally done by developers and creates the configure file
        autogen = path / 'autogen.sh'
        if autogen.exists() and autogen.is_file():
          style = CompileStyle.AUTOGEN
        else:
          # alternatively cmake can be used to create the configure file
          cmake = path / 'CMakeLists.txt'
          if cmake.exists() and cmake.is_file():
            style = CompileStyle.CMAKE

    return style

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __download_libraries(self):
    """ download the required libraries. """
    download_path = self.download_path
    download_path.mkdir(parents=True, exist_ok=True)
    self.__download_required_library_sources(download_path)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __build_libraries(self):
    """ build the required libraries, making any required output paths. """
    self.__create_output_directories()

    for library in self.static_build_order:
      self.__build_static_library(library)

    for library in self.static_copy_order:
      self.__copy_static_library(library)

    for library in self.shared_build_order:
      self.__build_shared_library(library)

    for library in self.shared_copy_order:
      self.__copy_shared_library(library)

    self.download_paths.clear()

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __build_static_library(self, library):
    """"""
    style = self.__detect_compile_type(library)

    if style == CompileStyle.CONFIGURE:
      self.__configure(library)

    # TODO non-configure libraries

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __copy_static_library(self, library):
    """"""
    # TODO copy static libraries to destination

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __build_shared_library(self, library):
    """"""
    style = self.__detect_compile_type(library)

    if style == CompileStyle.CONFIGURE:
      self.__configure(library)
    # TODO non-configure libraries

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __copy_shared_library(self, library):
    """"""
    # TODO copy shared libraries to destination

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __configure(self, library):
    """ """
    path = self.download_paths[library]
    parent_path = path.parent
    os.chdir(parent_path)
    config_type = self.current_compiler_type

    configure_args = []
    if config_type == CompilerType.GCC_NATIVE:
      configure_args.append('./configure')

    elif config_type == CompilerType.MINGW_32_NATIVE:
      """"""
      configure_args.append('./configure')
      configure_args.append('--host={}'.format('i686-w64-mingw32'))
      dest_path = self.download_path
      configure_args.append('--prefix={}'.format(dest_path))
      configure_args.append('-I{}'.format(self.include_list[CompilerType.MINGW_32_NATIVE]))
      configure_args.append('-L{}'.format(self.library_list[CompilerType.MINGW_32_NATIVE]))

    elif config_type == CompilerType.MINGW_64_NATIVE:
      """"""
      configure_args.append('./configure')
      configure_args.append('--host={}'.format('x86_64-w64-mingw32'))
      dest_path = self.download_path
      configure_args.append('--prefix={}'.format(dest_path))
      configure_args.append('-I{}'.format(self.include_list[CompilerType.MINGW_64_NATIVE]))
      configure_args.append('-L{}'.format(self.library_list[CompilerType.MINGW_64_NATIVE]))

    elif config_type == CompilerType.MINGW_32_MXE_SHARED:
      """"""
      configure_args.append('./configure')
      configure_args.append('--host={}'.format('i686-w64-mingw32'))
      dest_path = self.download_path
      configure_args.append('--prefix={}'.format(dest_path))
      configure_args.append('-I{}'.format(self.include_list[CompilerType.MINGW_32_MXE_SHARED]))
      configure_args.append('-L{}'.format(self.library_list[CompilerType.MINGW_32_MXE_SHARED]))

    elif config_type == CompilerType.MINGW_32_MXE_STATIC:
      """"""
      configure_args.append('./configure')
      configure_args.append('--host={}'.format('i686-w64-mingw32'))
      dest_path = self.download_path
      configure_args.append('--prefix={}'.format(dest_path))
      configure_args.append('-I{}'.format(self.include_list[CompilerType.MINGW_32_MXE_STATIC]))
      configure_args.append('-L{}'.format(self.library_list[CompilerType.MINGW_32_MXE_STATIC]))

    elif config_type == CompilerType.MinGW_64_MXE_STATIC:
      """"""
      configure_args.append('./configure')
      configure_args.append('--host={}'.format('x86_64-w64-mingw32'))
      dest_path = self.download_path
      configure_args.append('--prefix={}'.format(dest_path))
      configure_args.append('-I{}'.format(self.include_list[CompilerType.MinGW_64_MXE_STATIC]))
      configure_args.append('-L{}'.format(self.library_list[CompilerType.MinGW_64_MXE_STATIC]))

    elif config_type == CompilerType.MINGW_64_MXE_SHARED:
      """"""
      configure_args.append('./configure')
      configure_args.append('--host={}'.format('x86_64-w64-mingw32'))
      dest_path = self.download_path
      configure_args.append('--prefix={}'.format(dest_path))
      configure_args.append('-I{}'.format(self.include_list[CompilerType.MINGW_64_MXE_SHARED]))
      configure_args.append('-L{}'.format(self.library_list[CompilerType.MINGW_64_MXE_SHARED]))

    os.chdir(path)
    self.print_message(_('Changed working directory to {}').format(os.getcwd()))

    process = subprocess.run(configure_args,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             universal_newlines=True)
    
    while True:
      out = process.stdout.readline()
      if out == '' and process.poll() is not None:
        self.print_message('Configure completed with returncode {}'.format(process.returncode))
        break
      if out:
        self.print_message(out.strip())

#     process = subprocess.run(['make'])

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __create_output_directories(self):
    """Creates necessary paths for the library.

    Creates the paths dependant on the specified compiler, whether
    static or shared libraries are chosen, and creates
    lib and include directories based on the supplied and required --download_path.

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
    the associated current_lib_static_dest or current_lib_shared_dest will hanve a
    Path value, the other will have None.
    """
    inc_path = Path()
    bin_path = Path()
    dest_static = Path()
    dest_shared = Path()

    if self.dest_path:
      out_lib_path = Path(self.dest_path) / 'lib'

      if self.current_compiler_type == CompilerType.GCC_NATIVE:
        inc_path = out_lib_path / 'unix/include'
        bin_path = out_lib_path / 'unix/bin'
        dest_static = out_lib_path / 'unix.static/lib'
        dest_shared = out_lib_path / 'unix.shared/lib'

      elif self.current_compiler_type == CompilerType.MINGW_32_NATIVE:
        inc_path = out_lib_path / 'mingw32/include'
        bin_path = out_lib_path / 'mingw32/bin'
        dest_static = out_lib_path / 'mingw32.static/lib'
        dest_shared = out_lib_path / 'mingw32.shared/lib'

      elif self.current_compiler_type == CompilerType.MINGW_64_NATIVE:
        inc_path = out_lib_path / 'mingw64/include'
        bin_path = out_lib_path / 'mingw64/bin'
        dest_static = out_lib_path / 'mingw64.static/lib'
        dest_shared = out_lib_path / 'mingw64.shared/lib'

      elif self.current_compiler_type == CompilerType.MINGW_32_MXE_SHARED:
        inc_path = out_lib_path / 'mxe.mingw32.shared/include'
        bin_path = out_lib_path / 'mxe.mingw32.shared/bin'
        dest_static = None
        dest_shared = out_lib_path / 'mxe.mingw32.shared/lib'

      elif self.current_compiler_type == CompilerType.MINGW_64_MXE_SHARED:
        inc_path = out_lib_path / 'mxe.mingw64.shared/include'
        bin_path = out_lib_path / 'mxe.mingw64.shared/bin'
        dest_static = None
        dest_shared = out_lib_path / 'mxe.mingw64.shared/lib'

      elif self.current_compiler_type == CompilerType.MINGW_32_MXE_STATIC:
        inc_path = out_lib_path / 'mxe.mingw32.static/include'
        bin_path = out_lib_path / 'mxe.mingw32.static/bin'
        dest_static = out_lib_path / 'mxe.mingw32.static/lib'
        dest_shared = None

      elif self.current_compiler_type == CompilerType.MinGW_64_MXE_STATIC:
        inc_path = out_lib_path / 'mxe.mingw64.static/include'
        bin_path = out_lib_path / 'mxe.mingw64.static/bin'
        dest_static = out_lib_path / 'mxe.mingw64.static/lib'
        dest_shared = None

      # create the actual paths if they don't already exist
      inc_path.mkdir(parents=True, exist_ok=True)
      bin_path.mkdir(parents=True, exist_ok=True)
      if dest_shared:
        dest_shared.mkdir(parents=True, exist_ok=True)
      if dest_static:
        dest_static.mkdir(parents=True, exist_ok=True)

      # send created message to log
      self.print_message(_('Include path {} for {} created.').format(inc_path, self.current_compiler_type.name))
      self.print_message(_('Binaries path {} for {} created.').format(bin_path, self.current_compiler_type.name))
      self.print_message(_('Static Library path {} for {} created.').format(dest_static, self.current_compiler_type.name))
      self.print_message(_('Shared Library path {} for {} created.').format(dest_shared, self.current_compiler_type.name))

      # save paths to self
      self.current_include_dest = inc_path
      self.current_bin_dest = bin_path
      self.current_lib_static_dest = dest_static
      self.current_lib_shared_dest = dest_shared

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __check_prepared(self):
    self.prepared = (self.compiler_selected and self.libraries_selected)
    if (self.prepared):
      self.prepare_btn.setEnabled(True)

    else:
      self.prepare_btn.setEnabled(False)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_libraries(self, item):
    """ Select a library to build.

    Selects a library, and recurses through its required libraries,
    marking those that are required to build the requested library
    and creating a build order list to make certain that all required
    libraries are built first. If a library is removed then all required
    libraries are also removed unless required by a different selection.

    Also defines a build order for the libraries, required libraries first.
    """
    # recover extra data from library list item
    primary_selection_type = item.data(selected_role)
    required_libs = item.data(required_libs_role)
    optional_libs = item.data(optional_libs_role)
    primary_lib_name = item.data(name_role)

    # create simple list of required or required + optional libraries
    if self.build_optional:
      primary_build_set = set({**required_libs, **optional_libs})
    else:
      primary_build_set = set(required_libs)

    # change selection lib_type appropriately
    if primary_selection_type == SelectionType.SELECTED:
      # primary and optional can be deselected.
      primary_selection_type = SelectionType.NONE
      item.setToolTip(_('Library not selected'))
    elif primary_selection_type == SelectionType.NONE:
      # toggle the selection lib_type to/from SELECTED
      primary_selection_type = SelectionType.SELECTED
      item.setToolTip(_('Library was selected by user'))
    elif primary_selection_type == SelectionType.REQUIRED:
      # required libraries cannot be deselected.
      QMessageBox.warning(self,
                          _('Deletion Warning'),
                          _('You are attempting to remove {},\n'
                            'which is a required library.\n'
                            'This is not allowed.').format(primary_lib_name),
                          QMessageBox.Ok)
      return
    item.setData(selected_role, primary_selection_type)

    if primary_lib_name not in self.requirements_list:
      self.requirements_list[primary_lib_name] = []

    if primary_lib_name not in self.build_order:
      self.build_order.append(primary_lib_name)

    if primary_selection_type == SelectionType.SELECTED:
      # primary library - now add required and (possibly) optional libraries.
      primary_item = self.__add_primary_library_to_tree(primary_lib_name)

      for required_lib_name in primary_build_set:

        # create a primary item fro trhe requirements display
        item = self.__add_library_requirements_to_tree(primary_item, required_lib_name)
        item.setData(0, name_role, required_lib_name)
        item.setData(0, selected_role, SelectionType.REQUIRED)

        # add to final required library list
        if primary_lib_name in list(self.requirements_list):
          # just add the required library
          if required_lib_name not in self.requirements_list.get(primary_lib_name, []):
            self.requirements_list[primary_lib_name].append(required_lib_name)
        else:
          # first time add primary and required library to the requirements display
          self.requirements_list[primary_lib_name] = [required_lib_name, ]

        if required_lib_name in optional_libs:
          item.setData(0, optional_role, True)
          item.setToolTip(0, _('Library was added as an optional library'))
        else:
          item.setData(0, optional_role, False)
          item.setToolTip(0, _('Library was added as a required library'))

        self.__recurse_required_libraries(item)

    else:
      # remove non-required libraries
      if primary_lib_name in list(self.requirements_list):
        requirements = self.requirements_list.pop(primary_lib_name)
        # First set all required libraries to not required.
        for lib_name in requirements:
          for required_item in self.library_list.findItems(lib_name, Qt.MatchExactly):
            required_item.setData(selected_role, SelectionType.NONE)
      # Unfortunately they may be required by some other library.
      # so possible reset them
      for key, requirements in  self.requirements_list.items():
        for lib_name in requirements:
          for required_item in self.library_list.findItems(lib_name, Qt.MatchExactly):
            self.print_message(_('{} optional library has been added for {}.'.format(key, primary_lib_name)))
            required_item.setData(selected_role, SelectionType.REQUIRED)

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

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __add_primary_library_to_tree(self, name):
    """ Adds primary libraries to the library tree """
    item = QTreeWidgetItem();
    item.setData(0, name_role, name)
    item.setData(0, selected_role, SelectionType.SELECTED)
    item.setToolTip(0, _('Primary Library'))
    item.setText(0, name);
    self.requirements_tree.addTopLevelItem(item)
    return item

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __add_library_requirements_to_tree(self, parent_item, name):
    """ Adds required libraries to the library tree. """
    item = QTreeWidgetItem()
    item.setText(0, name)
    item.setData(0, name_role, name)
    item.setData(0, selected_role, SelectionType.REQUIRED)
    item.setToolTip(0, _('Required Library'))
    parent_item.addChild(item)
    return item

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __recurse_required_libraries(self, item):
    lib_name = item.data(0, name_role)
    # actually should only be one with each name
    required_libs = {}
    optional_libs = {}
    for required_item in self.library_list.findItems(lib_name, Qt.MatchExactly):
      required_libs = required_item.data(required_libs_role)
      optional_libs = required_item.data(optional_libs_role)
      primary_lib_name = required_item.data(name_role)
      
    # this will make the required lib earlier in the build queue
    if primary_lib_name in self.build_order:
      self.build_order.remove(primary_lib_name)
    self.build_order.appendleft(primary_lib_name)

    # if no required or optional libraries quit recursing
    if not (required_libs or optional_libs):
      return

    # create simple list of required or required + optional libraries
    if self.build_optional:
      build_set = set({**required_libs, **optional_libs})
    else:
      build_set = set(required_libs)

    for required_lib_name in build_set:
      required_item = self.__add_library_requirements_to_tree(item, required_lib_name)

      # add required library to the requirements list
      if primary_lib_name in list(self.requirements_list):
        if required_lib_name not in self.requirements_list.get(primary_lib_name, []):
          self.requirements_list[primary_lib_name].append(required_lib_name)
      else:
        self.requirements_list[primary_lib_name] = [required_lib_name, ]

        if required_lib_name in optional_libs:
          required_item.setData(0, optional_role, True)
          required_item.setToolTip(0, _('Library was selected as an optional library'))
        else:
          required_item.setData(0, optional_role, False)
          required_item.setToolTip(0, _('Library was selected as a required library'))

      self.__recurse_required_libraries(required_item)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __clear_libraries(self):
    """ Clears all library selections.
    """
    self.build_order_list.clear()
    self.requirements_tree.clear()
    self.build_order.clear()
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
    prepare_btn.setText("Prepare Build")
    prepare_btn.setEnabled(False)
    prepare_btn.setToolTip(
      _("Prepare the system for a build.\n"
              "This checks available libraries and sets up the system\n"
              "with all the information it will require to build any of\n"
              "the supported libraries.")
      )
    btn_layout.addWidget(prepare_btn)
    prepare_btn.clicked.connect(self.__prepare_libraries_for_build)
    self.prepare_btn = prepare_btn

    download_btn = QPushButton(self)
    download_btn.setIcon(build_icon)
    download_btn.setText(_("Download Libraries"))
    download_btn.setEnabled(False)
    btn_layout.addWidget(download_btn)
    download_btn.clicked.connect(self.__download_libraries)
    self.download_btn = download_btn

    build_btn = QPushButton(self)
    build_btn.setIcon(build_icon)
    build_btn.setText(_("Build Libraries"))
    build_btn.setEnabled(False)
    btn_layout.addWidget(build_btn)
    build_btn.clicked.connect(self.__build_libraries)
    self.build_btn = build_btn

    close_btn = QPushButton(self)
    close_btn.setIcon(exit_icon)
    close_btn.setToolTip(_("Close the application"))
    btn_layout.addWidget(close_btn)
    close_btn.clicked.connect(self.close)

    return btn_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_mxe_frame(self):
    mxe_frame = QFrame(self)
    mxe_frame.setContentsMargins(0, 0, 0, 0)
    mxe_layout = QGridLayout()
    mxe_layout.setContentsMargins(0, 0, 0, 0)
    mxe_layout.setColumnStretch(0, 3)
    mxe_layout.setColumnStretch(1, 1)
    mxe_layout.setColumnStretch(2, 1)
    mxe_frame.setLayout(mxe_layout)

    self.mxe_path_lbl = QLabel(self)
    self.mxe_path_lbl.setToolTip(
      _(
        'The base directory in which the MXE library files exist.\n'
        'This only applies when building Windows applications.')
      )
    mxe_layout.addWidget(self.mxe_path_lbl, 0, 0)

    source_btn = QPushButton(_('Modify'), self)
    source_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    source_btn.clicked.connect(self.__select_mxe_path)
    mxe_layout.addWidget(source_btn, 0, 1)

    clear_btn = QPushButton(_('Clear'), self)
    clear_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    clear_btn.clicked.connect(self.__mxe_path_cleared)
    mxe_layout.addWidget(clear_btn, 0, 2)

    return mxe_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_exist_frame(self):
    exist_frame = QFrame(self)
    exist_frame.setContentsMargins(0, 0, 0, 0)
    exist_layout = QGridLayout()
    exist_layout.setContentsMargins(0, 0, 0, 0)
    exist_layout.setColumnStretch(0, 3)
    exist_layout.setColumnStretch(1, 1)
    exist_frame.setLayout(exist_layout)

    exist_lbl = QLabel(self)
    exist_lbl.setText(_('Choose Exist Action'))
    exist_lbl.setToolTip(
      _(
        'Choose the action to take if the downloaded files already exist.\n'
        'There are three options:\n'
        'Skip, which skips the download,\n'
        'Overwrite, which overwrites the existing download and\n'
        'Backup which renames the existing directory and creates a\n;'
        'new copy.')
      )
    exist_layout.addWidget(exist_lbl, 0, 0)

    values = [_('Skip Download'),
              _('Overwrite Existing download'),
              _('Backup Existing download')]
    self.exist_box = QComboBox(self)
    self.exist_box.setToolTip(
      _(
        'Choose the action to take if the downloaded files already exist.\n'
        'There are three options:\n'
        'Skip, which skips the download,\n'
        'Overwrite, which overwrites the existing download and\n'
        'Backup which renames the existing directory and creates a\n;'
        'new copy.')
      )
    self.exist_box.addItems(values)
    self.exist_box.currentTextChanged.connect(self.__exist_type_changed)
    exist_layout.addWidget(self.exist_box, 0, 1)

    return exist_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_source_frame(self):
    source_frame = QFrame(self)
    source_frame.setContentsMargins(0, 0, 0, 0)
    source_layout = QGridLayout()
    source_layout.setContentsMargins(0, 0, 0, 0)
    source_layout.setColumnStretch(0, 3)
    source_layout.setColumnStretch(1, 1)
    source_frame.setLayout(source_layout)

    self.source_path_lbl = QLabel(self)
    self.source_path_lbl.setToolTip(
      _(
        'The base directory in which the library source files\n'
        'will be built. Library source files will be created in\n'
        'subdirectories of this directory.')
      )
    source_layout.addWidget(self.source_path_lbl, 0, 0)

    source_btn = QPushButton(_('Modify'), self)
    source_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    source_btn.clicked.connect(self.__select_source_path)
    source_layout.addWidget(source_btn, 0, 1)

    return source_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_destination_frame(self):
    dest_frame = QFrame(self)
    dest_frame.setContentsMargins(0, 0, 0, 0)
    dest_layout = QGridLayout()
    dest_layout.setContentsMargins(0, 0, 0, 0)
    dest_layout.setColumnStretch(0, 3)
    dest_layout.setColumnStretch(1, 1)
    dest_frame.setLayout(dest_layout)

    self.dest_path_lbl = QLabel(self)
    self.dest_path_lbl.setToolTip(
      _(
        'The base directory in which the compiled library files will be\n'
        'stored after the build. Library files files will be placed in\n'
        'directory trees underneath this directory, dependant on\n'
        'compiler, library and build  types.')
      )
    dest_layout.addWidget(self.dest_path_lbl, 0, 0)

    dest_btn = QPushButton(_('Modify'), self)
    dest_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    dest_btn.clicked.connect(self.__select_dest_path)
    dest_layout.addWidget(dest_btn, 0, 1)
    return dest_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_compiler_frame(self):
    frame_0 = QFrame(self)
    layout_0 = QGridLayout()
    frame_0.setLayout(layout_0)

    frame_1 = QFrame(self)
    layout_1 = QFormLayout()
    frame_1.setLayout(layout_1)

    self.compilers = QListWidget(self)
    self.compilers.setToolTip(
        _(
          'You will need to select a compiler from this list. These are\n'
          'the compilers that have been located in your computer and may\n'
          'include native compilers for compiling for your machine, local\n'
          'MinGW cross compilers for Windows, MXE cross compilers if you\n'
          'have installed MXE on your machine or a cross compiler for one\n'
          'of the many architectures available via the GNU compiler collection.\n'
          'At present the Microsoft MSVC under Wine is not supported.'
        )
      )
    self.compilers.itemClicked.connect(self.__select_compiler)
    layout_1.addRow(_("Available Compilers:"), self.compilers)

    self.library_style_box = QComboBox(self)
    self.library_style_box.addItems([_('Shared'),
                                     _('Static'),
                                     _('Shared and Static')])
    self.library_style_box.setToolTip(
      _(
        "Select a library style, either shared, static or both.\n"
        "This defines whether shared (*.so, *.dll.a), static (*.a)\n"
        "or both will be built. The MinGW style for library naming\n"
        "is used for shared Windows libraries so *.dll.a is used\n"
        "rather than *.dll. The actual library is the same, it's\n"
        "just a different naming convention.")
      )
    self.library_style_box.currentTextChanged.connect(self.__select_library_style)
    layout_1.addRow("Library Style's:", self.library_style_box)

    self.build_style_box = QComboBox(self)
    self.build_style_box.setToolTip(
      _(
        "Select a build style. This will define what libraries are\n"
        "build and where exactly libraries are stored. The options are\n"
        "'Build Required', this will only build those libraries, either\n"
        "shared or static that do not already exist for the compiler that\n"
        "that you have selected.\n"
        "'Build Required and Copy Existing' which will again build those\n"
        "libraries that do not exist for that compiler but will also copy\n"
        "any existing libraries into the destination library tree. This allows\n"
        "you to keep all the libraries in one place.\n"
        "'Build All' which ignores any prebuilt libraries and builds all of\n"
      "them from the source files.")
      )
    self.build_style_box.addItems([_('Build Required'),
                                   _('Build Required and Copy Existing'),
                                   _('Build All')])
    self.build_style_box.currentTextChanged.connect(self.__select_build_style)
    layout_1.addRow(_("Build Style:"), self.build_style_box)

    layout_0.addWidget(frame_1, 0, 0)

    lbl_1 = QLabel(self)
    lbl_1.setText(_("Shared Library Paths:"))
    layout_0.addWidget(lbl_1, 1, 0)

    headers = [_('Library'), _('Name'), _('Path')]
    self.shared_library_tbl = QTableWidget(self)
    self.shared_library_tbl.setToolTip(
      _(
        "This contains a list of all shared libraries from your build list that\n"
        "have been located for you selected compiler."
      )
      )
    self.shared_library_tbl.setColumnCount(3)
    self.shared_library_tbl.setSelectionMode(QAbstractItemView.NoSelection)
    self.shared_library_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
    self.shared_library_tbl.horizontalHeader().setStretchLastSection(True)
    self.shared_library_tbl.setHorizontalHeaderLabels(headers);
    layout_0.addWidget(self.shared_library_tbl, 2, 0)

    lbl_2 = QLabel(self)
    lbl_2.setText(_("Static Library Paths:"))
    layout_0.addWidget(lbl_2, 3, 0)

    self.static_library_tbl = QTableWidget(self)
    self.static_library_tbl.setToolTip(
      _(
        "This contains a list of all static libraries from your build list that\n"
        "have been located for you selected compiler."
        )
      )
    self.static_library_tbl.setColumnCount(3)
    self.static_library_tbl.setSelectionMode(QAbstractItemView.NoSelection)
    self.static_library_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
    self.static_library_tbl.horizontalHeader().setStretchLastSection(True)
    self.static_library_tbl.setHorizontalHeaderLabels(headers);
    layout_0.addWidget(self.static_library_tbl, 4, 0)

    return frame_0

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_library_style(self, text):
    """ """
    if text == _('Shared'):
      self.current_library_style = LibraryStyle.SHARED
    elif text == _('Static'):
      self.current_library_style = LibraryStyle.STATIC
    elif text == _('Shared and Static'):
      self.current_library_style = LibraryStyle.SHARED_AND_STATIC

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_build_style(self, text):
    """ """
    if text == _('Build Required'):
      self.current_build_style = BuildStyle.CREATE_MISSING
    elif text == _('Build Required and Copy Existing'):
      self.current_build_style = BuildStyle.CREATE_MISSING_AND_COPY
    elif text == _('Build All'):
      self.current_build_style = BuildStyle.CREATE_ALL

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_libraries_frame(self):
    libraries_frame = QFrame(self)
    libraries_frame.setContentsMargins(0, 0, 0, 0)
    lib_layout = QGridLayout()
    libraries_frame.setLayout(lib_layout)

    # ==== TOP ROW ====
    library_lbl = QLabel(_("Available Libraries :"), self)
    library_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    lib_layout.addWidget(library_lbl, 0, 0)

    library_list = QListWidget(self)
    library_list.setToolTip(
      _(
        "Select those libraries that you want to build from this list. Any\n"
        "library that is required by another selected library will be\n"
        "automatically selected for you as a requirement. For example if\n"
        "you select Tesseract, it will automatically select 'Leptonica' as\n"
        "a requirement, however this requires other libraries so they will\n"
        "also be auto selected for you so just select the top libraries that\n"
        "you require.")
        )
#     library_list.setItemDelegate(LibraryItemDelegate(library_list, self))
    library_list.setItemDelegate(LibraryItemDelegate())
    library_list.itemClicked.connect(self.__select_libraries)
    lib_layout.addWidget(library_list, 1, 0)
    lib_layout.setContentsMargins(0, 0, 0, 0)
    self.library_list = library_list

    requirements_lbl = QLabel("Requirements :", self)
    requirements_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    lib_layout.addWidget(requirements_lbl, 0, 1)
    requirements_tree = QTreeWidget(self)
    requirements_tree.setToolTip(
      _(
        "You cannot make a selection from this list, it merely shows\n"
        "a list of primary libraries that you selected with their\n"
        "associated requirement libraries")
      )
    requirements_tree.setColumnCount(1)
    headers = [_('Library')]
    requirements_tree.setHeaderLabels(headers);
    requirements_tree.setItemDelegate(LibraryItemDelegate())
    lib_layout.addWidget(requirements_tree, 1, 1, 2, 1)
    self.requirements_tree = requirements_tree

    clear_btn = QPushButton(_('Clear Libraries'), self)
    clear_btn.setToolTip(
      _("This will clear all selected libraries to allow you to start afresh."))
    clear_btn.clicked.connect(self.__clear_libraries)
    lib_layout.addWidget(clear_btn, 2, 0)

    build_order_lbl = QLabel(_("Build Order :"), self)
    build_order_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    lib_layout.addWidget(build_order_lbl, 0, 2)

    build_order_list = QListWidget(self)
    build_order_list.setToolTip(
      _(
        "You cannot make a selection from this list, it shows\n"
        "the order in which the libraries will be built. Requirements\n"
        "first, selected libraries later.")
      )
    self.build_order_list = build_order_list
    lib_layout.addWidget(build_order_list, 1, 2, 2, 1)

    # ==== SECOND ROW ====
#     git_frame = QFrame(self)
#     git_frame.setContentsMargins(0, 0, 0, 0)
#     git_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#     git_layout = QGridLayout()
#     git_frame.setLayout(git_layout)
#     lib_layout.addWidget(git_frame, 3, 0, 1, 3)
    
    self.download_edit = QPlainTextEdit(self)
    lib_layout.addWidget(self.download_edit, 3, 0, 1, 3)
  
#     self.git_downloading_lbl = QLabel(self)
#     self.git_downloading_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
#     self.git_downloading_lbl.setText(self.downloading_str.format(0, 0, ''))
#     git_layout.addWidget(self.git_downloading_lbl, 0, 0, 1, 3)
# 
#     git_lbl1 = QLabel(self)
#     git_lbl1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
#     git_lbl1.setText(_('Git Objects :'))
#     git_layout.addWidget(git_lbl1, 1, 0)
# 
#     self.git_obj_progress = QProgressBar(self)
#     self.git_obj_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#     self.git_obj_progress.setMinimum(0)
#     self.git_obj_progress.setMaximum(100)
#     git_layout.addWidget(self.git_obj_progress, 1, 1)
# 
#     git_lbl2 = QLabel(self)
#     git_lbl2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
#     git_lbl2.setText(_('Git Deltas :'))
#     git_layout.addWidget(git_lbl2, 1, 2)
# 
#     self.git_del_progress = QProgressBar(self)
#     self.git_del_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#     self.git_del_progress.setMinimum(0)
#     self.git_del_progress.setMaximum(100)
#     git_layout.addWidget(self.git_del_progress, 1, 3)

    # ==== THIRD ROW ===
    msg_edit = QPlainTextEdit(self)
    msg_edit.setToolTip(
      _(
        "This shows a list of debug messages and is really only of interest\n"
        "to me as the programmer of this application. I'll probably remove\n"
        "if I ever get a production version of it running.")
      )
    msg_edit.setFont(QFont("Courier", 10))
    lib_layout.addWidget(msg_edit, 4, 0, 1, 3)
    self.msg_edit = msg_edit

    lib_layout.setRowStretch(0, 1)
    lib_layout.setRowStretch(1, 4)
    lib_layout.setRowStretch(3, 4)
    lib_layout.setColumnStretch(0, 1)
    lib_layout.setColumnStretch(1, 2)
    lib_layout.setColumnStretch(2, 1)

    return libraries_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
#   def __set_downloading_lbl(self, value, name):
#     self.git_downloading_lbl.setText(self.downloading_str.format(value, self.download_list, name))

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_main_frame(self):
    """"""
    main_frame = QFrame(self)
    layout = QGridLayout()
    main_frame.setLayout(layout)
    """
    Compiler frame. Holds data like
    list of available compilers, displays library and include
    paths etc.
    """
    compiler_frame = self.__init_compiler_frame()
    layout.addWidget(compiler_frame, 0, 0)

    """
    Libraries frame. Holds the list of available libraries and allows
    the user to select the libraries that they want to install.
    Required libraries will be selecte automatically
    """
    libraries_frame = self.__init_libraries_frame()
    layout.addWidget(libraries_frame, 0, 1)

    return main_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――

  def __init_config_frame(self):
    """
    Configuration frame. Holds data like source/destination paths etc.
    """
    config_frame = QFrame(self)
    config_layout = QHBoxLayout()
    config_frame.setLayout(config_layout)

    """ Left side """
    config_frame1 = QFrame(self)
    layout1 = QFormLayout()
    config_frame1.setLayout(layout1)
    config_layout.addWidget(config_frame1)

    layout1.addRow(_("Source Path:"), self.__init_source_frame())
    layout1.addRow(_("Destination Path:"), self.__init_destination_frame())
    layout1.addRow(_("MXE Path:"), self.__init_mxe_frame())
    layout1.addRow(_("Exist Action:"), self.__init_exist_frame())

    build_optional_box = QCheckBox(self)
    build_optional_box.setChecked(self.build_optional)
    build_optional_box.stateChanged.connect(self.__build_optional_changed)
    layout1.addRow(_("Build Optional libraries"), build_optional_box)

    """ Right side """
    config_frame2 = QFrame(self)
    layout2 = QGridLayout()
    config_frame2.setLayout(layout2)
    config_layout.addWidget(config_frame2)

    libraries_lbl1 = QLabel(self)
    libraries_lbl1.setText(_('Supported Libraries'))
    layout2.addWidget(libraries_lbl1, 0, 0)

    headers = [_('Name'), _('Library Name'), _(' URL'), _(' Type')]
    self.libraries_tbl = QTableWidget(self)
    self.libraries_tbl.setHorizontalHeaderLabels(headers)
    self.libraries_tbl.horizontalHeader().setStretchLastSection(True)
    self.libraries_tbl.verticalHeader().hide()
    self.libraries_tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
    self.libraries_tbl.setColumnCount(4)
    self.libraries_tbl.doubleClicked.connect(self.__select_library_edit)
    self.libraries_tbl.setToolTip(
      _('')
      )
    layout2.addWidget(self.libraries_tbl, 1, 0)

    config_layout.setStretch(0, 1)
    config_layout.setStretch(1, 1)

    return config_frame

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __build_optional_changed(self, state):
    """"""
    if state == Qt.Checked:
      self.build_optional = True
    else:
      self.build_optional = False

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_library_edit(self, item):
    """ select a library to edit from the config available libraries list """

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init_gui(self):
    """ initialise the gui.
    """
    
    main_frame = QFrame(self)
    layout = QGridLayout()
    main_frame.setLayout(layout)
    self.setCentralWidget(main_frame)

    tabs = QTabWidget(self)
    tabs.addTab(self.__init_main_frame(), _('Builder'))
    tabs.addTab(self.__init_config_frame(), _('Configuration'))
    layout.addWidget(tabs, 0, 0)
 
    """ main buttons, help, quit etc. """
    btn_frame = self.__init_btn_frame()
    layout.addWidget(btn_frame, 1, 0)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __check_path_permission(self, path):

    try:
      path.mkdir(parents=True)
    except FileExistsError:
      self.print_message(_("Path exists"))

    filepath = path / 'test_file_permission'
    try:
      open(filepath, 'w')
    except IOError:
      self.print_message(_('You do not have permission to write to {}').format(str(self.dest_path)))
      self.print_message(
        _(
          'Either change this directory to one that you do have\n'
          'permission for or Library Builder will ask you for\n'
          'your sudo password later.')
        )

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_source_path(self):
    """"""
    input_text, ok = QInputDialog.getText(self,
                                     _('Change Source Path'),
                                     _('Enter new source path'),
                                     QLineEdit.EchoMode.Normal,
                                     str(self.dest_path))
    if ok:
      self.dest_path = Path(input_text)
      self.__check_path_permission(self.dest_path)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_dest_path(self):
    """"""
    input_text, ok = QInputDialog.getText(self,
                                     _('Change Destination Path'),
                                     _('Enter new destination path'),
                                     QLineEdit.EchoMode.Normal,
                                     str(self.download_path))
    if ok:
      self.dest_path = Path(input_text)
      self.__check_path_permission(self.download_path)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __select_mxe_path(self):
    """"""
    input_text, ok = QInputDialog.getText(self,
                                     _('Change MXE Path'),
                                     _('Enter new MXE path'),
                                     QLineEdit.EchoMode.Normal,
                                     str(self.mxe_path))
    if ok:
      self.mxe_path = Path(input_text)
  #         self.__check_path_permission(self.mxe_path)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __exist_type_changed(self, text):
    """"""
    if text == 'SKIP':
      self.exist_action = ExistAction.SKIP
    elif text == 'OVERWRITE':
      self.exist_action = ExistAction.OVERWRITE
    elif text == 'BACKUP':
      self.exist_action = ExistAction.BACKUP

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __mxe_path_cleared(self):
    """"""
    btn = QMessageBox.warning(self,
                              _('Clearing MXE Path'),
                              _('Click OK to clear, Cancel to carry on.'),
                              QMessageBox.Ok | QMessageBox.Cancel,
                              QMessageBox.Cancel)
    if btn == QMessageBox.Ok:
      self.mxe_path = ''
      self.mxe_path_lbl.clear()

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __print_options(self):
    """ Prints a list of command line arguments.
    """
    self.print_message(_("Library source downloads : {}").format(self.download_path.name))
    self.print_message(_("Library destination : {}").format(self.dest_path.name))
    self.print_message(_("Exist action     : {}").format(str(self.exist_action)))
    self.print_message(_("Supplied MXE path: {}").format(self.mxe_path))

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __locate_mxe(self):
    """ Attempt to find the MXE cross compiler libraries.

    Searches the suggested paths for the MXE cross compiler system.

    Paths searched by default are 'opt/mxe' for a system wide setup or
    under the users home directory. This second option can take a
    significant time, depending on the size of the home directory so
    this action can be overridden by supplying a path in the --mxe_path
    command line argument.

    """

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
        self.print_message(_('MXE found at {}').format(self.mxe_path))

    else:
      # check file was not found so probably a defunct MXE or a different setup.
      self.print_message(_("MXE not found."))
      self.print_message(_("Searched in '/opt' and your home directory for MXE"))
      self.print_message(_("Use --mxe_path if you want to use MXE and it is not located in these locations."))

    self.mxe_path = mxe_path
    self.mxe_exists = mxe_exists

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
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

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __merge_apps_to_app_list(self, apps, app_list):
    new_list = {}
    if apps:
      for name in apps:
        new_list[name] = apps[name]
    return {**app_list, **new_list}

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_compiler_apps_in_path(self, root_path):
    """ Find any gcc/g++ compilers in the selected path.
    """
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
          """ Others??? """

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

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __locate_compiler_apps(self):
    """ Locate all gcc lib_type compilers.

    Locates any existing gcc/g++ compilers in the usual Linux PurePaths
    '/usr/bin' and '/usr/local/bin', plus if located in the MXE directory.
    """
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

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def __parse_arguments(self, params):
  #       """ Parses any supplied command line arguments and stores them for later use.
  #       """
  #       parser = argparse.ArgumentParser(description='Tesseract library compiler.')
    # MXE specific arguments
  #       parser.add_argument('--mxe_path',
  #                           dest='mxe_path',
  #                           action='store',
  #                           help='The path to your MXE installation, required if --use_mxe is set.')
  #       parser.add_argument('-a', '--exist_action',
  #                           dest='exist_action',
  #                           choices=['Skip', 'Overwrite', 'Backup'],
  #                           action='store',
  #                           default='Skip',
  #                           help='Action on existance of working directory')

    # Build specific arguments
  #       parser.add_argument('-l', '--download_path',
  #                           dest='download_path',
  #                           action='store',
  #                           required=False,
  #                           help='Set the root library path to which the libraries will be stored.\n'
  #                                'various directories will be built on top of this as required by\n'
  #                                'the various architectures.')
  #       parser.add_argument('-w', '--dest_path',
  #                           dest='dest_path',
  #                           action='store',
  #                           required=False,
  #                           help='Set the root workspace path to which the source files will be stored.\n'
  #                                'in various directories which will be built on top of this as required by\n'
  #                                'the various libraries.')

    # Application specific arguments.
  #       parser.add_argument('--width',
  #                           dest='width',
  #                           action='store',
  #                           default='1200',
  #                           help='Set the width of the application, default 1200 pixels')
  #       parser.add_argument('--height',
  #                           dest='height',
  #                           action='store',
  #                           default='800',
  #                           help='Set the height of the application, default 800 pixels')
  #       parser.add_argument('--position',
  #                           dest='position',
  #                           choices=['TL', 'C'],
  #                           action='store',
  #                           default='C',
  #                           help='Default position of the application, TL(top left), C(Centre), default centred.')
  #       args = parser.parse_args()
  #
  #       if args is not None:

  #         if args.dest_path:
  #           self.dest_path = Path(args.dest_path)
  #           self.source_path_lbl.setText(str(self.dest_path))
  #
  #         if args.download_path:
  #           self.download_path = Path(args.download_path)
  #           self.dest_path_lbl.setText(str(self.download_path))

  #         if args.exist_action == 'Skip':
  #           self.exist_action = ExistAction.SKIP
  #         elif args.exist_action == 'Overwrite':
  #           self.exist_action = ExistAction.OVERWRITE
  #         elif args.exist_action == 'Backup':
  #           self.exist_action = ExistAction.BACKUP

  #         if args.mxe_path:
  #           self.mxe_path = Path(args.mxe_path)

  #         if args.position:
  #           if args.position == 'TL':
  #             self.position = FramePosition.TopLeft
  #           else:
  #             self.position = FramePosition.Centre
  #         else:
  #           self.position = FramePosition.Centre

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def __detect_existing_download(self, libname, download_path):
  #       if download_path.exists():
  #         for f in download_path.glob(libname + '*'):
  #           if f.exists():
  #             p = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
  #             m = p.search(f.name)
  #             version = m.group(1)
  #             return (version, True)
  #
  #       return ('0.0.0', False)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def __detect_library_version(self, version):
  #       f_version = version.split('.')
  #       major_version = f_version[0]
  #       minor_version = f_version[1]
  #       build_version = f_version[2]
  #       return major_version, minor_version, build_version

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def __detect_download_version(self, filename):
  #       lib_re = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
  #       m = lib_re.search(filename)
  #       d_version = m.group(1).split('.')
  #       major_version = d_version[0]
  #       minor_version = d_version[1]
  #       build_version = d_version[2]
  #       return major_version, minor_version, build_version

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_libraries(self, name, libname, libpath):
    static_libraries = {}
    shared_libraries = {}
    static = []
    shared = []
    libs_found = False
    for path in libpath:
      for f in path.glob(libname + '*.so'):  # G++ native shared libraries
        if f not in shared:
          shared.append(f)
          libs_found = True

      for f in path.glob(libname + '*.a'):  # G++ static libraries
        if f not in static:
          static.append(f)
          libs_found = True

      for f in path.glob(libname + '*.dll'):  # MinGW shared library
        if f not in shared:
          shared.append(f)
          libs_found = True

      for f in path.glob(libname + '*.dll.a'):  # MinGW shared library
        if f not in shared:
          shared.append(f)
          libs_found = True

    static_libraries[name] = static
    shared_libraries[name] = shared
    return libs_found, shared_libraries, static_libraries

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_existing_library(self, name, libname):
    """ """
    lib_style = self.current_library_style
    comp_type = self.current_compiler_type
    destpath = []
    libpath = []

    if lib_style == LibraryStyle.SHARED:
      destpath.append(self.current_lib_shared_dest)
      libpath.extend(self.shared_list[comp_type])
    elif lib_style == LibraryStyle.STATIC:
      destpath.append(self.current_lib_static_dest)
      libpath.extend(self.static_list[comp_type])
    elif lib_style == LibraryStyle.SHARED_AND_STATIC:
      destpath.append(self.current_lib_shared_dest)
      destpath.append(self.current_lib_static_dest)
      libpath.extend(self.shared_list[comp_type])
      libpath.extend(self.static_list[comp_type])

    return (self.__detect_libraries(name, libname, libpath))

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  #     def __download_compressed_file(self, name, libname, url, download_path):
  #       (# try to detect already downloaded file
  #         file, version, exists) = self.__detect_existing_download(libname, download_path)
  #       if not exists:
  #         try:
  #           local_file = urlgrabber.urlopen(url)  # use urlgrabber to open the url
  #           actual_url = local_file.url  # detects the actual filename of the redirected url
  #           values = urlsplit(actual_url)  # split the url up into bits
  #           filepath = Path(values[2].decode('UTF-8'))  # part 2 is the file section of the url
  #           filename = filepath.name  # just extract the file name.
  #
  #         # urlgrabber follows redirects better
  #         except urlgrabber.grabber.URLGrabError as error:
  #           self.print_message(str(error))
  #
  #         (f_major, f_minor, f_build) = self.__detect_library_version(version)
  #         (d_major, d_minor, d_build) = self.__detect_download_version(filename)
  #         if (not exists or d_major < f_major or d_minor < f_minor or
  #           d_build < f_build):
  #           self.print_message(_('Downloading {} at {}').format(download_path, filename))
  #           download_file = download_path / filename
  #           data = local_file.read()  # read the file data for later reuse
  #           # save the file.
  #           with open(str(download_file), 'wb') as f:
  #             f.write(data)
  #           local_file.close()
  #           extract_path = self.download_path / name
  #           extract_path.mkdir(parents=True, exist_ok=True)
  #         else:
  #           download_file = file
  #
  #         self.print_message(_('Download of {} complete.').format(filename))
  #         self.print_message(_('Decompressing file {}.').format(filename))
  #         # decompress it
  #         compressed_filename = str(download_file)
  #         if zipfile.is_zipfile(compressed_filename):
  #           with zipfile.ZipFile(compressed_filename, 'r') as zip_file:
  #             zip_file.extract_all(str(extract_path))
  #             return extract_path
  #
  #         else:
  #           try:
  #             tar_archive = tarfile.open(compressed_filename, 'r:*')
  #             tar_archive.extractall(path=str(download_path))
  #             root_dir = os.path.commonprefix(tar_archive.getnames())
  #             return Path(root_dir)
  #
  #           except tarfile.ReadError as error:
  #             self.print_message(str(error))
  #
  #           self.print_message(_('Decompressing file {} complete.').format(filename))

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __receive_objects_start(self, objects):
    ''' Git download tracking - Total number of Git objects '''
    if objects > 0.0 and self.transfer_objects == 0:
      self.transfer_objects = objects
      self.git_obj_progress.setValue(0)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __receive_transfer_objects(self, objects):
    ''' Git download tracking - Total number of transferred objects '''
    if self.transfer_objects > 0.0:
      transfered_objects = (objects / self.transfer_objects) * 100
      self.git_obj_progress.setValue(transfered_objects)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __receive_deltas_start(self, deltas):
    ''' Git download tracking - Total number of Git deltas '''
    if deltas > 0.0 and self.transfer_deltas == 0:
      self.transfer_deltas = deltas
      self.git_del_progress.setValue(0)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __receive_transfer_deltas(self, deltas):
    ''' Git download tracking - Total number of transferred deltas '''
    if self.transfer_deltas > 0.0:
      transfered_deltas = (deltas / self.transfer_deltas) * 100
      self.git_del_progress.setValue(transfered_deltas)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __receive_repo_path(self, name, path):
    self.download_paths[name] = Path(path)
    self.download_edit.appendPlainText(_('Download of {} complete').format(name))
    if name in self.download_list:
      self.download_list.remove(name)
    if not self.download_list:
      self.build_btn.setEnabled(True)
    else:
      self.build_btn.setEnabled(False)
    
    if not self.download_list:
      self.build_btn.setEnabled(True)
  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
