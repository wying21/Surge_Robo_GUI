import time
import threading
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QTextCursor

class jump_worker(QObject):
    jump_sig  = Signal(QTextCursor)
    send_char_sig = Signal(str)
    erro_sig = Signal()
    def sendCursor(self, Cursor):
        self.jump_sig.emit(Cursor)
    def sendChar(self, char):
        self.send_char_sig.emit(char)


class read_thr(threading.Thread):
    """串口调试助手的收信线程"""
    def __init__(self, robot, portDialog):
        threading.Thread.__init__(self)
        self.isRunning = False
        self.show  = False
        self.robot = robot
        self.ser = robot.ser
        self.worker = jump_worker()
        self.portDialog = portDialog
        self.cursor = portDialog.recv_Text.textCursor()
    
    def jump_to_last_line(self):
        if self.portDialog.AutoLast.isChecked():
            try:
                self.worker.sendCursor(self.cursor)
            except:
                pass
    
    def run(self):
        temp = b""
        self.isRunning = True
        while self.isRunning:
            if self.ser.isOpen() and self.show:
                self.robot.read_lock.acquire()
                try:
                    text = self.ser.read()
                except:
                    self.worker.erro_sig.emit()
                self.robot.read_lock.release()
                if text:
                    temp += text
                    try:  # 解决汉字等二进制转换的问题
                        decode_str = temp.decode(encoding="utf-8")
                        for k, i in enumerate(decode_str):
                            if i in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0e\x0f":
                                decode_str = decode_str[:k] + "\\x" + temp[k:k+1].hex() + decode_str[k+1:]
                        self.worker.sendChar(decode_str)
                        temp = b""
                    except BaseException as e:
                        if len(temp) > 5:
                            # self.worker.sendChar(temp.decode(encoding="utf-8", errors="replace"))
                            decode_str = ""
                            for i in temp:
                                decode_str += "\\x" + temp.hex()
                            self.worker.sendChar(decode_str)
                            
                            temp = b""
                    self.jump_to_last_line()               
            time.sleep(0.001)
        print("串口打印线程被终止")
