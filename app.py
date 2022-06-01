import hashlib
import json
import os
import random
import resource
import string
import sys
import time
from concurrent.futures import thread
from datetime import datetime
from glob import glob
from pathlib import Path
from posixpath import expanduser

import numpy
from PIL import Image, ImageSequence
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication, QMainWindow

root_dir = os.path.dirname(__file__)
build_dir = os.path.join(Path.home(),"desktop")

import itertools

list_style = """
                     {
                  font-weight: 700;
                  font-size: 1.2em;
                  font: 18pt "Calibri";
                  width: 100%;
                  padding: 0.8em;
                  border: 5px solid rgb(228, 228, 228);
                  background:grey;
                  box-shadow: 0.1em 0em 0.4em 0em grey;
                  border-radius: 0.5em;
                  text-align: center;
               }
       """


class create_gif_worker(QObject):
   progress = pyqtSignal(int)
   finished = pyqtSignal()
   
   def run(self):
      dir_list = glob(f"{build_dir}/build/images/*.png")
      frames = []
      i=0
      for img in dir_list:
         img = Image.open(img).convert("RGBA")
         frames.append(img)
         self.progress.emit(int((int(i)/len(self.dir_list))*100))
         i = i+1
      frames[0].save(f"{build_dir}/build/gif/model.gif",
            save_all=True,
            append_images=frames[1:],
            duration=500,
            loop=0)
      self.finished.emit()



class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    update_meta = pyqtSignal(list)
    update_img_counter = pyqtSignal(int)
    def __init__(self,counter, Height=3000, Width=3000) -> None:
      super(Worker,self).__init__()
      self.counter = counter
      self.height = Height
      self.width = Width
    @pyqtSlot()
    def run(self):
       with open(root_dir+"/config.json","r+") as reader:
           data = json.load(reader)
           trait_path = Path(data['traits_dir'])
           layers = data['traits']

       random_traits = []
       for layer in layers:
             layer_path = Path.joinpath(trait_path,layer)
             traits = glob(str(Path.joinpath(layer_path,"*")))
             random_traits.append(traits)
       traits_list = list(itertools.product(*random_traits))
       for s in range(5):
          random.shuffle(traits_list)
       j = 1
       for i in range(0,self.counter):
          final_image = None
          attributes = []
          self.progress.emit(round((int(i)/self.counter)*100))
          traits = traits_list[i]
          for trait in traits:
             attributes.append(
                {
                   "trait_type": os.path.split(os.path.split(trait)[0])[-1],
                   "value": os.path.split(trait)[-1].split(".")[0]
                }
             )
             new_image = Image.open(trait).convert("RGBA")
             if final_image is None:
                final_image = new_image
             else:
                final_image.alpha_composite(new_image)
          resized_image = final_image.resize((self.height,self.width),Image.ANTIALIAS)
          resized_image.save(f'{build_dir}/build/images/{str(j)}.png')
          self.update_meta.emit([attributes,j])
          self.update_img_counter.emit(j)
          j = j + 1
       self.finished.emit()

      # with open(root_dir+"/config.json","r+") as reader:
      #    data = json.load(reader)
      #    trait_path = Path(data['traits_dir'])
      #    layers = data['traits']
      #    random_layers = []
      #    uniqueDnaTorrance = set()
      #    for i in range(1, self.counter+1):
      #       ranodm_traits = []
      #       final_image = None
      #       attributes = []
      #       for layer in layers:
      #          layer_path = Path.joinpath(trait_path,layer)
      #          traits = glob(str(Path.joinpath(layer_path,"*")))
      #          trait_ = random.choice(traits)
      #          attributes.append(
      #             {
      #                "trait_type": os.path.split(os.path.split(trait_)[0])[-1],
      #                "value": os.path.split(trait_)[-1].split(".")[0]
      #             }
      #          )
      #          if trait_ not in ranodm_traits:
      #             new_image = Image.open(trait_).convert("RGBA")
      #             if final_image is None:
      #                final_image = new_image
      #             else:
      #                final_image.alpha_composite(new_image)
      #             ranodm_traits.append(trait_)
      #          else:
      #             continue
      #       resized_image = final_image.resize((self.height,self.width),Image.ANTIALIAS)
      #       resized_image.save(f'{build_dir}/build/images/{str(i)}.png')
      #       random_layers.append(ranodm_traits)
   #  def get_dirs(self,loop_c):
   #     i = 0
   #     while i<loop_c:




class UI(QMainWindow):
   def __init__(self) -> None:
       super(UI,self).__init__() 
       self.list_style = list_style
       #Load the UI File
       uic.loadUi('app.ui',self)
       self.setWindowTitle("NFTG")
       self.setStyleSheet("background-color: #E2F3FE;")
      #  self.setStyleSheet("background-color: #2E02C1;color:#fff;")
       self.setWindowIcon(QIcon(":/icons/assets/app-icon.ico"))
       self.setFixedSize(self.size())

       # message box
       self.messageBox = self.findChild(QLabel,"label_5")

       # Image Height 
       self.height = self.findChild(QLineEdit,"height")
       self.height.setValidator(QIntValidator(1, 8000,self))

       # Image Height 
       self.width = self.findChild(QLineEdit,"width")
       self.width.setValidator(QIntValidator(1, 8000,self))

       # Generate images amount
       self.how_many_generate = self.findChild(QLineEdit, "generate_amount")
       self.how_many_generate.setValidator(QIntValidator(1, 99999,self))
       
      # layer list linked
       self.select_dir = self.findChild(QCommandLinkButton,"commandLinkButton")
       self.select_dir.clicked.connect(self.select_dir_handler)

      # generate button
       self.generate_btn = self.findChild(QPushButton,"pushButton")
       self.generate_btn.clicked.connect(self.generate_handler)

       # Progressbar 
       self.progress_bar = self.findChild(QProgressBar, "progressBar")
       self.progress_bar.setVisible(False)

       # QListWidget
       self.list_View = self.findChild(QListWidget,"listWidget")
       self.list_View.setStyleSheet("QListWidget::item "+self.list_style) 

       self.list_container(self.list_View)

       # layer list label
       self.layer_text = self.findChild(QLabel, "layer_label")

       # image generate maximum amount
       self.mx_img_value = self.findChild(QLabel,"mx_img_value")

       # confirm config list btn
       self.config_btn = self.findChild(QPushButton,"config_btn")
       self.config_btn.clicked.connect(self.config_handler)

       # generated image counter
       self.img_counter = self.findChild(QLabel,"img_counter")

       # rarity set button
      #  self.set_rarity = self.findChild(QPushButton,"setRarity")
      #  self.set_rarity.clicked.connect(self.set_Rarity)

      # check if layer list or directory is exist or not
       self.traits_dir = None
       self.traits_list = None

       try:
         with open(root_dir+"/config.json","r+") as reader:
            data = json.load(reader)
            self.traits_dir = data['traits_dir']
            self.traits_list = data['traits']
            self.max_value = data['max_limit']

       except Exception as e:
         self.list_View.setVisible(False)
         self.layer_text.setVisible(False)
         self.mx_img_value.setVisible(False)
         self.config_btn.setVisible(False)
         self.max_value = 0

   # list_view configurations
   def list_container(self, list_View):
      self.list_View.setIconSize(QSize(24, 24))
      self.list_View.setDragDropMode(QAbstractItemView.InternalMove)
      self.list_View.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
      self.list_View.setDefaultDropAction(Qt.MoveAction) 
      self.list_View.setSelectionMode(QAbstractItemView.ExtendedSelection)
      self.list_View.setAcceptDrops(True)
      self.list_View.setDragEnabled(True)
      try:
         with open(root_dir+"/config.json","r+") as reader:
            data = json.load(reader)
            for item in data['traits']:
               icon = QIcon(':/icons/assets/folder-icon.ico')
               itm = QListWidgetItem(icon,item)
               self.list_View.addItem(itm)
            self.max_value = data['max_limit']
            self.mx_img_value.setText('max limit Number '+str(data['max_limit']))
      except Exception as e:
         # print(e)
         self.messageBox.setText('Please Select Directory Where Traits Exist')

   # config directory
   def make_dirs(self, folder):
      """Creates the directories to store final images and later on, their corresponding json data. If
      the folders already exist, print to confirm and continue with the program.
      """
      build_dirs = ['build', 'build/images', 'build/json','build/gif']
      for _dir in build_dirs:
         if not os.path.isdir(folder+"/"+_dir):
               os.mkdir(folder+"/"+_dir)

   # calculate maximum limitation of image creation
   def get_max_limit(self,trait_path, layers):
      random_traits = []
      for i,layer in enumerate(layers):
         layer_path = Path.joinpath(trait_path,layer)
         traits = glob(str(Path.joinpath(layer_path,"*")))
         random_traits.append(traits)
      
      return len(list(itertools.product(*random_traits)))


   # traits folders handler
   def select_dir_handler(self):
      folder = str(
         QFileDialog.getExistingDirectory(
            self, 
            "Select Directory",
            build_dir,
            QFileDialog.ShowDirsOnly
            )
         )
      if folder != "":
         base_layers = [os.path.split(i)[-1] for i in glob(os.path.join(folder,'*'))]
         total_traits = [glob(os.path.join(im,"*.png")) for im in  [i for i in glob(os.path.join(folder,'*'))]]
         file_counter = [len(i) for i in [glob(os.path.join(str(folder)+"/"+j,"*")) for j in base_layers]]
         config_layers = {
            "traits_dir":str(folder),
            "traits_counter": file_counter,
            "traits": base_layers,
            "max_limit": self.get_max_limit(Path(folder), base_layers)
            }
         with open(root_dir+"/config.json","w+") as writer:
            writer.write(json.dumps(config_layers, indent=4))
            self.list_View.clear()
            icon = QIcon(':/icons/assets/folder-icon.ico')
            for item in base_layers:
               itm = QListWidgetItem(icon,item)
               self.list_View.addItem(itm)
         self.list_View.setVisible(True)
         self.layer_text.setVisible(True)
         self.mx_img_value.setVisible(True)
         self.mx_img_value.setText('max limit of images '+str(self.get_max_limit(Path(folder), base_layers)))
         self.max_value = self.get_max_limit(Path(folder), base_layers)
         self.messageBox.setText('Updated')
      else:
         self.messageBox.setText('Please Select Directory Where Traits Exist')

   # config button handler
   def config_handler(self):
      items = [i for i in self.get_items()]
      with open(root_dir+"/config.json","r+") as reader:
         data = json.load(reader)
      data['traits'] = items
      with open(root_dir+"/config.json","w+") as writer:
         writer.write(json.dumps(data, indent=4))
      self.messageBox.setText('Layers Saved.')

   # get all items from list_view
   def get_items(self):
      for i in range(self.list_View.count()):
         if self.list_View.item(i).text() == "":
            continue
         yield self.list_View.item(i).text()
   
   # Progress bar updater
   def update_progress(self,n):
      self.progress_bar.setValue(n)

   def img_counter_update(self,n):
      self.img_counter.setText(str(n))
   
   # create MetaData file
   def create_meta(self, params):
      attributes = params[0]
      counter = params[-1]
      meta = {
         "name": "model name #"+str(counter),
         "description": "Remember to replace this , with your description",
         "image": f"ipfs://NewUriToReplace/{counter}.png",
            "dna": hashlib.sha256(json.dumps(attributes).encode('utf-8')).hexdigest(),
            "edition": counter,
            "date": datetime.now().timestamp(),
            "attributes":attributes,
            "compiler": "NFTG Art Engine"
      }
      with open(f"{build_dir}/build/json/{counter}.json","w+") as writer:
         writer.write(json.dumps([meta], indent=4))

      # image Generate Handler
   def generate_handler(self):
      self.make_dirs(build_dir) # create build directory in desktop
      height = int(self.height.text()) if self.height.text() != '' else 0
      width = int(self.width.text()) if self.height.text() != '' else 0 
      if self.how_many_generate.text() != '':
         image_count = int(self.how_many_generate.text())
         if image_count>0 and image_count <= self.max_value:
            self.thread = QThread()
            if height == 0 or width == 0:
               self.worker = Worker(image_count)
            else:
               print(height,width)
               self.worker = Worker(image_count, height, width )
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.update_progress)
            self.worker.update_meta.connect(self.create_meta)
            self.worker.update_img_counter.connect(self.img_counter_update)
            self.thread.start()

            

            self.progress_bar.setVisible(True)
            self.generate_btn.setEnabled(False)
            self.config_btn.setEnabled(False)
            self.img_counter.setVisible(True)

            self.messageBox.setText("Image is generating please wait until completed.")

            self.thread.finished.connect(
               lambda:self.progress_bar.setVisible(False)
            )
            self.thread.finished.connect(
               lambda:self.generate_btn.setEnabled(True)
            )
            self.thread.finished.connect(
               lambda:self.progress_bar.setValue(0)
            )
            self.thread.finished.connect(
               lambda:self.config_btn.setEnabled(True)
            )
            self.thread.finished.connect(
               lambda: self.messageBox.setText("completed.")
            )
            
            self.thread.finished.connect(
               lambda: self.img_counter.setVisible(False)
            )


            # self.thread.finished.connect(
            #    lambda: self.create_gif()
            # )

         else:
            self.messageBox.setText(f"The maximum limit is {self.max_value} for your traits.")
      else:
        self.messageBox.setText("Please Enter How Many Images You Want To Generate?")

   def create_new_image(self,img_path):
      img = Image.open(img_path).convert("RGBA")
      return img


   def set_Rarity(self):
      print("rarity window opened")
      # self.table_widget = Rarity_Window()

   # create gif image file
   def create_gif(self):
      create_gif_worker
      # dirs = glob(f"{build_dir}/build/images/*.png")
      # frames = []
      # i=0
      # for img in dirs:
      #    img = Image.open(img).convert("RGBA")
      #    frames.append(img)
      #    self.update_progress(int((int(i)/len(dirs))*100))
      #    i = i+1
      #    time.sleep(0.05)
      # frames[0].save(f"{build_dir}/build/gif/model.gif",
      #       save_all=True,
      #       append_images=frames[1:],
      #       duration=500,
      #       loop=0)
   #    dirs = glob(f"{build_dir}/build/images/*.png")

   #    gif_creator = create_gif_worker(dirs)

   #    gif_creator.moveToThread(thread)
   #    thread.started.connect(gif_creator.run)
   #    gif_creator.finished.connect(thread.quit)

   #    gif_creator.finished.connect(gif_creator.deleteLater)
   #    thread.finished.connect(thread.deleteLater)

   #    gif_creator.progress.connect(self.update_progress)
   #    thread.start()
            
   #    self.progress_bar.setVisible(True)
   #    self.generate_btn.setEnabled(False)
   #    self.config_btn.setEnabled(False)
   #    self.messageBox.setText("GIF file Generating ...")
   #    thread.finished.connect(
   #       lambda:self.progress_bar.setVisible(False)
   #    )
   #    thread.finished.connect(
   #       lambda:self.generate_btn.setEnabled(True)
   #    )
   #    thread.finished.connect(
   #       lambda:self.progress_bar.setValue(0)
   #    )
   #    thread.finished.connect(
   #       lambda:self.config_btn.setEnabled(True)
   #    )

# class MyTable(QWidget):

#     def __init__(self):
#         super(MyTable, self).__init__()
#         self.Table()

#     def Table(self):
#         self.mytable()
#         self.layout = QVBoxLayout()
#         self.layout.addWidget(self.tableWidget)
#         self.setLayout(self.layout)
#         self.show()

#     def mytable(self):
#          self.tableWidget = QTableWidget()
#          # set table widget attributes
#          self.tableWidget.setEditTriggers(QAbstractItemView.DoubleClicked) # use NoEditTriggers to disable editing
#          self.tableWidget.setAlternatingRowColors(True)
#          self.tableWidget.setSelectionMode(QAbstractItemView.NoSelection)
#          self.tableWidget.verticalHeader().setDefaultSectionSize(18) # tighten up the row size
#          self.tableWidget.horizontalHeader().setStretchLastSection(False) # stretch last column to edge
#          self.tableWidget.setSortingEnabled(False) # allow sorting


#          self.tableWidget.setRowCount(1)
#          self.tableWidget.setColumnCount(1)
#          self.tableWidget.setItem(0, 0 , QTableWidgetItem("Hello"))
#          self.tableWidget.move(300, 300)


class Rarity_Window(QWidget):
   updateSignal = pyqtSignal()
   def __init__(self, parent=None):
      super(Rarity_Window, self).__init__(parent)
      with open(root_dir+"/config.json","r+") as reader:
         data = json.load(reader)
         self.trait_path = Path(data['traits_dir'])
         self.layers = data['traits']
         self.folder = data['traits_dir']
      self.resize(640,480)
      self.setWindowTitle("Rarity Configuration")
      self.setWindowIcon(QIcon(":/icons/assets/app-icon.ico"))


      self.button = QPushButton('Confirm')
      self.button.clicked.connect(self.populate)
      layout = QVBoxLayout()
      self.setLayout(layout)
      self.createTable()
      layout.addWidget(self.table_widget)
      layout.addWidget(self.button)


      self.show()

   def FindMaxLength(self, folder_dir, layers):
      lst = [glob(os.path.join(os.path.join(self.folder,layer), "*")) for layer in self.layers]
      maxList = max(lst, key = len)
      maxLength = max(map(len, lst))
         
      return maxLength

   def createTable(self):

      self.table_widget = QTableWidget(self)

      #   for i in self.layers:
      #      print([i for i in glob(os.path.join(self.folder,"*"))])
      self.table_widget.setRowCount(self.FindMaxLength(self.folder, self.layers))
      self.table_widget.setColumnCount(len(self.layers))

      
      self.table_widget.setAutoScroll(True)
      self.table_widget.setSortingEnabled(False)
      self.table_widget.setHorizontalHeaderLabels(self.layers)
      self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
      for i, layer in  enumerate(self.layers):
         for j,trait in enumerate(glob(os.path.join(os.path.join(self.folder,layer), "*"))):
            # print(os.path.split(trait)[-1])
            self.table_widget.setItem(j,i,QTableWidgetItem(os.path.split(trait)[-1].split(".")[0]))
      
      

   def populate(self):
      rarities = {}
      for i,layer in enumerate(self.layers):
         rarity = list()
         for j in range(self.FindMaxLength(self.folder,self.layers)):
            try:
               rarity.append(self.table_widget.item(j,i).text())
               # print(self.table_widget.item(j,i).text())
            except Exception as e:
               # print(e)
               pass
         rarities.update({layer:rarity})
      print(rarities)
      # print(self.FindMaxLength(self.folder, self.layers))
      # for i, layer in  enumerate(self.layers):
      #    for j,trait in enumerate(glob(os.path.join(os.path.join(self.folder,layer), "*"))):
      #       # print(os.path.split(trait)[-1])
      #       self.table_widget.setItem(j,i,QTableWidgetItem(os.path.split(trait)[-1].split(".")[0]))

         # traits = [t for t in [glob(os.path.join(i,"*.png")) for i in glob(os.path.join(self.folder,"*"))

         # for t in traits:
         #    print(t)

         # for i in range(nrows):
         #       for j in range(ncols):
         #          item = QTableWidgetItem('%s%s' % (i, j))
         #          self.table_widget.setItem(0, 0, item)
         # self.updateSignal.emit()

   #  def update_table(self):
   #      self.table_widget.sortItems(0,Qt.DescendingOrder)




def window():
   app = QApplication(sys.argv)
   win = UI() # initialized UI 
   win.show() # show Window UI
   sys.exit(app.exec_())

   
if __name__ == '__main__':
   window()
