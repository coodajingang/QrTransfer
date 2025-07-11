import json
import pyperclip
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import traceback

class ReadClipboardThread(QThread):
    log_msg = pyqtSignal(str)

    def __init__(self, interval, collectedData, qr_pice_wrapper, feed_back_dqueue):
        super().__init__()
        self.interval = interval
        self.collectedData = collectedData
        self.qr_pice_wrapper = qr_pice_wrapper
        self.feed_back_dqueue = feed_back_dqueue


    def run(self):
        self.timer = QTimer()
        self.log_msg.emit("启动剪贴板同步线程")
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.do_work)
        self.timer.start()
        self.exec_()  # 启动事件循环，线程不会退出

    def stop(self):
        self.timer.stop()
        self.quit()
        self.wait()

    
    def do_work(self):
        try:
            # 从剪贴板读取数据
            clipboard_data = pyperclip.paste()
            #print(clipboard_data)
            if clipboard_data:
                # 尝试解析 JSON 数据
                if not clipboard_data.startswith("QRTRANSFER:"): 
                    return
                clipboard_data = clipboard_data.replace("QRTRANSFER:", "")
                data = json.loads(clipboard_data)
                self.collectedData.clear()
                self.collectedData.update(data)
                if "qr" in self.collectedData:
                    self.qr_pice_wrapper.clear_already_collected(self.collectedData["qr"])
                self.log_msg.emit(f"剪贴板数据已更新: {len(self.collectedData)} 个")
                # self.log_msg.emit(f"剪贴板数据已更新--qr2 : {self.collectedData["qr2"]}")
                # self.log_msg.emit(f"剪贴板数据已更新--qr3 : {self.collectedData["qr3"]}")
                # self.log_msg.emit(f"剪贴板数据已更新--qr4 : {self.collectedData["qr4"]}")
                if "un_qr1" in self.collectedData:
                    self.log_msg.emit(f"未扫描到的索引通知sender: {self.collectedData['un_qr1']}")
                    for i in self.collectedData['un_qr1']:
                        self.feed_back_dqueue.put(i)
                if "un_qr2" in self.collectedData:
                    self.log_msg.emit(f"未扫描到的索引通知sender: {self.collectedData['un_qr2']}")
                    for i in self.collectedData['un_qr2']:
                        self.feed_back_dqueue.put(i)
                if "un_qr3" in self.collectedData:
                    self.log_msg.emit(f"未扫描到的索引通知sender: {self.collectedData['un_qr3']}")
                    for i in self.collectedData['un_qr3']:
                        self.feed_back_dqueue.put(i)
                if "un_qr4" in self.collectedData:
                    self.log_msg.emit(f"未扫描到的索引通知sender: {self.collectedData['un_qr4']}")
                    for i in self.collectedData['un_qr4']:
                        self.feed_back_dqueue.put(i)

            else: 
                self.log_msg.emit("剪贴板没有数据")
        except json.JSONDecodeError:
            # 如果剪贴板数据不是有效的 JSON，忽略错误
            self.log_msg.emit("剪贴板数据不是有效的 JSON 格式")
        except Exception as e:
            traceback.print_exc()
            self.log_msg.emit(f"读取剪贴板时发生错误: {e}")
            # self.sleep(self.interval)
