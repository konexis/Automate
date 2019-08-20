import os
from PyQt5.QtCore import QObject,pyqtSignal,pyqtSlot
import pyautogui
from time import sleep


class Worker(QObject):
    'Object managing the simulation'
    finished = pyqtSignal()
    sbMessage = pyqtSignal(list)

    def __init__(self):
        super(Worker, self).__init__()
    
    def control(self,action):
        cd = {"X Coordinate":"int","Y Coordinate":"int","Relative X":"int","Relative Y":"int","Clicks":"int","Times":"int",
              "Button":["left","middle","right"], "Overwrite":["yes","no"], "Search Until Find":["yes","no"], "Press After Found":["yes","no"],"Fast Find":["yes","no"],
              "Duration":"float","Interval":"float", "Presses":"int","Wait":"float","Miliseconds":"int",
              "Text":"str", "Key":"key", "Hotkey":"multiKey","Dir Path":"str","File Name":"str","File Path":"str"}
        keys = pyautogui.KEYBOARD_KEYS
        j=0
        for i in range(1,len(action)):
            setting_ = action[i+j:i+j+2]
            if cd[setting_[0]] == "int":
                try:int(setting_[1])
                except: return [False,i]
            if setting_[0] == "Button":
                if not setting_[1] in cd[setting_[0]]: return [False,i]
            if cd[setting_[0]] == "float":
                try: float(setting_[1])
                except: return [False,i]
            if cd[setting_[0]] == "key":
                if not setting_[1] in keys: return [False,i]
            if cd[setting_[0]] == "multiKey":
                for _ in setting_[1].split():
                    if not _ in keys: return [False,i]
            if setting_[0] == "Dir Path":
                if not os.path.isdir(setting_[1]): return [False,"{} , no directory.".fotmat(i)]
            if setting_[0] == "File Path":
                if not os.path.isfile(setting_[1]): return [False,"{} , no file.".fotmat(i)]
            if setting_[0] == "File Name":
                if setting_[1] == "" or None: return [False,"{} , no file name.".fotmat(i)]
            if cd[setting_[0]] == ["yes","no"]:
                if not setting_[1] in ["yes","no"]: return [False,i]
           
                    
            if i+j+2 == len(action):
                return [True]
            j+=1
    
    def run(self):
        for action in self._actions:
            if not self._running:
                self.sbMessage.emit(["Program stopped.",4000])
                self.finished.emit()
                break
            if action[0] ==  "Delay":
                delay = int(action[2])
                sleep(delay/1000)
# =============================================================================
#                 loop = QEventLoop()
#                 QTimer.singleShot(delay, loop.quit)
#                 loop.exec_()
# =============================================================================
                ##ÿQTest.qWait(delay)
                
            # MOUSE
            if action[0] ==  "Move To":
                x,y,duration = int(action[2]),int(action[4]),float(action[6])
                pyautogui.moveTo(x,y,duration)
            if action[0] ==  "Move Relative":
                x,y,duration = int(action[2]),int(action[4]),float(action[6])
                pyautogui.moveRel(x,y,duration)
            if action[0] ==  "Drag To":
                x,y,duration = int(action[2]),int(action[4]),float(action[6])
                pyautogui.dragTo(x,y,duration)
            if action[0] ==  "Drag Relative":
                x,y,duration = int(action[2]),int(action[4]),float(action[6])
                pyautogui.dragRel(x,y,duration)
            if action[0] ==  "Click To":
                x,y,button,clicks,interval,duration = int(action[2]),int(action[4]),action[6],int(action[8]),float(action[10]),float(action[12])
                pyautogui.click(x=x,y=y,button=button,clicks=clicks,interval=interval,duration=duration)
            if action[0] ==  "Click":
                button,clicks,interval,duration = action[2],int(action[4]),float(action[6]),float(action[8])
                pyautogui.click(button=button,clicks=clicks,interval=interval,duration=duration)
            if action[0] ==  "Scroll":
                clicks = int(action[2])
                pyautogui.scroll(clicks=clicks)
                
            # KEYBOARD 
            if action[0] ==  "Write":
                interval,text = float(action[2]),action[4]
                pyautogui.typewrite(text,interval=interval)
            if action[0] ==  "Press":
                presses,interval,text = int(action[2]),float(action[4]),action[6]
                pyautogui.press(text,interval=interval,presses=presses)
            if action[0] ==  "Hotkey":
                hotkey = action[2].split()
                pyautogui.hotkey(*hotkey)
            if action[0] ==  "Key Down":
                hotkey = action[2]
                pyautogui.keyDown(hotkey)
            if action[0] ==  "Key Up":
                hotkey = action[2]
                pyautogui.keyUp(hotkey)
                
            # SCREEN
            if action[0] ==  "Screenshot":
                overwrite,dir_path,file_name = action[2],action[4],action[6]
                if overwrite == "yes":
                    path = os.path.join(dir_path,file_name)+".png"
                    pyautogui.screenshot(path)
                if overwrite == "no":
                    path = os.path.join(dir_path,file_name)
                    path = self.notOverwrite(path)
                    pyautogui.screenshot(path)
                    
            if action[0] ==  "Find Image":
                cb1,cb2,cb3,wait,path = action[2],action[4],action[6],float(action[8]),action[10]
                
                if cb1 == "yes":
                    while self._running:
                        a = None
                        try:
                            if cb3:
                                a = pyautogui.locateCenterOnScreen(path,grayscale=True)
                            else:
                                a = pyautogui.locateCenterOnScreen(path)
                        except:pass
                        if a:
                             break
                        sleep(wait)
                    if cb2 == "yes" and a:
                         pyautogui.click(a[0],a[1])
                if cb1 == "no":
                    a = None
                    try:
                        if cb3:
                            a = pyautogui.locateCenterOnScreen(path,grayscale=True)
                        else:
                            a = pyautogui.locateCenterOnScreen(path)
                    except:pass
                if cb2 == "yes" and a:
                    pyautogui.click(a[0],a[1])
    
    @pyqtSlot()
    def start(self,steps,actions,loop):
        self._step = 0
        self._running = True
        self._maxSteps = steps
        self._actions = actions
        
        for i,action in enumerate(self._actions):
            c = self.control(action)
            if c[0] == False:
                self.sbMessage.emit(["Error at {},{}".format(i+1,c[1]),5000])
                self._running == False
                
        if loop == False:
            while self._step  < self._maxSteps  and self._running == True:
                self._step += 1
                self.sbMessage.emit(["Running... {}".format(self._step)])
                self.run()
                
        if loop == True:
            while self._running == True:
                self._step += 1
                self.sbMessage.emit(["Running... {}".format(self._step)])
                self.run()
            
        if self._running == True:
            self.sbMessage.emit(["Successfully end.",4000])
            self.finished.emit()
        else: 
            self.sbMessage.emit(["Program stopped.",4000])
            self.finished.emit()

    def stop(self):
        self.finished.emit()
        self._running = False
        
    def notOverwrite(self,path):
        if not os.path.isfile(path+".png"):
            return path+".png"
        
        for i in range(1,100000):
            path2 = path+"({})".format(i)
            if not os.path.isfile(path2+".png"):
                return path2+".png"

