'''
Created on 21 Sep 2019

@author: simonmeaden
'''

"""@package tesseract_builder
Downloads and builds the Tesseract OCR library, and if necessary it's
required libraries from their Git repositories.
 
"""
import sys
# import argparse
import os
# from os import walk, path
# from pathlib import Path

# from common_types import ExistAction
# from repository import Repository
from main_window import MainWindow
# from numpy.core.defchararray import lower
# from builtins import dir

from PySide2 import QtWidgets
  
if __name__ == '__main__': 
#   options = parse_arguments()
#   print_options(options)
  
  app = QtWidgets.QApplication([])

  window = MainWindow(sys.argv)
  window.show() # IMPORTANT!!!!! Windows are hidden by default.
  
  # Start the event loop.
  app.exec_()    
  


  
  