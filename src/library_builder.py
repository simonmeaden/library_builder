'''
Created on 21 Sep 2019

@author: simonmeaden
'''

"""@package tesseract_builder
Downloads and builds the Tesseract OCR library, and if necessary it's
required libraries from their Git repositories.
 
"""
import sys
import os
from main_window import MainWindow

from PySide2 import QtWidgets
from PySide2.QtCore import (
    Qt,
    QResource,
  )
  
if __name__ == '__main__': 
#   options = parse_arguments()
#   print_options(options)
  
  app = QtWidgets.QApplication([])
  
  QResource.registerResource("icons.rcc");

  window = MainWindow(sys.argv)
  window.show() # IMPORTANT!!!!! Windows are hidden by default.
  
  # Start the event loop.
  app.exec_()    
  


  
  