from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Message_Worker(QObject):
   finished = pyqtSignal()
   message_signal = pyqtSignal(str)
   def __init__(self, message) -> None:
       super().__init__()
       self.message = message
   def run(self):
      self.message_signal.emit(self.message)
      self.finished.emit()