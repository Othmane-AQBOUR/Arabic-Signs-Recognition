from multiprocessing.spawn import get_preparation_data
from operator import index
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QColor, QImage , QIcon
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from qtwidgets import Toggle, AnimatedToggle
import sys
import cv2
import numpy as np
#from utils import Sign_Recognition as sr
import os
from pyparsing import Char
from tensorflow.keras import models
import imutils
from imutils.video import FPS
from threading import Thread
import arabic_reshaper
from bidi.algorithm import get_display
import threading
import time

'''
#Python 3
if sys.version_info >= (3, 0):
	from queue import Queue
#Python 2.7
else:
	from Queue import Queue
'''



currentVal = u''
phraseList = []

#Tensorflow utils
ROOT_DIR =os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join( ROOT_DIR , 'saved_model/ARS_REC_model_gray_v3.h5') 
model = models.load_model(path)
IMG_SIZE = 64
CATEGORIES = ['ain', 'al', 'aleff', 'bb', 'dal', 'dha', 'dhad', 'fa', 
             'gaaf', 'ghain', 'ha', 'haa', 'jeem', 'kaaf', 'khaa', 'la', 
             'laam', 'meem', 'nun', 'ra', 'saad', 'seen', 'sheen', 'ta', 
             'taa', 'thaa', 'thal', 'toot', 'waw', 'ya', 'yaa', 'zay']
buckwalterMod = {
        'ء': 'c', 'ا': 'A', 'إ': 'A',
        'أ': 'aleff', 'آ': 'A', 'ب': 'bb',
        'ة': 'toot', 'ت': 'taa', 'ث': 'thaa',
        'ج': 'jeem', 'ح': 'haa', 'خ': 'khaa',
        'د': 'dal', 'ذ': 'thal', 'ر': 'ra',
        'ز': 'zay', 'س': 'seen', 'ش': 'sheen',
        'ص': 'saad', 'ض': 'dhad', 'ط': 'ta',
        'ظ': 'dha', 'ع': 'ain', 'غ': 'ghain',
        'ف': 'fa', 'ق': 'gaaf', 'ك': 'kaaf',
        'ل': 'laam', 'م': 'meem', 'ن': 'nun',
        'ه': 'ha', 'ؤ': 'c', 'و': 'waw',
        'ى': 'yaa', 'ئ': 'c', 'ي': 'ya',
        }

#reversedBucket = {y: x for x, y in buckwalterMod.items()} 

fps = FPS().start()
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        #self.Q = Queue(maxsize=128)

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            #if not self.Q.full():
            ret, cv_img = cap.read()
            if ret:
                    #self.Q.put(cv_img)
                self.change_pixmap_signal.emit(cv_img)
            else:
                self.stop()
                return
        # shut down capture system
        cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class Window(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt ASR GUI")
        self.setWindowIcon(QIcon('logo192.png'))
        self.display_width = 640
        self.display_height = 480

        #title
        self.title = QLabel('Arabic Signs Language')
        self.title.setObjectName('title1')
        self.title.setAlignment(Qt.AlignCenter)
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.setObjectName('vid')
        self.image_label.resize(self.display_width, self.display_height)
        '''
        effect = QGraphicsDropShadowEffect(self)
        effect.setColor(QColor(0x99, 0x99, 0x99))
        effect.setBlurRadius(10)
        effect.setXOffset(5)
        effect.setYOffset(5)
        self.image_label.setGraphicsEffect(effect)
        '''

        #sr = reversedBucket['aleff'].encode('UTF-8')
        #print(sr)
        # create a text label
        predi = 'none'
        #phrase_txt = u''
        self.textLabel = QLabel(predi , self)
        self.textLabel.setObjectName('predi')
        self.textLabel.setAlignment(Qt.AlignCenter)
        
        #self.phrase = QLabel(phrase_txt , self)
        #self.printButton = QPushButton('PyQt5 button', self)
        #self.printButton.clicked.connect(self.on_click)

        self.toggle_1 = Toggle()
        # create a vertical box layout and add the labels
        wid = QWidget(self)
        self.setCentralWidget(wid)
        vbox =  QGridLayout()
        vbox.addWidget(self.title , 0,1)
        vbox.addWidget(self.image_label,1,1)
        vbox.addWidget(self.textLabel,2,1)
        vbox.addWidget(self.toggle_1,2,2)
        #vbox.addWidget(self.printButton)
        #vbox.addWidget(self.phrase)
        
        # set the vbox layout as the widgets layout
        wid.setLayout(vbox)
        
        # create the video capture thread
        self.Vid_thread = VideoThread()
        # connect its signal to the update_image slot
        self.Vid_thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()
        print(currentVal)

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv2.rectangle(cv_img , (300,300) , (100,100), (0,255,0) , 0))
        image_to_process = cv_img[100:300, 100:300]
        fps.update()
        index = self.predict_img(image_to_process)
        prediction = CATEGORIES[index]
        #currentVal = reversedBucket[prediction]
        self.textLabel.setText(prediction)
        self.image_label.setPixmap(qt_img)

    def predict_img(image):
        g_img = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        resized = imutils.resize(g_img, width=IMG_SIZE , height=IMG_SIZE)
        l_img = [resized]

        input = np.array(l_img)
        input = input.reshape(-1 , IMG_SIZE, IMG_SIZE , 1 )
        #convert to flaot
        input = input.astype('float32')
        #converting value from [0,255] to [0,1]
        input /= 255.0
        prediction = model.predict(input)
        ind = np.argmax(prediction)
        #print(ind[0][0])
        return ind

    '''
    @pyqtSlot()
    def on_click(self):
        print('PyQt5 button click')
        phraseList.append(currentVal)
        if(len(phraseList) > 3):
            phrase_txt = ''.join(phraseList)
    '''
    
    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
    def closeEvent(self, event):
        fps.stop()
        print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
        self.thread.stop()
        event.accept()
    
    def openCamera(self):
        pass





if __name__ == "__main__":
    # create pyqt5 app
    # start the app
    App = QApplication(sys.argv)
    App.setObjectName('app')
    
    css = """
        QWidget{
            margin: 0;
            padding: 0;
        }
        #vid{
            background:rgb(255, 255, 255);
            border-top-left-radius: 30px;
            border-top-right-radius: 30px;
        }
        #title1{
            text-align: center;
            font-size: 40px;
            font-family: Fira Sans;
        }
        #predi{
            text-align: center;
            font-size: 30px;
        }
    """
    App.setStyleSheet(css)
    # create the instance of our Window
    window = Window()
    window.show()
    

    sys.exit(App.exec())