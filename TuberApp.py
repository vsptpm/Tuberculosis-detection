#MyApp.py
# D. Thiebaut
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSlot
from TUBER_ui import Ui_MainWindow
from PyQt5.QtGui import QPixmap
import sys
from TuberModel import Model
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import cv2
from PIL import Image
import numpy as np
import os
from keras.models import load_model
from keras.preprocessing import image
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import load_img, img_to_array
from keras import backend as keras



class MainWindowUIClass( Ui_MainWindow ):
    def __init__( self ):
        '''Initialize the super class
        '''
        super().__init__()
        self.model = Model()
        
    def setupUi( self, MW ):
        ''' Setup the UI of the super class, and add here code
        that relates to the way we want our UI to operate.
        '''
        super().setupUi( MW )

        # close the lower part of the splitter to hide the 
        # debug window under normal operations
        #self.splitter.setSizes([300, 0])

    #def debugPrint( self, msg ):
        #'''Print the message in the text edit at the bottom of the
        #horizontal splitter.
        #'''
        #self.debugTextBrowser.append( msg )
    
    
    def refreshAll( self ):
        '''
        Updates the widgets whenever an interaction happens.
        Typically some interaction takes place, the UI responds,
        and informs the model of the change.  Then this method
        is called, pulling from the model information that is
        updated in the GUI.
        '''
        self.lineEdit.setText( self.model.getFileName() )
        
    
    # slot
    def returnPressedSlot( self ):
        ''' Called when the user enters a string in the line edit and
        presses the ENTER key.
        '''
        fileName =  self.lineEdit.text()
        if self.model.isValid( fileName ):
            self.model.setFileName( self.lineEdit.text() )
            self.refreshAll()
        else:
            m = QtWidgets.QMessageBox()
            m.setText("Invalid file name!\n" + fileName )
            m.setIcon(QtWidgets.QMessageBox.Warning)
            m.setStandardButtons(QtWidgets.QMessageBox.Ok
                                 | QtWidgets.QMessageBox.Cancel)
            m.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            ret = m.exec_()
            self.lineEdit.setText( "" )
            self.refreshAll()
            self.debugPrint( "Invalid file specified: " + fileName  )

    # slot
    #def writeDocSlot( self ):
        #''' Called when the user presses the Write-Doc button.
        #'''
        #self.model.writeDoc( self.textEdit.toPlainText() )
        #self.debugPrint( "WriteDoc button pressed!" )
        
    # slot
    def browseSlot( self ):
        ''' Called when the user presses the Browse button
        '''
        #self.debugPrint( "Browse button pressed" )
        self.label_4.setText(" ")

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
                        None,
                        "Open a XRay Image",
                        "",
                        "Image files (*.jpg *.png *.jpeg)",
                        options=options)
        if fileName:
            print(fileName)
            self.lineEdit.setText(fileName)
            self.pixmap = QPixmap(fileName)
            self.adjustPixmap = self.pixmap.scaled(271, 161)
            #self.label.resize(self.pixmap.width(),self.pixmap.height())
            self.label_2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            #self.label.setAlignment(Qt.AlignCenter)
            self.label_2.setPixmap(self.adjustPixmap)
            #self.debugPrint( "setting file name: " + fileName )
            self.model.setFileName( fileName )
            self.refreshAll()

    def dice_coef(self,y_true, y_pred):
        y_true_f = keras.flatten(y_true)
        y_pred_f = keras.flatten(y_pred)
        intersection = keras.sum(y_true_f * y_pred_f)
        return (2. * intersection + 1) / (keras.sum(y_true_f) + keras.sum(y_pred_f) + 1)

    def dice_coef_loss(self,y_true, y_pred):
        return -self.dice_coef(y_true, y_pred)

    def test_load_image(self,test_file, target_size=(256, 256)):
        img = cv2.imread(test_file, cv2.IMREAD_GRAYSCALE)
        img = img / 255
        img = cv2.resize(img, target_size)
        img = np.reshape(img, img.shape + (1,))
        img = np.reshape(img, (1,) + img.shape)
        return img

    def save_result(self,save_path, npyfile, test_files):
        for i, item in enumerate(npyfile):
            result_file = test_files
            img = (item[:, :, 0] * 255.).astype(np.uint8)

            filename, fileext = os.path.splitext(os.path.basename(result_file))

            result_file = 'predict.png'

            cv2.imwrite(result_file, img)
    def grabcut(self,imagepath):
        print("entring grabcut")
        # Load the image
        image = os.path.basename(imagepath)
        image_file = imagepath
        img = cv2.imread(image_file)
        img = cv2.resize(img, dsize=(512, 512), interpolation=cv2.INTER_CUBIC)
        print("read image file")
        # Create a 0's mask
        mask = np.zeros(img.shape[:2], np.uint8)
        # Create 2 arrays for background and foreground model
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)

        rect = (350, 66, 300, 624)
        mask, bgdModel, fgdModel = cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)

        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        img_seg = img * mask2[:, :, np.newaxis]

        # Load the masked image
        mask_image_file = "predict.png"
        img_mark = cv2.imread(mask_image_file)
        print("read mask file")
        # cv2.imshow('m', img_mark)
        # Subtract to obtain the mask
        mask_dif = cv2.subtract(img_mark, img_seg)
        # Convert the mask to grey and threshold it
        mask_grey = cv2.cvtColor(mask_dif, cv2.COLOR_BGR2GRAY)
        ret, mask1 = cv2.threshold(mask_grey, 200, 255, 0)

        print("mask[mask1 == 255] = 1")
        mask[mask1 == 255] = 1
        mask, bgdModel, fgdModel = cv2.grabCut(img, mask, None, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_MASK)
        mask_final = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        img_out = img * mask_final[:, :, np.newaxis]
        print("generated cropped image")

        # cv2.imwrite(r'C:\Users\ATHIRANIRMAL\Desktop\PROJECT\Tuberculosis_Project\GrabCut', img_out)
        cv2.imwrite('cropped.png',img_out)
        print("saving cropped.png")


    def processImageSlot(self):

        print('image loaded')
        images = []
        fileName = self.lineEdit.text()
        model_mask = load_model('unet_lung_seg.hdf5', custom_objects={'dice_coef_loss':self.dice_coef_loss, 'dice_coef':self.dice_coef})
        print('lung seg model loaded')
        test_gen = self.test_load_image(fileName,target_size=(512, 512))
        results = model_mask.predict(test_gen)
        self.save_result(os.getcwd(), results,fileName )
        self.grabcut(fileName)

        img = load_img('cropped.png', target_size=(224, 224), color_mode='rgb', interpolation='lanczos')
        img_array = img_to_array(img, data_format='channels_last', dtype='float32')
        images.append(img_array)
        images = np.array(images).reshape(-1, 224, 224, 3)
        images/=255.0

        #model = load_model('vgg19-best-model.h5')
        model = load_model('DenseNet201_best_model.h5')
        result = model.predict(images)
        prediction = result.argmax(1)
        print(prediction)
        if prediction[0] == 1:
            pred = "Normal"
        else:
            pred = "Tuberculosis"

        self.label_4.setText(pred)
            
            
def main():
    """
    This is the MAIN ENTRY POINT of our application.  The code at the end
    of the mainwindow.py script will not be executed, since this script is now
    our main program.   We have simply copied the code from mainwindow.py here
    since it was automatically generated by '''pyuic5'''.

    """
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = MainWindowUIClass()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

main()
