

import shutil , os
# from datetime import datetime
from pathlib import Path
import urlgrabber
from urllib.request import urlsplit
import zipfile, tarfile
import re


from PySide2.QtCore import (
    Signal,
#    Slot,
    QObject,
    QThread,
  )

from common_types import ExistAction


import gettext
gb = gettext.translation('repository', localedir='locales', languages=['en_GB'])
gb.install()
_ = gb.gettext # English (United Kingdom)


#========================================================================================
class FileTransfer(QThread):
  """"""
  
  send_message = Signal(str)
  finished = Signal()
  send_repo_path = Signal(str, str)

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __init__(self):
    """
    Constructor 
    """
    QThread.__init__(self)
    
    self.running = True
    self.download_paths = []
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def run(self):
    while self.running:
      ''''''
      if len(self.download_paths) > 0:
        data = self.download_paths.pop(0)
        name = data[0]
        libname = data[1]
        url = data[2]
        download_path = data[3]
        self.__download_file(name, libname, url, download_path)
        
    self.finished.emit()  
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def set_clone_paths(self, name, libname, url, download_path, exist_action):
    '''''' 
    self.download_paths.append((name, libname, url, download_path, exist_action))
    
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __download_remote_file(self, local_file, download_file):
    data = local_file.read() # read the file data for later reuse
  # save the file.
    with open(str(download_file), 'wb') as f:
      f.write(data)
    local_file.close()

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __download_file(self, name, libname, url, download_path):
    # try to detect already downloaded file
    (version, exists) = self.__detect_existing_download(libname, download_path)
    
    if not exists:
      # download new local version
      try:
        # urlgrabber follows redirects better than using burllib directly
        local_file = urlgrabber.urlopen(url)  # use urlgrabber to open the url
        actual_url = local_file.url  # detects the actual filename of the redirected url
        values = urlsplit(actual_url)  # split the url up into bits
        filepath = Path(values[2].decode('UTF-8'))  # part 2 is the file name section of the url
        filename = filepath.name  # just extract the file name.
        
      except urlgrabber.grabber.URLGrabError as error:
        self.print_message(str(error))
        
      self.print_message(_('Started downloading {}').format(download_path, filename))
      download_file = download_path / filename
      extract_path = self.download_path / name
      extract_path.mkdir(parents=True, exist_ok=True)      
      self.__download_remote_file(local_file, download_file)
      self.__decompress(filename, download_file, download_path, extract_path)
      self.print_message(_('Completed download of {}.').format(filename))
    else:
      # check existing local version against download version
      (f_major, f_minor, f_build) = self.__detect_library_version(version)
      (d_major, d_minor, d_build) = self.__detect_download_version(filename)
      if (d_major > f_major or 
          d_minor > f_minor or
          d_build > f_build):
        # download replacement if newer
        self.print_message(_('Started downloading {} to replace earlier version').format(download_path, filename))
        download_file = download_path / filename
        extract_path = self.download_path / name
        extract_path.mkdir(parents=True, exist_ok=True)
        self.__download_remote_file(local_file, download_file)
        self.__decompress(filename, download_file, download_path, extract_path)
        self.print_message(_('Completed download of {} of replacement version.').format(filename))

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_existing_download(self, libname, download_path):
    if download_path.exists():
      for f in download_path.glob(libname + '*'):
        if f.exists():
          p = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
          m = p.search(f.name)
          version = m.group(1)
          return (version, True)
    
    return ('0.0.0', False) 

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_library_version(self, version):
    f_version = version.split('.')
    major_version = f_version[0]
    minor_version = f_version[1]
    build_version = f_version[2]
    return major_version, minor_version, build_version
  
  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __detect_download_version(self, filename):
    lib_re = re.compile(r'(?P<version>\d+\.\d+\.\d[^.]*)')
    m = lib_re.search(filename)
    d_version = m.group(1).split('.')
    major_version = d_version[0]
    minor_version = d_version[1]
    build_version = d_version[2]
    return major_version, minor_version, build_version

  #――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __decompress(self, filename, download_file, download_path, extract_path):
    self.print_message(_('Decompressing file {}.').format(filename))
    # decompress it
    compressed_filename = str(download_file)
    if zipfile.is_zipfile(compressed_filename):
      with zipfile.ZipFile(compressed_filename, 'r') as zip_file:
        zip_file.extract_all(str(extract_path))
        return extract_path
      
    else:
      try:
        tar_archive = tarfile.open(compressed_filename, 'r:*')
        tar_archive.extractall(path=str(download_path))
        root_dir = os.path.commonprefix(tar_archive.getnames())
        return Path(root_dir)
        
      except tarfile.ReadError as error:
        self.print_message(str(error))
        
      self.print_message(_('Decompressing file {} complete.').format(filename))

      



