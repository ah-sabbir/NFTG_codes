from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *



class Progress_Worker(QObject):
   def __init__(self, count, progress) -> None:
       super().__init__()
       self.count = count
       self.progress = progress
   def run(self):
      pass



class listItems_worker(object):
   def __init__(self):
      super(listItems,self).__init__()
   def iterAllItems(self):
    for i in range(self.count()):
        yield self.item(i)

