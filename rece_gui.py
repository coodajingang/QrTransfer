from collections import deque
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QLineEdit, QDialog, QPushButton, QSpinBox, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, QTextEdit, QGridLayout, QMessageBox
from PyQt5.QtCore import QTimer, QRect, QPoint, Qt
from data_transfer import send_file
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QPen, QCursor, QImage
import threading
import cv2
import numpy as np
import pyautogui
import time
import os
from queue import Queue
import pyautogui  # 用于截屏
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QPainter, QPen, QColor
from qr_recognizer import recognize_qr_code, parse_qr_data, recognize_qr_code_for_reader_param
from selection import SelectionArea
import zlib
from file_handler import decompress_data
from recognition_thread import RecognitionThread
from param_qr import TransferParams
import pyperclip
import json

from timed_deque import TimedDeque

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("二维码数据接收系统")
        self.setGeometry(100, 100, 800, 600)
        self.pre_size = 120 # 二维码预览框的大小 

        # 创建主布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # 文件存储路径
        self.file_path_label = QLabel("文件存储路径:")
        self.file_path_input = QLineEdit()
        self.browse_button = QPushButton("浏览")
        self.browse_button.clicked.connect(self.browse_file)

        # 分段数设置
        self.segment_count_label = QLabel("文件总分段数:")
        self.segment_count_input = QSpinBox()
        self.segment_count_input.setMinimum(1)
        self.segment_count_input.setMaximum(999999)
        self.segment_count_input.setValue(200)
        self.segment_count_input.valueChanged.connect(self.on_segment_size_changed)

        self.segment_size_label = QLabel("分段大小:")
        self.segment_size_input = QSpinBox()
        self.segment_size_input.setMinimum(1)
        self.segment_size_input.setMaximum(999999)
        self.segment_size_input.setValue(200)

        # 二维码选择框 rect 数据  
        self.monitor_qr_label = QLabel()
        self.monitor_qr_label.setText("x/y/width/height")
        # self.qr_rect_x = 0
        # self.qr_rect_y = 0
        # self.qr_rect_width = 0
        # self.qr_rect_height = 0 

        self.qr_rect_x_input = QSpinBox()
        self.qr_rect_x_input.setMinimum(1)
        self.qr_rect_x_input.setMaximum(999999)
        self.qr_rect_x_input.setValue(100)
        self.qr_rect_y_input = QSpinBox()
        self.qr_rect_y_input.setMinimum(1)
        self.qr_rect_y_input.setMaximum(999999)
        self.qr_rect_y_input.setValue(100)
        self.qr_rect_width_input = QSpinBox()
        self.qr_rect_width_input.setMinimum(1)
        self.qr_rect_width_input.setMaximum(999999)
        self.qr_rect_width_input.setValue(300)
        self.qr_rect_height_input = QSpinBox()
        self.qr_rect_height_input.setMinimum(1)
        self.qr_rect_height_input.setMaximum(999999)
        self.qr_rect_height_input.setValue(300)

        hbox = QHBoxLayout()
        hbox.addWidget(self.monitor_qr_label)
        hbox.addWidget(self.qr_rect_x_input)
        hbox.addWidget(self.qr_rect_y_input)
        hbox.addWidget(self.qr_rect_width_input)
        hbox.addWidget(self.qr_rect_height_input)
        #hbox.addWidget(self.monitor_qr_btn)

        # action hbox 
        self.monitor_qr_process_label = QLabel()
        self.monitor_qr_process_label.setText("-/-")
        self.monitor_qr_range_label = QLabel()
        self.monitor_qr_range_label.setText("[:]")
        action_hbox = QHBoxLayout() 
        #action_hbox.addWidget(self.monitor_qr_range_label)
        #action_hbox.addWidget(self.monitor_qr_process_label)

        # preview label
        self.monitor_qr_preview_label = QLabel()

        # 二维码扫描总数和进度
        self.qr1_total = 0
        self.qr2_total = 0
        self.qr3_total = 0
        self.qr4_total = 0
        self.qr_process = 0
        self.qr1_process = 0
        self.qr2_process = 0
        self.qr3_process = 0
        self.qr4_process = 0

        
        self.monitor_qr1_process_label = QLabel()
        self.monitor_qr2_process_label = QLabel()
        self.monitor_qr3_process_label = QLabel()
        self.monitor_qr4_process_label = QLabel()
        self.monitor_qr1_process_label.setText("-/-")
        self.monitor_qr2_process_label.setText("-/-")
        self.monitor_qr3_process_label.setText("-/-")
        self.monitor_qr4_process_label.setText("-/-")

        process_vbox = QVBoxLayout()
        process_vbox.addWidget(self.monitor_qr1_process_label)
        process_vbox.addWidget(self.monitor_qr2_process_label)
        process_vbox.addWidget(self.monitor_qr3_process_label)
        process_vbox.addWidget(self.monitor_qr4_process_label)

        self.monitor_qr1_range_label = QLabel()
        self.monitor_qr2_range_label = QLabel()
        self.monitor_qr3_range_label = QLabel()
        self.monitor_qr4_range_label = QLabel()
        self.monitor_qr1_range_label.setText("[:]")
        self.monitor_qr2_range_label.setText("[:]")
        self.monitor_qr3_range_label.setText("[:]")
        self.monitor_qr4_range_label.setText("[:]")
        range_vbox = QVBoxLayout()
        range_vbox.addWidget(self.monitor_qr1_range_label)
        range_vbox.addWidget(self.monitor_qr2_range_label)
        range_vbox.addWidget(self.monitor_qr3_range_label)
        range_vbox.addWidget(self.monitor_qr4_range_label)

        self.detail_qr1_btn = QPushButton("进度详情")
        self.detail_qr2_btn = QPushButton("进度详情")
        self.detail_qr3_btn = QPushButton("进度详情")
        self.detail_qr4_btn = QPushButton("进度详情")
        self.detail_qr1_btn.clicked.connect(self.show_qr1_process_detail)
        self.detail_qr2_btn.clicked.connect(self.show_qr2_process_detail)
        self.detail_qr3_btn.clicked.connect(self.show_qr3_process_detail)
        self.detail_qr4_btn.clicked.connect(self.show_qr4_process_detail)
        detail_vbox = QVBoxLayout()
        detail_vbox.addWidget(self.detail_qr1_btn)
        detail_vbox.addWidget(self.detail_qr2_btn)
        detail_vbox.addWidget(self.detail_qr3_btn)
        detail_vbox.addWidget(self.detail_qr4_btn)

        preview_hbox = QHBoxLayout() 
        preview_hbox.addWidget(self.monitor_qr_preview_label)
        preview_hbox.addLayout(range_vbox)
        preview_hbox.addLayout(process_vbox)
        preview_hbox.addLayout(detail_vbox)


        # 开始和暂停按钮
        self.start_button = QPushButton("3.开始")
        self.start_button.clicked.connect(self.start_recognition)
        self.pause_button = QPushButton("暂停")
        self.pause_button.clicked.connect(self.pause_recognition)
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_recognition)
        self.read_sender_param_button = QPushButton("1.读取发送者参数")
        self.read_sender_param_button.clicked.connect(self.read_sender_params_area)

        self.monitor_qr_btn = QPushButton("2.选择二维码框")
        self.monitor_qr_btn.clicked.connect(self.select_qr_area)  

        # vbox_btn = QVBoxLayout()
        action_hbox.addWidget(self.read_sender_param_button)
        action_hbox.addWidget(self.monitor_qr_btn)
        action_hbox.addWidget(self.start_button)
        action_hbox.addWidget(self.pause_button)
        action_hbox.addWidget(self.stop_button)
        # vbox_btn.addWidget(self.stop_button)
        # vbox_btn.addWidget(self.pause_button)
        # vbox_btn.addWidget(self.start_button)

        #preview_hbox.addLayout(vbox_btn)

        # 添加帧率设置
        self.frame_rate_label = QLabel("帧率:")
        self.frame_rate_input = QSpinBox()
        self.frame_rate_input.setMinimum(1)
        self.frame_rate_input.setMaximum(100)
        self.frame_rate_input.setValue(30)  # 默认30帧

        # 线程控制变量
        self.recognition_threads = {}  # 使用字典存储线程
        self.is_running = False
        self.is_paused = False
        self.collected_data = {}
        self.data_lock = threading.Lock()

        # 需要禁用的控件列表
        self.control_widgets = [
            self.file_path_input,
            self.browse_button,
            self.segment_count_input,
            self.frame_rate_input,
            self.monitor_qr_btn,
            self.qr_rect_x_input,
            self.qr_rect_y_input,
            self.qr_rect_width_input,
            self.qr_rect_height_input,
            self.read_sender_param_button,
            self.segment_size_input
        ]

        # 布局设置
        self.layout = QGridLayout(self.central_widget)
        self.layout.addWidget(self.file_path_label, 0, 0)
        self.layout.addWidget(self.file_path_input, 0, 1)
        self.layout.addWidget(self.browse_button, 0, 2)
        self.layout.addWidget(self.segment_count_label, 1, 0)
        self.layout.addWidget(self.segment_count_input, 1, 1)
        self.layout.addWidget(self.segment_size_label, 2, 0)
        self.layout.addWidget(self.segment_size_input, 2, 1)
        self.layout.addWidget(self.frame_rate_label, 3, 0)
        self.layout.addWidget(self.frame_rate_input, 3, 1)
        self.layout.addLayout(hbox, 4, 0, 1, 3)
        self.layout.addLayout(action_hbox, 5, 0, 1, 3)
        self.layout.addLayout(preview_hbox, 6, 0, 1, 3)
        #self.layout.addLayout(hbox_btn, 5, 0, 1, 3)
        self.layout.addWidget(self.log_area, 7, 0, 1, 3)

        self.monitoring = False  # 监测状态
        #self.update_qr_process()

        # 设置预览标签的大小和样式
        preview_size = QSize(self.pre_size, self.pre_size)
        preview_style = """
            QLabel {
                border: 1px solid #cccccc;
                background-color: #f0f0f0;
            }
        """
        
        for label in [self.monitor_qr_preview_label]:
            label.setMinimumSize(preview_size)
            label.setMaximumSize(preview_size)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(preview_style)

        self.screenshot_queue = Queue()
        self.collected_data = {}  # 存储收集到的数据
        self.total_segments = 0   # 总分段数
        self.qrcode_count = 0 # 二维码个数 
        self.chunk_ranges = [] # 二维码索引分段 [[0, 81], [81, 162], [162, 243], [243, 325]]
        self.collected_qr1 = {}
        self.collected_qr2 = {}
        self.collected_qr3 = {}
        self.collected_qr4 = {}
        self.screenshot_timer = QTimer()
        self.screenshot_timer.timeout.connect(self.capture_screen)

        # 添加剪贴板同步 
        self.write_clipboard_timer = QTimer()
        self.write_clipboard_timer.timeout.connect(self.write_clipboard)

        # 初始化最近收集item队列 
        self.timed_deque = TimedDeque(max_age_seconds=30)

        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.addPermanentWidget(self.monitor_qr_process_label)
        self.status_bar.addPermanentWidget(self.monitor_qr_range_label)
        self.speed_label = QLabel("采集速度: 0 pices/s")
        self.status_bar.addPermanentWidget(self.speed_label)

        self.send_feedback_label = QLabel("")
        self.status_bar.addPermanentWidget(self.send_feedback_label)
        self.status_bar_progress_label = QLabel("")
        self.status_bar.addPermanentWidget(self.status_bar_progress_label)

        # 速度计算
        self.last_second_item_count = 0
        self.speed_update_timer = QTimer()
        self.speed_update_timer.timeout.connect(self.update_speed_status)


        
        
    def update_speed_status(self):
        speed = self.qr_process - self.last_second_item_count
        self.last_second_item_count = self.qr_process 
        self.speed_label.setText(f"采集速度: {speed} pices/s")
        self.log_message(f"采集速度: {speed} pices/s {self.last_second_item_count}")

    # 将以扫描内容写入剪贴板 
    def write_clipboard(self): 
        # pack the data into a dict 
        packed_data = {}
        # packed_data["qr1"] = self.collected_qr1
        # packed_data["qr2"] = self.collected_qr2
        # packed_data["qr3"] = self.collected_qr3
        # packed_data["qr4"] = self.collected_qr4
        packed_data["qr"] = self.timed_deque.get_items()

        total = self.total_segments
        pct = 0.0
        if total > 0:
            pct = self.qr_process / float(total)
            self.status_bar_progress_label.setText(f"已扫描条数: {self.qr_process} / {total}, 百分比: {pct:.2%}")
        else:
            self.status_bar_progress_label.setText(f"已扫描条数: {self.qr_process} / {total}")

        if pct > 0.97:
            self.log_message("开始收集未扫描到的索引通知sender")
            packed_data["un_qr1"] = self.uncollected_ranges(0, self.collected_qr1)
            packed_data["un_qr2"] = self.uncollected_ranges(1, self.collected_qr2)
            packed_data["un_qr3"] = self.uncollected_ranges(2, self.collected_qr3)
            packed_data["un_qr4"] = self.uncollected_ranges(3, self.collected_qr4)
            self.send_feedback_label.setText("开始收集未扫描到的索引通知sender")

        data = json.dumps(packed_data)
        pyperclip.copy("QRTRANSFER:" + data)
        self.log_message(f"已将数据写入剪贴板: {data}")

    # 更新二维码识别进度 
    def update_qr_process(self):  
        if (self.qr_process >= 0): 
            self.monitor_qr_process_label.setText(f"{self.qr_process}")
        if (self.qr1_process >= 0): 
            self.monitor_qr1_process_label.setText(f"{self.qr1_process}")
        if (self.qr2_process >= 0): 
            self.monitor_qr2_process_label.setText(f"{self.qr2_process}")
        if (self.qr3_process >= 0): 
            self.monitor_qr3_process_label.setText(f"{self.qr3_process}")
        if (self.qr4_process >= 0): 
            self.monitor_qr4_process_label.setText(f"{self.qr4_process}")
        return 
        self.recalculate_total(self.segment_count_input.value())
        if (self.qr1_rect): 
            self.monitor_qr1_process_label.setText(f"{self.qr1_process}/{self.qr1_total}")
        else: 
            self.monitor_qr1_process_label.setText("-/-")
        if (self.qr2_rect):         
            self.monitor_qr2_process_label.setText(f"{self.qr2_process}/{self.qr2_total}")
        else: 
            self.monitor_qr2_process_label.setText("-/-")
        if (self.qr3_rect): 
            self.monitor_qr3_process_label.setText(f"{self.qr3_process}/{self.qr3_total}")
        else: 
            self.monitor_qr3_process_label.setText("-/-")
        if (self.qr4_rect):
            self.monitor_qr4_process_label.setText(f"{self.qr4_process}/{self.qr4_total}")
        else: 
            self.monitor_qr4_process_label.setText("-/-")

    def on_segment_size_changed(self, value): 
        #self.update_qr_process()
        pass

    # 调整分段数处理函数 即文件总分段数 
    def recalculate_total(self, value): 
        total = 0 
        if (self.qr1_rect): 
            total += 1
        if (self.qr2_rect): 
            total += 1      
        if (self.qr3_rect): 
            total += 1
        if (self.qr4_rect): 
            total += 1 
        if (total == 0):
            return 
        size = value // total 
        lastSize = value - (size * (total-1)) 
        # set last one 
        lastIdx = 4 
        if (self.qr4_rect): 
            lastIdx = 4 
            self.qr4_total = lastSize 
        elif (self.qr3_rect): 
            lastIdx = 3 
            self.qr3_total = lastSize 
        elif (self.qr2_rect): 
            lastIdx = 2 
            self.qr2_total = lastSize 
        elif (self.qr1_rect): 
            lastIdx = 1 
            self.qr1_total = lastSize            
        # set other's  
        for i in range(lastIdx): 
            if (i == 1 and self.qr1_rect): 
                self.qr1_total = size 
            elif (i == 2 and self.qr2_rect): 
                self.qr2_total = size 
            elif (i == 3 and self.qr3_rect): 
                self.qr3_total = size 
            elif (i == 4 and self.qr4_rect): 
                self.qr4_total = size               
    # 
        
    def read_sender_params_area(self): 
        self.log_area.append("读取发送者参数二维码...")
        current_screen = self.screen()
        self.selection_area = SelectionArea(self, "reader_param")
        self.selection_area.setGeometry(current_screen.geometry())
        self.selection_area.show()
        self.selection_area.raise_()
        self.selection_area.activateWindow()

    def select_qr_area(self): 
        self.log_area.append("请框选二维码区域...")
        current_screen = self.screen()
        self.selection_area = SelectionArea(self, "1")
        self.selection_area.setGeometry(current_screen.geometry())
        self.selection_area.show()
        self.selection_area.raise_()
        self.selection_area.activateWindow()


    def browse_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "选择文件存储路径", "", "All Files (*)")
        if file_path:
            self.file_path_input.setText(file_path)

    def show_alert(self, title, message, icon=QMessageBox.Icon.Information):
        """
        显示一个消息框
        :param title: 消息框标题
        :param message: 消息内容
        :param icon: 消息框图标类型，默认为信息图标
        """
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    def check_can_start(self): 
        if not self.file_path_input.text():
            self.show_alert("错误", "请选择文件存储路径", QMessageBox.Icon.Warning)
            return False
        
        if self.segment_count_input.value() <= 0:
            self.show_alert("错误", "文件分段数必须大于0", QMessageBox.Icon.Warning)
            return False
            
        # if not (self.qr1_rect or self.qr2_rect or self.qr3_rect or self.qr4_rect):
        #     self.show_alert("错误", "请至少选择一个二维码监控区域", QMessageBox.Icon.Warning)
        #     return False
            
        return True

    def toggle_controls(self, enabled):
        """启用或禁用控件"""
        for widget in self.control_widgets:
            widget.setEnabled(enabled)

    def start_recognition(self):
        if not self.check_can_start():
            return
            
        # 清理旧数据
        self.collected_data.clear()
        self.collected_qr1.clear()
        self.collected_qr2.clear()
        self.collected_qr3.clear()
        self.collected_qr4.clear()
        self.qr1_total = 0
        self.qr2_total = 0
        self.qr3_total = 0
        self.qr4_total = 0
        self.qr_process = 0
        self.qr1_process = 0
        self.qr2_process = 0
        self.qr3_process = 0
        self.qr4_process = 0
        self.last_second_item_count = 0
        self.total_segments = self.segment_count_input.value()
        self.qr1_total = self.total_segments

        # 检查设置参数，通过手动输入或者通过扫描发送者参数获得 ， self.chunk_ranges qrcode_count
        # 若是通过扫描二维码得到 这俩参数有值 
        # 若是手工输入参数， 需要识别数据后才能获取 
        self.update_chunk_ranges()
        
        # 创建并启动识别线程
        self.recognition_thread = RecognitionThread(self.screenshot_queue)
        self.recognition_thread.data_recognized.connect(self.on_data_recognized)
        self.recognition_thread.error_occurred.connect(self.on_error_occurred)
        self.recognition_thread.qrcode_count_signal.connect(self.on_qrcode_count_occurred)
        self.recognition_thread.start()
        
        # 启动截图定时器
        interval = int(1000 / self.frame_rate_input.value())
        self.screenshot_timer.setInterval(interval)
        self.screenshot_timer.start()

        # 启动速度计算定时器
        self.speed_update_timer.setInterval(1000)  # 每秒更新
        self.speed_update_timer.start()  # 每秒更新
        
        # 禁用控件
        self.toggle_controls(False)
        self.log_message("开始识别...")

        self.write_clipboard_timer.setInterval(5000)  # 每秒写入一次剪贴板
        self.write_clipboard_timer.start()
        self.log_message("启动剪贴板同步...")



    def on_error_occurred(self, msg): 
        self.log_message(msg)
    def on_qrcode_count_occurred(self, count): 
        if (self.qrcode_count  == 0):
            self.qrcode_count = count
        if (len(self.chunk_ranges) == 0): 
            # split index 
            for i in range(self.qrcode_count):
                start_idx = i * self.segment_size_input.value()
                end_idx = min((i + 1) * self.segment_size_input.value(), self.segment_count_input.value())
                self.chunk_ranges.append([start_idx, end_idx])
            self.update_chunk_ranges()

    def update_chunk_ranges(self): 
        self.monitor_qr_range_label.setText(f"总共 [0:{self.segment_count_input.value() - 1}]")
        if (self.qrcode_count == 0 or len(self.chunk_ranges) == 0):
            return
        for index in range(self.qrcode_count): 
            if (index == 0):
                self.monitor_qr1_range_label.setText(f"分段 [{self.chunk_ranges[0]}]")
            elif (index == 1):
                self.monitor_qr2_range_label.setText(f"分段 [{self.chunk_ranges[1]}]")
            elif (index == 2):
                self.monitor_qr3_range_label.setText(f"分段 [{self.chunk_ranges[2]}]")
            elif (index == 3):
                self.monitor_qr4_range_label.setText(f"分段 [{self.chunk_ranges[3]}]")

    def capture_screen(self):
        """捕获屏幕区域"""
        try:
            # 计算需要截取的总区域
            x, y, width, height = self.qr_rect_x_input.value(), self.qr_rect_y_input.value(), self.qr_rect_width_input.value(), self.qr_rect_height_input.value()
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot_np = np.array(screenshot)
            
            # 发送到识别线程
            self.screenshot_queue.put(screenshot_np)
            
            # 更新预览
            self.update_preview(screenshot_np)
            
        except Exception as e:
            self.log_message(f"截图错误: {str(e)}")
    
    def update_preview(self, image):
        # 暂时不更新预览
        pass
    

    def on_data_recognized(self, index, data_content):
        """处理识别到的数据"""
        if index not in self.collected_data:
            self.collected_data[index] = data_content
            self.log_message(f"识别到数据片段 {index}")
            
            # 更新总体进度
            progress = len(self.collected_data)
            self.qr_process = progress
            
            self.timed_deque.append(index)  # 添加到最近收集的队列

            # 根据index判断属于哪个区间，更新对应的进度
            if self.chunk_ranges:
                for i, (start, end) in enumerate(self.chunk_ranges):
                    if start <= index < end:
                        # 计算该区间已识别的数据量
                        if i == 0:
                            self.qr1_process += 1
                            self.collected_qr1[index] = index
                        elif i == 1:
                            self.qr2_process += 1
                            self.collected_qr2[index] = index
                        elif i == 2:
                            self.qr3_process += 1
                            self.collected_qr3[index] = index
                        elif i == 3:
                            self.qr4_process += 1
                            self.collected_qr4[index] = index
                        break
            
            self.update_qr_process()
            
            # 检查是否完成
            if progress >= self.total_segments:
                self.complete_recognition()

    def complete_recognition(self):
        """完成识别处理"""
        self.screenshot_timer.stop()
        self.write_clipboard_timer.stop()
        self.speed_update_timer.stop()
        self.recognition_thread.stop()
        self.recognition_thread.wait()
        
        # 处理收集到的数据
        self.process_collected_data()

        
        # 恢复控件状态
        self.toggle_controls(True)
        self.log_message("识别完成")
        self.status_bar_progress_label.setText(f"已扫描条数: {self.qr_process} / {self.qr_process}, 百分比: 100%")
        self.send_feedback_label.setText("")


    def process_collected_data(self):
        """处理收集到的数据片段并写入文件"""
        try:
            # 检查是否有收集到数据
            if not self.collected_data:
                self.log_message("没有收集到任何数据")
                return

            # 检查是否所有片段都已收集
            if len(self.collected_data) < self.total_segments:
                self.log_message(f"数据不完整: 已收集 {len(self.collected_data)}/{self.total_segments} 个片段")
                return

            # 按索引排序并合并数据
            merged_data = bytearray()
            for i in range(self.total_segments):
                if i not in self.collected_data:
                    self.log_message(f"缺少片段 {i}")
                    return
                merged_data.extend(self.collected_data[i])

            # 解压缩数据
            try:
                decompressed_data = zlib.decompress(merged_data)
            except zlib.error as e:
                self.log_message(f"数据解压缩失败: {str(e)}")
                return

            # 写入文件
            file_path = self.file_path_input.text()
            # 获取文件所在目录路径
            directory = os.path.dirname(file_path)
            
            # 如果目录不存在，创建目录
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(decompressed_data)

            self.log_message(f"文件已成功保存到: {file_path}")
            self.show_alert("成功", "文件接收完成", QMessageBox.Icon.Information)

        except Exception as e:
            self.log_message(f"处理数据时出错: {str(e)}")
            self.show_alert("错误", f"处理数据时出错: {str(e)}", QMessageBox.Icon.Critical)

    def log_message(self, message):
        """在日志区域输出消息"""
        self.log_area.append(message)  # 将消息添加到日志区域

    def stop_recognition(self):
        """停止识别"""
        self.screenshot_timer.stop()
        self.write_clipboard_timer.stop()
        self.speed_update_timer.stop()
        self.collected_data.clear()
        self.collected_qr1.clear()
        self.collected_qr2.clear()
        self.collected_qr3.clear()
        self.collected_qr4.clear()
        if hasattr(self, 'recognition_thread'):
            self.recognition_thread.stop()
            self.recognition_thread.wait()
        self.toggle_controls(True)
        self.log_message("停止识别")

    def pause_recognition(self):
        """暂停/继续识别"""
        if self.screenshot_timer.isActive():
            self.screenshot_timer.stop()
            self.pause_button.setText("继续")
        else:
            self.screenshot_timer.start()
            self.pause_button.setText("暂停")

        if self.write_clipboard_timer.isActive(): 
            self.write_clipboard_timer.stop()
        else: 
            self.write_clipboard_timer.start()

        if self.speed_update_timer.isActive(): 
            self.speed_update_timer.stop()
        else: 
            self.speed_update_timer.start()

    def monitor_qr_area(self):
        self.log_area.append("请框选二维码区域...")
        current_screen = self.screen()
        self.selection_area = SelectionArea(self)
        #self.selection_area.showFullScreen()  # 全屏显示选择区域
        # 设置选择区域窗口的位置为当前屏幕
        self.selection_area.setGeometry(current_screen.geometry())
        self.selection_area.show()
        self.selection_area.raise_()
        self.selection_area.activateWindow()

    def set_selection(self, rect, area_idx):
        x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
        self.log_area.append(f"选择的区域:{area_idx} = ({x}, {y}, {width}, {height})") 
        if (area_idx == "reader_param"):
            self.log_area.append("开始读取发送者二维码参数")
            QTimer.singleShot(200, lambda: self.capture_screenshot_for_reader_param(x, y, width, height))
            return 
        self.qr_rect_x_input.setValue(x)
        self.qr_rect_y_input.setValue(y)
        self.qr_rect_width_input.setValue(width)
        self.qr_rect_height_input.setValue(height)
        if width <= 0 or height <= 0:
            print("Invalid selection area")
            self.log_message("Invalid selection area")
            return
        
        # 使用QTimer延迟截图，给系统一些时间清除选择窗口
        QTimer.singleShot(200, lambda: self.capture_screenshot(x, y, width, height))

    def capture_screenshot_for_reader_param(self, x, y, width, height):
        try:
            print(f"开始截图: x={x}, y={y}, width={width}, height={height}")
            # 捕获选定区域的截图
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            # 转换为OpenCV格式
            screenshot_np = np.array(screenshot)
            
            if screenshot_np.size == 0:
                print("Screenshot is empty")
                self.log_message("Screenshot is empty")
                return
            
            data = recognize_qr_code_for_reader_param(screenshot_np) 
            if (data): 
                self.log_area.append(f"读取发送者参数 结果{data}") 
                self.frame_rate_input.setValue(data.frame_rate)
                self.segment_count_input.setValue(data.total_chunks)
                self.file_path_input.setText(os.path.join(os.getcwd(), data.filename))
                self.total_segments = data.total_chunks
                self.chunk_ranges = data.chunk_ranges
                self.segment_size_input.setValue(data.chunks_size)
                self.qrcode_count = data.qr_count
            else: 
                self.log_area.append("读取发送者参数异常，读取为空")
        except Exception as e:
            print(f"截图错误: {str(e)}")

    def capture_screenshot(self, x, y, width, height):
        try:
            print(f"开始截图: x={x}, y={y}, width={width}, height={height}")
            # 捕获选定区域的截图
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            # 转换为OpenCV格式
            screenshot_np = np.array(screenshot)
            
            if screenshot_np.size == 0:
                print("Screenshot is empty")
                self.log_message("Screenshot is empty")
                return
            
            # 转换颜色空间 (BGR to RGB)
            screenshot_rgb = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)  # 修改这里
            
            # 创建QImage
            height, width = screenshot_rgb.shape[:2]
            bytes_per_line = 3 * width
            q_img = QImage(screenshot_rgb.data, width, height, bytes_per_line, 
                          QImage.Format.Format_RGB888)
                      
            # 创建并缩放QPixmap
            pixmap = QPixmap.fromImage(q_img)
            scaled_pixmap = pixmap.scaled(
                QSize(self.pre_size, self.pre_size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 设置预览图像
            self.monitor_qr_preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"截图错误: {str(e)}")

    def capture_and_recognize(self, x, y, width, height):
        while self.monitoring:
            # 截取屏幕
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

            # 识别二维码
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector(screenshot_gray)

            if data:
                self.log_area.append(f"识别到二维码数据: {data}")

            # 暂停一段时间以避免过于频繁的截屏
            cv2.waitKey(1000)  # 每秒截取一次

    # 收集未扫描到的索引 
    def uncollected_ranges(self, range_idx, collected_ranges): 
        uncollected_ranges = []
        if range_idx >= len(self.chunk_ranges):
            return uncollected_ranges
        chunk_ranges = self.chunk_ranges[range_idx]
        if (not collected_ranges) or (not chunk_ranges):
            return uncollected_ranges
        if (len(collected_ranges) == 0) or (len(chunk_ranges) == 0):
            return uncollected_ranges

        start_idx = chunk_ranges[0]
        end_idx = chunk_ranges[1]
        for i in range(start_idx, end_idx): 
            if i not in collected_ranges: 
               uncollected_ranges.append(i)
        return uncollected_ranges

    def show_qr1_process_detail(self):
        self.show_process_detail_dialog("qr1", 0, self.collected_qr1)
    def show_qr2_process_detail(self):
        self.show_process_detail_dialog("qr2", 1, self.collected_qr2)
    def show_qr3_process_detail(self):
        self.show_process_detail_dialog("qr3", 2, self.collected_qr3)
    def show_qr4_process_detail(self):
        self.show_process_detail_dialog("qr4", 3, self.collected_qr4)
    def show_process_detail_dialog(self, title, range_idx, collected_ranges):
        self.log_message(f"显示进度详情 {range_idx} ")
        if range_idx >= len(self.chunk_ranges):
            self.log_message("不存在的chunk_range")
            return 
        chunk_ranges = self.chunk_ranges[range_idx]
        if (not collected_ranges) or (not chunk_ranges):
            self.log_message("chunk_ranges为空或者collected_ranges为空")
            return 
        if (len(collected_ranges) == 0) or (len(chunk_ranges) == 0):
            self.log_message("chunk_ranges为空或者collected_ranges为空")
            return 
        start_idx = chunk_ranges[0]
        end_idx = chunk_ranges[1]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"接收详情--{title}")
        #dialog.setGeometry(150, 150, 600, 400)
        log_layout = QVBoxLayout(dialog)

        # Create a text area to display logs
        display_area = QTextEdit(dialog)
        display_area.setReadOnly(True)  # Set to read-only
        log_layout.addWidget(display_area)

        # Populate the log display area with existing logs
        #display_area.setPlainText(self.log_area.toPlainText())  # Copy logs from the main log area
        display_area.append(f"已收集个数 {len(collected_ranges)}")
        display_area.append(f"范围：{start_idx} - {end_idx}")
        msg = ""
        count = 0 
        total_line = 0 
        for i in range(start_idx, end_idx): 
            if i not in collected_ranges: 
               count += 1
               msg += "  " + str(i)
            if count > 5:
                display_area.append(msg)
                msg = ""
                count = 0
                total_line += 1
            if total_line > 10:
                break
        display_area.append(msg)

        # Add a close button
        close_button = QPushButton("关闭", self)
        close_button.clicked.connect(dialog.close)  # Connect button to close the dialog
        log_layout.addWidget(close_button)
        dialog.setLayout(log_layout)
        dialog.exec()
