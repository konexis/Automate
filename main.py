from PyQt5.QtCore import QAbstractEventDispatcher, QAbstractNativeEventFilter,QRegExp,Qt,QThread
from PyQt5.QtGui import QIntValidator,QKeySequence,QRegExpValidator,QIcon
from PyQt5.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QComboBox,
                             QVBoxLayout, QFormLayout, QLineEdit, QPushButton,QMainWindow,
                             QTabWidget,QWidget,QStackedWidget,QRadioButton,QShortcut,QPlainTextEdit,
                             QCheckBox,QDoubleSpinBox,QStatusBar,QDockWidget,QSizePolicy,QMessageBox,QSpinBox)

import sys,os,pickle
from time import sleep
import pyautogui
from pyqtkeybind import keybinder
import threading
from action import ActionTreeWidget
from worker import Worker
        
class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('icon.ico'))
        self.setupWidgets()
        
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.setWindowTitle("Auto it!")
        self.stop_threads = False
        pyautogui.FAILSAFE = False

    def setupWidgets(self):
        frame = QFrame()
        frameLayout = QHBoxLayout(frame)

        self.widget = Tabs()
        self.widget.setFixedWidth(400)
        self.statusbar = QStatusBar()
        self.setStatusBar = self.statusbar
     
        self.actionTree = ActionTreeWidget()
        self.dock = QDockWidget("Action List",self)
        self.dock.setWidget(self.actionTree)
        
        self.actionTree.clicked.connect(self.showIndex)
        self.actionTree.doubleClicked.connect(self.onDoubleClick)
        
        self.addDockWidget(Qt.RightDockWidgetArea,self.dock)
        
        self.dock.setFeatures(QDockWidget.DockWidgetMovable)
        
        self.startButton = QPushButton("Start")
        self.stopButton = QPushButton("Stop")
        self.clearButton = QPushButton("Clear")
        self.deleteButton = QPushButton("Delete")
        self.delayButton = QPushButton("Add Delay (ms)")
        self.saveButton = QPushButton("Save Actions")
        self.loadButton = QPushButton("Load Actions")
        self.delaySB = QSpinBox()
        self.delaySB.setMinimum(0)
        self.delaySB.setMaximum(999999999)
        self.delaySB.setSingleStep(100)
        self.delaySB.setValue(1000)


        self.changeActions()
        self.thread = QThread()
        self.thread.start()

        self.worker = Worker()
        self.worker.sbMessage.connect(self.showMessage)
        self.worker.finished.connect(self.stop_thread)
        self.worker.moveToThread(self.thread)
        #self.worker.task()
        
        self.widget.saveHotkeysPB.clicked.connect(self.saveHotkeys)
        self.startButton.clicked.connect(self.thStart)
        self.stopButton.clicked.connect(self.thStop)
        self.clearButton.clicked.connect(self.clearActions)
        self.deleteButton.clicked.connect(self.deleteAction)
        self.delayButton.clicked.connect(lambda: self.addItem(["Delay","Miliseconds",str(self.delaySB.value())]))
        self.saveButton.clicked.connect(self.saveFile)
        self.loadButton.clicked.connect(self.loadFile)
        
        listVBox = QVBoxLayout()
        listVBox.addWidget(self.dock)
        listHBox = QHBoxLayout()
        listHBox.addWidget(self.startButton)
        listHBox.addWidget(self.clearButton)
        listHBox.addWidget(self.deleteButton)
        listHBox2 = QVBoxLayout()
        listHBox2.addWidget(self.widget)
        
        listHBox4 = QHBoxLayout()
        listHBox4.addWidget(self.delaySB)
        listHBox4.addWidget(self.delayButton)
        
        listHBox2.addLayout(listHBox4)
        listHBox3 = QHBoxLayout()
        listHBox3.addWidget(self.stopButton)
        listHBox3.addWidget(self.saveButton)
        listHBox3.addWidget(self.loadButton)
        listVBox.addLayout(listHBox)
        listVBox.addLayout(listHBox3)
        optionVBox = QVBoxLayout()
        optionVBox.addLayout(listHBox2)
        optionVBox.addWidget(self.statusbar)
        
        v_widget = QWidget()
        v_widget.setLayout(optionVBox)
        v_widget.setFixedWidth(400)
        
        frameLayout.addWidget(v_widget)
        frameLayout.addLayout(listVBox)
        
        self.setCentralWidget(frame)
        self.show()

    def saveHotkeys(self):
        deactiveHotkeys(*hotkeysList)
        pickle_out = open(".settings","wb")
        hotkeys=[self.widget.mousePositionHotkey.text(),self.widget.stopActionHotkey.text(),self.widget.startActionHotkey.text(),self.widget.exitAppHotkey.text()]
        pickle.dump(hotkeys,pickle_out)
        pickle_out.close()
        activeHotkeys(*hotkeysList)
        
    def thStart(self):
        self.changeActions()
        self.startButton.setEnabled(False)
        self.t1 = threading.Thread(target = self.worker.start,args=(self.widget.repeatTimes.value(),self.actions,self.widget.repeatCheckBox.isChecked())) 
        self.t1.start()
        
    def thStop(self):
        self.startButton.setEnabled(True)
        self.t2 = threading.Thread(target = self.worker.stop)
        self.t2.start()
        self.stop_thread()
        
    def loadFile(self):
        fileName,_ = QFileDialog.getOpenFileName(self, 'Open Actions', os.getcwd(),"Action Files(*.actions)")
        if fileName:
            pickle_in = open(fileName,"rb")
            self.actions = pickle.load(pickle_in)
            pickle_in.close()
            for i in self.actions:
                self.addItem(i)
            
    def saveFile(self):
        self.changeActions()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName,_ = QFileDialog.getSaveFileName(self,"Save Actions","","Action Files(*.actions)")

        if fileName:
            pickle_out = open(fileName,"wb")
            pickle.dump(self.actions,pickle_out)
            pickle_out.close()
        
    def showIndex(self):
        for ix in self.actionTree.selectedIndexes():
            selectedRow = ix.row() # or ix.data()
        try:self.statusbar.showMessage("Row index = {}".format(selectedRow+1),1000)
        except:pass
        
    def onDoubleClick(self, index):
        item = self.actionTree.currentItem()
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        if self.actionTree.currentIndex().column()!=1:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
    def deleteAction(self):
        for ix in self.actionTree.selectedIndexes():
            selectedRow = ix.row() # or ix.data()
        try:
            self.actionTree.takeTopLevelItem(selectedRow)
            self.statusbar.showMessage("Row {} deleted.".format(selectedRow+1),1000)
        except:pass
        
    def changeActions(self):
        self.actions = self.actionTree.getItems()
        
    def clearActions(self):
        buttonReply = QMessageBox.warning(self, 'Warning!', "Do you want to clear all actions?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.actionTree.clear()
        
    def showMessage(self,i):
        try:
            self.statusbar.showMessage(i[0],i[1])
        except:
            self.statusbar.showMessage(i[0])
        
    def stop_thread(self):
        self.startButton.setEnabled(True)
        self.thread.quit()
        self.thread.wait()
        
    def addItem(self,item):
        parent=self.actionTree.addItem([item[0]],"Action")
        j=0
        for i in range(1,len(item)):
            self.actionTree.addItem(item[i+j:i+j+2],"Setting",parent)
            if i+j+2 == len(item):break
            j+=1
            
    def showItems(self):
        self.actionTree.getItems()
            

class Tabs(QTabWidget):
    def __init__(self):
        super().__init__()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()
        self.tab4UI()
        
        self.addTab(self.tab1,"Mouse")
        self.addTab(self.tab2,"Keyboard")
        self.addTab(self.tab3,"Screen")
        self.addTab(self.tab4,"Settings")
        
        
        
    def tab1UI(self):
        
        self.stackedwidget = QStackedWidget()
        
        self.moveToWid = QWidget()
        self.moveRelWid = QWidget()
        self.dragToWid = QWidget()
        self.dragRelWid = QWidget()
        self.clickToPositionWid = QWidget()
        self.clickWid = QWidget()
        self.scrollWid = QWidget()
        
        self.moveToLay()
        self.moveRelLay()
        self.dragToLay()
        self.dragRelLay()
        self.clickToPositionLay()
        self.clickLay()
        self.scrollLay()
        
        self.stackedwidget.addWidget(self.moveToWid)
        self.stackedwidget.addWidget(self.moveRelWid)
        self.stackedwidget.addWidget(self.dragToWid)
        self.stackedwidget.addWidget(self.dragRelWid)
        self.stackedwidget.addWidget(self.clickToPositionWid)
        self.stackedwidget.addWidget(self.clickWid)
        self.stackedwidget.addWidget(self.scrollWid)
        
        v_box = QVBoxLayout()
        MP_form = QFormLayout()
        
        #MOUSE POSITION
        self.mousepositionButton = QPushButton("Get mouse position {}".format(hotkeysList[0]))
        self.mousepositionLabel = QLabel()
        self.mousepositionButton.clicked.connect(self.getMousePosition)
        self.mousepositionButton.setShortcut("Ctrl+P")
        self.shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut.activated.connect(self.getMousePosition)
        
        #COMBOBOX
        self.comboBox = QComboBox()
        self.comboBox.addItems(["Move To",
                                "Move Relative",
                                "Drag To",
                                "Drag Relative",
                                "Click To",
                                "Click",
                                "Scroll"])
        
        MP_form.addRow(self.mousepositionButton, self.mousepositionLabel)
        MP_form.addRow(self.comboBox)
        v_box.addLayout(MP_form)
        
        
        v_box.addWidget(self.stackedwidget)
        
        self.tab1.setLayout(v_box)
        
        
        self.comboBox.currentIndexChanged.connect(self.cbApply)
        
    def cbApply(self,q):
        self.stackedwidget.setCurrentIndex(q)
        
    def moveToLay(self):
        self.onlyInt = QIntValidator()
        
        self.moveToX=QLineEdit("0")
        self.moveToY=QLineEdit("0")
        self.moveToDuration=QLineEdit("0")
        self.moveToAddButton = QPushButton("Add to List")
        
        self.moveToX.setValidator(self.onlyInt)
        self.moveToY.setValidator(self.onlyInt)
        self.moveToDuration.setValidator(self.onlyInt)

        moveToForm = QFormLayout()
        moveToForm.addRow("X coordinate :",self.moveToX)
        moveToForm.addRow("Y coordinate :",self.moveToY)
        moveToForm.addRow("Duration :",self.moveToDuration)
        moveToForm.addRow(self.moveToAddButton)
        self.moveToWid.setLayout(moveToForm)
        
        self.moveToAddButton.clicked.connect(self.moveToDo)
            
    def moveRelLay(self):
        self.onlyInt = QIntValidator()
        
        self.moveRelX=QLineEdit("0")
        self.moveRelY=QLineEdit("0")
        self.moveRelDuration=QLineEdit("0")
        self.moveRelAddButton = QPushButton("Add to List")
        
        self.moveRelX.setValidator(self.onlyInt)
        self.moveRelY.setValidator(self.onlyInt)
        self.moveRelDuration.setValidator(self.onlyInt)

        moveRelForm = QFormLayout()
        moveRelForm.addRow("Relative X :",self.moveRelX)
        moveRelForm.addRow("Relative Y :",self.moveRelY)
        moveRelForm.addRow("Duration :",self.moveRelDuration)
        moveRelForm.addRow(self.moveRelAddButton)
        self.moveRelWid.setLayout(moveRelForm)
        
        self.moveRelAddButton.clicked.connect(self.moveRelDo)
        
    def dragToLay(self):
        self.onlyInt = QIntValidator()
        
        self.dragToX=QLineEdit("0")
        self.dragToY=QLineEdit("0")
        self.dragToDuration=QLineEdit("0")
        self.dragToAddButton = QPushButton("Add to List")
        
        self.dragToX.setValidator(self.onlyInt)
        self.dragToY.setValidator(self.onlyInt)
        self.dragToDuration.setValidator(self.onlyInt)

        dragToForm = QFormLayout()
        dragToForm.addRow("X coordinate :",self.dragToX)
        dragToForm.addRow("Y coordinate :",self.dragToY)
        dragToForm.addRow("Duration :",self.dragToDuration)
        dragToForm.addRow(self.dragToAddButton)
        self.dragToWid.setLayout(dragToForm)

        self.dragToAddButton.clicked.connect(self.dragToDo)
        
    def dragRelLay(self):
        self.onlyInt = QIntValidator()
        
        self.dragRelX=QLineEdit("0")
        self.dragRelY=QLineEdit("0")
        self.dragRelDuration=QLineEdit("0")
        self.dragRelAddButton = QPushButton("Add to List")
        
        self.dragRelX.setValidator(self.onlyInt)
        self.dragRelY.setValidator(self.onlyInt)
        self.dragRelDuration.setValidator(self.onlyInt)

        dragRelForm = QFormLayout()
        dragRelForm.addRow("Relative X :",self.dragRelX)
        dragRelForm.addRow("Relative Y :",self.dragRelY)
        dragRelForm.addRow("Duration :",self.dragRelDuration)
        dragRelForm.addRow(self.dragRelAddButton)
        self.dragRelWid.setLayout(dragRelForm)
        
        self.dragRelAddButton.clicked.connect(self.dragRelDo)
        
    def clickToPositionLay(self):
        self.onlyInt = QIntValidator()
        
        self.clickToPositionX = QLineEdit("0")
        self.clickToPositionY = QLineEdit("0")
        self.clickToPositionClicks=QLineEdit("1")
        self.clickToPositionInterval=QLineEdit("0")
        self.clickToPositionDuration = QLineEdit("0")

        self.clickToPositionX.setValidator(self.onlyInt)
        self.clickToPositionY.setValidator(self.onlyInt)
        self.clickToPositionClicks.setValidator(self.onlyInt)
        self.clickToPositionInterval.setValidator(self.onlyInt)
        self.clickToPositionDuration.setValidator(self.onlyInt)
        
        self.clickToPositionR1 = QRadioButton("Left")
        self.clickToPositionR2 = QRadioButton("Middle")
        self.clickToPositionR3 = QRadioButton("Right")
        
        self.clickToPositionAddButton = QPushButton("Add to List")
        
        clickToPositionH_box = QHBoxLayout()
        clickToPositionH_box.addWidget(self.clickToPositionR1)
        clickToPositionH_box.addWidget(self.clickToPositionR2)
        clickToPositionH_box.addWidget(self.clickToPositionR3)
        
        clickToPositionForm = QFormLayout()
        clickToPositionForm.addRow("Button :",clickToPositionH_box)
        clickToPositionForm.addRow("X coordinate :",self.clickToPositionX)
        clickToPositionForm.addRow("Y coordinate :",self.clickToPositionY)
        clickToPositionForm.addRow("Clicks (times) :",self.clickToPositionClicks)
        clickToPositionForm.addRow("Interval :",self.clickToPositionInterval)
        clickToPositionForm.addRow("Duration :",self.clickToPositionDuration)
        clickToPositionForm.addRow(self.clickToPositionAddButton)
        self.clickToPositionWid.setLayout(clickToPositionForm)
        
        self.clickToPositionAddButton.clicked.connect(self.clickToPositionDo)
        
    def clickLay(self):
        self.onlyInt = QIntValidator()
        
        self.clickClicks=QLineEdit("1")
        self.clickInterval=QLineEdit("0")
        self.clickDuration = QLineEdit("0")

        self.clickClicks.setValidator(self.onlyInt)
        self.clickInterval.setValidator(self.onlyInt)
        self.clickDuration.setValidator(self.onlyInt)
        
        self.clickR1 = QRadioButton("Left")
        self.clickR2 = QRadioButton("Middle")
        self.clickR3 = QRadioButton("Right")
        
        self.clickAddButton = QPushButton("Add to List")
        
        clickH_box = QHBoxLayout()
        clickH_box.addWidget(self.clickR1)
        clickH_box.addWidget(self.clickR2)
        clickH_box.addWidget(self.clickR3)
        
        clickForm = QFormLayout()
        clickForm.addRow("Button :",clickH_box)
        clickForm.addRow("Clicks (times) :",self.clickClicks)
        clickForm.addRow("Interval :",self.clickInterval)
        clickForm.addRow("Duration :",self.clickDuration)
        clickForm.addRow(self.clickAddButton)
        self.clickWid.setLayout(clickForm)
        
        self.clickAddButton.clicked.connect(self.clickDo)
    
    def scrollLay(self):
        self.onlyInt = QIntValidator()
        self.scrollTimes=QLineEdit("1")
        self.scrollTimes.setValidator(self.onlyInt)
        self.scrollAddButton = QPushButton("Add to List")
        
        scrollForm = QFormLayout()
        scrollForm.addRow("Times :",self.scrollTimes)
        scrollForm.addRow("Times :",self.scrollAddButton)
        self.scrollWid.setLayout(scrollForm)
        
        self.scrollAddButton.clicked.connect(self.scrollDo)
        
    def getMousePosition(self):
        x,y=pyautogui.position()
        x,y=str(x),str(y)
        self.mousepositionLabel.setText("{},{}".format(x,y))
        self.clickToPositionX.setText(x)
        self.clickToPositionY.setText(y)
        self.moveToX.setText(x)
        self.moveToY.setText(y)
        self.dragToX.setText(x)
        self.dragToY.setText(y)
        
        
    def moveToDo(self):
        item = ["Move To","X Coordinate",self.moveToX.text(),"Y Coordinate",self.moveToY.text(),"Duration",self.moveToDuration.text()]
        add(item)
    def moveRelDo(self):
        item = ["Move Relative","Relative X",self.moveRelX.text(),"Relative Y",self.moveRelY.text(),"Duration",self.moveRelDuration.text()]
        add(item)
    def dragToDo(self):
        item = ["Drag To","X Coordinate",self.dragToX.text(),"Y Coordinate",self.dragToY.text(),"Duration",self.dragToDuration.text()]
        add(item)
    def dragRelDo(self):
        item = ["Drag Relative","Relative X",self.dragRelX.text(),"Relative Y",self.dragRelY.text(),"Duration",self.dragRelDuration.text()]
        add(item)
    def clickToPositionDo(self):
        clickSelected = "left"
        if self.clickToPositionR2.isChecked():
             clickSelected = "middle" 
        if self.clickToPositionR3.isChecked():
             clickSelected = "right"
        item = ["Click To","X Coordinate",self.clickToPositionX.text(),"Y Coordinate",self.clickToPositionY.text(),"Button",clickSelected,"Clicks",self.clickToPositionClicks.text(),"Interval",self.clickToPositionInterval.text(),"Duration",self.clickToPositionDuration.text()]
        add(item)
        
    def clickDo(self):
        clickSelected = "left"
        if self.clickR2.isChecked():
             clickSelected = "middle" 
        if self.clickR3.isChecked():
             clickSelected = "right"
        item = ["Click","Button",clickSelected,"Clicks",self.clickClicks.text(),"Interval",self.clickInterval.text(),"Duration",self.clickDuration.text()]
        add(item)
    
    def scrollDo(self):
        item = ["Scroll","Times",self.scrollTimes.text()]
        add(item)
        
    def tab2UI(self):
        self.stackedwidget2 = QStackedWidget()
        
        self.writeWid = QWidget()
        self.pressWid = QWidget()
        self.hotkeyWid = QWidget()
        self.keyDownUpWid = QWidget()
        
        self.writeLay()
        self.pressLay()
        self.hotkeyLay()
        self.keyDownUpLay()
        
        self.stackedwidget2.addWidget(self.writeWid)
        self.stackedwidget2.addWidget(self.pressWid)
        self.stackedwidget2.addWidget(self.hotkeyWid)
        self.stackedwidget2.addWidget(self.keyDownUpWid)

        
        v_box2 = QVBoxLayout()
        
        #COMBOBOX
        self.comboBox2 = QComboBox()
        self.comboBox2.addItems(["Write",
                                 "Press",
                                 "Hotkey",
                                 "Key Down/Up"])
        
        v_box2.addWidget(self.comboBox2)
        v_box2.addWidget(self.stackedwidget2)
        
        self.tab2.setLayout(v_box2)
        
        self.comboBox2.currentIndexChanged.connect(self.cbApply2)
        
    def cbApply2(self,q):
        self.stackedwidget2.setCurrentIndex(q)
        
    def writeLay(self):
        onlyInt = QIntValidator()
        self.writeText = QPlainTextEdit()
        self.writeInterval = QLineEdit("0")
        writeButton = QPushButton("Add to List")
        self.writeInterval.setValidator(onlyInt)
        
        writeForm = QFormLayout()
        writeForm.addRow("Text :",self.writeText)
        writeForm.addRow("Interval :",self.writeInterval)
        writeForm.addRow(writeButton)
        self.writeWid.setLayout(writeForm)
        
        writeButton.clicked.connect(self.writeDo)
        
    def writeDo(self):
        item = ["Write","Interval",self.writeInterval.text(),"Text",self.writeText.toPlainText()]
        add(item)
        
    def pressLay(self):
        onlyInt = QIntValidator()
        nospace = QRegExpValidator(QRegExp("[^ ]+"))
        self.pressText = QLineEdit()
        self.pressInterval = QLineEdit("0")
        self.pressPresses = QLineEdit("1")
        pressButton = QPushButton("Add to List")
        self.pressInterval.setValidator(onlyInt)
        self.pressPresses.setValidator(onlyInt)
        self.pressText.setValidator(nospace)
        pressInfo = QLabel("You can write enter, capslock ve space...\nLook keys.txt for details.")


        pressForm = QFormLayout()
        pressForm.addRow(pressInfo)
        pressForm.addRow("Key :",self.pressText)
        pressForm.addRow("Presses :",self.pressPresses)
        pressForm.addRow("Interval :",self.pressInterval)
        pressForm.addRow(pressButton)
        self.pressWid.setLayout(pressForm)
        
        pressButton.clicked.connect(self.pressDo)
        
    def pressDo(self):
        item = ["Press","Presses",self.pressPresses.text(),"Interval",self.pressInterval.text(),"Key",self.pressText.text()]
        add(item)
        
    def hotkeyLay(self):
        hotkeyInfo = QLabel("If you want ctrl+c write ctrl c\nshift+ctrl+u = shift ctrl u \nalt+f4 = alt f4")
        self.hotkeyText = QLineEdit()
        hotkeyButton = QPushButton("Add to List")
        
        hotkeyForm = QFormLayout()
        hotkeyForm.addRow(hotkeyInfo)
        hotkeyForm.addRow("Hotkey :",self.hotkeyText)
        hotkeyForm.addRow(hotkeyButton)
        self.hotkeyWid.setLayout(hotkeyForm)
        
        hotkeyButton.clicked.connect(self.hotkeyDo)
        
    def hotkeyDo(self):
        item = ["Hotkey","Hotkey",self.hotkeyText.text()]
        add(item)
        
    def keyDownUpLay(self):
        nospace = QRegExpValidator(QRegExp("[^ ]+"))
        self.keyDownUpText = QLineEdit()
        self.keyDownUpText.setValidator(nospace)
        self.keyDownUpR1 = QRadioButton("Down")
        self.keyDownUpR2 = QRadioButton("Up")
        keyDownUpButton = QPushButton("Add to List")
        keyDownUpInfo = QLabel("Down will press key.\nUp will leave key.")


        keyDownUpForm = QFormLayout()
        keyDownUpHBox = QHBoxLayout()
        keyDownUpHBox.addWidget(self.keyDownUpR1)
        keyDownUpHBox.addWidget(self.keyDownUpR2)
        keyDownUpForm.addRow(keyDownUpInfo)
        keyDownUpForm.addRow(keyDownUpHBox)
        keyDownUpForm.addRow("Key :",self.keyDownUpText)
        keyDownUpForm.addRow(keyDownUpButton)
        self.keyDownUpWid.setLayout(keyDownUpForm)
        
        keyDownUpButton.clicked.connect(self.keyDownUpDo)
        
    def keyDownUpDo(self):
        radio = "Key Down"
        if self.keyDownUpR2.isChecked():
            radio = "Key Up"
        item = [radio,"Key",self.keyDownUpText.text()]
        add(item)
        
    def tab3UI(self):
        self.stackedwidget3 = QStackedWidget()
        
        self.screenshotWid = QWidget()
        self.findImageWid =QWidget()
        
        self.screenshotLay()
        self.findImageLay()
        
        self.stackedwidget3.addWidget(self.screenshotWid)
        self.stackedwidget3.addWidget(self.findImageWid)
        
        v_box3 = QVBoxLayout()
        
        #COMBOBOX
        self.comboBox3 = QComboBox()
        self.comboBox3.addItems(["Screenshot",
                                 "Find Image on Screen"])
        
        v_box3.addWidget(self.comboBox3)
        v_box3.addWidget(self.stackedwidget3)
        self.tab3.setLayout(v_box3)
        
        self.comboBox3.currentIndexChanged.connect(self.cbApply3)
        
    def cbApply3(self,q):
        self.stackedwidget3.setCurrentIndex(q)
    
    def screenshotLay(self):
        self.screenshotPath = QLineEdit(os.getcwd())
        self.screenshotPath.setReadOnly(True)
        self.screenshotFile = QLineEdit()
        changePathButton = QPushButton("Change Path")
        screenshotButton = QPushButton("Add to List")
        
        self.screenshotR1 = QRadioButton("Yes")
        self.screenshotR2 = QRadioButton("No")
        
        
        screenshotHBox = QHBoxLayout()
        screenshotHBox.addWidget(self.screenshotR1)
        screenshotHBox.addWidget(self.screenshotR2)
        
        screenshotForm = QFormLayout()
        screenshotForm.addRow("Save Path :",self.screenshotPath)
        screenshotForm.addRow(changePathButton)
        screenshotForm.addRow("File Name :",self.screenshotFile)
        screenshotForm.addRow("Overwrite :",screenshotHBox)
        screenshotForm.addRow(screenshotButton)
        self.screenshotWid.setLayout(screenshotForm)
        changePathButton.clicked.connect(self.changePath)
        
        screenshotButton.clicked.connect(self.screenshotDo)
        
    def changePath(self):
        dir_ = QFileDialog.getExistingDirectory(self, 'Select a folder:', os.getcwd(), QFileDialog.ShowDirsOnly)
        self.screenshotPath.setText(dir_)
        
    def screenshotDo(self):
        if self.screenshotFile.text()=="":
            QMessageBox.warning(self, 'Error!', "Please enter a file name.", QMessageBox.Ok)
        else:
            radio = "yes"
            if self.screenshotR2.isChecked():
                radio = "no"
            item = ["Screenshot","Overwrite",radio,"Dir Path",self.screenshotPath.text(),"File Name",self.screenshotFile.text()]
            add(item)
    
    def findImageLay(self):
        self.findImagePath = QLineEdit()
        self.findImagePath.setReadOnly(True)
        self.findImageInfo = QLabel("Low screen resolution for fast search.")
        findImageButton = QPushButton("Select a Image")
        findImageButton2 = QPushButton("Add to List")
        self.findImageCB = QCheckBox()
        self.findImageCB2 = QCheckBox()
        self.findImageCB3 = QCheckBox()
        self.findImageDSB = QDoubleSpinBox()
        self.findImageDSB.setValue(60)
        
        
        self.findImageForm = QFormLayout()
        self.findImageForm.addRow(self.findImageInfo)
        self.findImageForm.addRow(self.findImagePath)
        self.findImageForm.addRow(findImageButton)
        self.findImageForm.addRow("Search until find",self.findImageCB)
        self.findImageForm.addRow("Press after found",self.findImageCB2)
        self.findImageForm.addRow("Fast find (less sensivity)",self.findImageCB3)
        self.findImageForm.addRow(findImageButton2)
  
        self.findImageWid.setLayout(self.findImageForm)
        self.findImageCB.clicked.connect(self.addRowCB)
        
        findImageButton.clicked.connect(self.selectImage)
        findImageButton2.clicked.connect(self.findImageDo)
        
    def addRowCB(self):
        if self.findImageCB.isChecked():
            self.findImageForm.addRow("Second wait for eact search",self.findImageDSB)
        else:
            label = self.findImageForm.labelForField(self.findImageDSB)
            if label is not None:
                label.deleteLater()
            self.findImageDSB.deleteLater()
            self.findImageDSB = QDoubleSpinBox()
            self.findImageDSB.setValue(60)
        
    def selectImage(self):
        dir_ = QFileDialog.getOpenFileName(self, 'Select a image', os.getcwd(),"Image files (*.jpg *.png)")
        self.findImagePath.setText(dir_[0])
        
    def findImageDo(self):
        if self.findImagePath.text()=="":
            QMessageBox.warning(self, 'Error!', "Please choose a image.", QMessageBox.Ok)
        else:
            cb = "no"
            cb2 = "no"
            cb3 = "no"
            wait = 60.0
            if self.findImageCB.isChecked():
                cb = "yes"
            if self.findImageCB2.isChecked():
                cb2 = "yes"
            if self.findImageCB3.isChecked():
                cb3 = "yes"
            if cb == "yes":
                wait = str(self.findImageDSB.value())
            
            item = ["Find Image","Search Until Find",cb,"Press After Found",cb2,"Fast Find",cb3,"Wait",wait,"File Path",self.findImagePath.text()]
            add(item)
            
    def tab4UI(self):
        self.repeatTimes = QSpinBox()
        self.repeatTimes.setMinimum(0)
        self.repeatTimes.setMaximum(999999)
        self.repeatTimes.setValue(1)
        self.repeatCheckBox = QCheckBox()
        self.mousePositionHotkey = QLineEdit(hotkeysList[0])
        self.stopActionHotkey = QLineEdit(hotkeysList[1])
        self.startActionHotkey = QLineEdit(hotkeysList[2])
        self.exitAppHotkey = QLineEdit(hotkeysList[3])
        self.saveHotkeysPB = QPushButton("Save Hotkeys")
        self.facebook = QLabel("<a href='https://www.facebook.com/fifalamoche'>Contact Me</a>")
        self.facebook.setAlignment(Qt.AlignRight)
        self.facebook.setOpenExternalLinks(True)
        
        tab4Form = QFormLayout()
        tab4Form.addRow(QLabel("                 Repeat Settings"))
        tab4Form.addRow("Repeat Times :",self.repeatTimes)
        tab4Form.addRow("Continuous Loop :",self.repeatCheckBox)
        tab4Form.addRow(QLabel("          Hotkey Settings (Need Restart App)"))
        tab4Form.addRow("Get mouse position :",self.mousePositionHotkey)
        tab4Form.addRow("Stop Action :",self.stopActionHotkey)
        tab4Form.addRow("Start Action :",self.startActionHotkey)
        tab4Form.addRow("Exit App :",self.exitAppHotkey)
        tab4Form.addRow(self.saveHotkeysPB)
        tab4Form.addRow(self.facebook)
        
        self.tab4.setLayout(tab4Form)
        

        
def getHotkeys():
    hotkeysList = ["Ctrl+P","Ctrl+Q","Alt+Space","Ctrl+E"]
    
    try:
        pickle_in = open(".settings","rb")
        hotkeysList = pickle.load(pickle_in)
        pickle_in.close()
        for i in hotkeysList:a=i[0]
    except:hotkeysList = ["Ctrl+P","Ctrl+Q","Alt+Space","Ctrl+E"]
    return hotkeysList

def activeHotkeys(h1,h2,h3,h4):
    keybinder.register_hotkey(window.winId(), h1, window.widget.getMousePosition)
    keybinder.register_hotkey(window.winId(), h2, stopAction)
    keybinder.register_hotkey(window.winId(), h3, start)
    keybinder.register_hotkey(window.winId(), h4, exit_app)
    win_event_filter = WinEventFilter(keybinder)
    event_dispatcher = QAbstractEventDispatcher.instance()
    event_dispatcher.installNativeEventFilter(win_event_filter)

    
    
    
def deactiveHotkeys(h1,h2,h3,h4):
    keybinder.unregister_hotkey(window.winId(), h1)
    keybinder.unregister_hotkey(window.winId(), h2)
    keybinder.unregister_hotkey(window.winId(), h3)
    keybinder.unregister_hotkey(window.winId(), h4)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    hotkeysList = getHotkeys()
    window = MainWindow()
    
    
    def add(item):
        window.addItem(item)
    def start():
        window.startButton.click()
    def stopAction():
        window.thStop()
    def exit_app():
        window.stop_threads = True
        window.close()
        sys.exit(app.exec())
    
    keybinder.init()
    activeHotkeys(*hotkeysList)
    
    
    win_event_filter = WinEventFilter(keybinder)
    event_dispatcher = QAbstractEventDispatcher.instance()
    event_dispatcher.installNativeEventFilter(win_event_filter)

    

    
    sys.exit(app.exec())
    deactiveHotkeys(*hotkeysList)
