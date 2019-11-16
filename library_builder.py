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
#import faulthandler

"""@package tesseract_builder

Downloads and builds the Tesseract OCR library, and if necessary it's
required libraries from their Git repositories.

"""

import sys

from main_window import MainWindow

from PySide2 import QtWidgets
from PySide2.QtCore import (
    QResource,
  )



if __name__ == '__main__':
  
#   options = parse_arguments()
#   print_options(options)


  app = QtWidgets.QApplication([])
  
  QResource.registerResource("icons.rcc");

  window = MainWindow(sys.argv)
  window.show()  # IMPORTANT!!!!! Windows are hidden by default.

  # Start the event loop.
  app.exec_()

