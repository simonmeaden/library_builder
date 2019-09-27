'''
Created on 27 Sep 2019

@author: simonmeaden
'''

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

class ChooseCompilerDialog(QDialog):
    '''
    classdocs
    '''


    def __init__(self, compiler_flavours):
      '''
      Constructor
      '''
      QDialog.__init__(self)
      self.setWindowTitle("Choose Compiler Flavour")
      self.compiler_flavours = compiler_flavours
      
      
    def __init_gui(self):
      """
      """
      
      
      
        