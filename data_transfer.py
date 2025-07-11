# data_transfer.py
from file_handler import compress_file, split_data
from qr_generator import generate_qr_code
import zlib
import base64
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
from PIL.ImageQt import toqimage
import threading
from queue import Queue
import math
import time

class QRCodeGeneratorThread(QThread):
    def __init__(self, chunks, start_idx, end_idx, width, height, result_queue):
        super().__init__()
        self.chunks = chunks
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.width = width
        self.height = height
        self.result_queue = result_queue

    def run(self):
        for index in range(self.start_idx, self.end_idx):
            c = self.chunks[index]
            # 计算数据长度和 CRC32 校验码
            data_length = len(c)
            crc32_checksum = zlib.crc32(c)
            
            # 构建新的数据格式
            formatted_chunk = (
                index.to_bytes(4, byteorder='big') +  # 序号 (4字节)
                data_length.to_bytes(2, byteorder='big') +  # 数据长度 (2字节)
                c +  # 数据内容
                crc32_checksum.to_bytes(4, byteorder='big')  # CRC32 校验码 (4字节)
            )
            
            # 生成二维码并放入结果队列
            qr_code = QPixmap.fromImage(toqimage(generate_qr_code(
                base64.b64encode(formatted_chunk).decode('utf-8'),
                self.width, 
                self.height
            )))
            self.result_queue.put((index, qr_code))

class QRCodeGeneratorForFeedBack(QThread):
    progress_updated = pyqtSignal(str)  # 用于发送进度消息
    def __init__(self, chunks, queue, width, height, qr_pice_wrapper, stop_event):
        super().__init__()
        self.chunks = chunks
        self.queue = queue  # 用于接收生成的二维码
        self.width = width
        self.height = height
        self.qr_pice_wrapper = qr_pice_wrapper
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            if self.stop_event.is_set():
                return
            index = self.queue.get()
            if index < 0 or index >= len(self.chunks):
                self.progress_updated.emit(f"二维码补充生成 索引 {index} 超出范围，跳过")
                continue
            if self.qr_pice_wrapper.has_qr_code(index): 
                self.qr_pice_wrapper.update_ready_to_collecte_status(index)
                self.progress_updated.emit(f"二维码补充生成 索引 {index} 数据已存在，更新状态")
                return 
            c = self.chunks[index] 
            if not c:
                self.progress_updated.emit(f"二维码补充生成 索引 {index} 数据为空，不存在的数据分段，请检查！")
                raise ValueError(f"数据分段 {index} 为空，可能是数据不完整或已被删除。")
            
            # 计算数据长度和 CRC32 校验码
            data_length = len(c)
            crc32_checksum = zlib.crc32(c)
            
            # 构建新的数据格式
            formatted_chunk = (
                index.to_bytes(4, byteorder='big') +  # 序号 (4字节)
                data_length.to_bytes(2, byteorder='big') +  # 数据长度 (2字节)
                c +  # 数据内容
                crc32_checksum.to_bytes(4, byteorder='big')  # CRC32 校验码 (4字节)
            )
            
            # 生成二维码并放入结果队列
            qr_code = QPixmap.fromImage(toqimage(generate_qr_code(
                base64.b64encode(formatted_chunk).decode('utf-8'),
                self.width, 
                self.height
            )))
            self.qr_pice_wrapper.set_ready_to_collecte(index, qr_code) # [index] = qr_code 
            self.progress_updated.emit(f"二维码补充生成完成: {index}")


class QRCodeGeneratorThread2(QThread):
    def __init__(self, chunks, start_idx, end_idx, width, height, thread_id, qr_pice_wrapper, progress_updated, stop_event):
        super().__init__()
        self.chunks = chunks
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.width = width
        self.height = height
        self.thread_id = thread_id
        self.qr_pice_wrapper = qr_pice_wrapper
        self.progress_updated = progress_updated
        self.stop_event = stop_event  # 用于控制线程停止

    def run(self):
        total_len = self.end_idx - self.start_idx + 1
        complete_count = 0
        self.progress_updated.emit(f"启动线程 {self.thread_id}: 处理范围 {self.start_idx}-{self.end_idx}")
        for index in range(self.start_idx, self.end_idx):
            if self.stop_event.is_set():
                return 
            c = self.chunks[index]
            # 计算数据长度和 CRC32 校验码
            data_length = len(c)
            crc32_checksum = zlib.crc32(c)
            
            # 构建新的数据格式
            formatted_chunk = (
                index.to_bytes(4, byteorder='big') +  # 序号 (4字节)
                data_length.to_bytes(2, byteorder='big') +  # 数据长度 (2字节)
                c +  # 数据内容
                crc32_checksum.to_bytes(4, byteorder='big')  # CRC32 校验码 (4字节)
            )
            
            # 生成二维码并放入结果队列
            qr_code = QPixmap.fromImage(toqimage(generate_qr_code(
                base64.b64encode(formatted_chunk).decode('utf-8'),
                self.width, 
                self.height
            )))
            self.qr_pice_wrapper.update_qr_code(index, qr_code) # [index] = qr_code 
            complete_count += 1
            # 每处理10%的数据更新一次进度
            if complete_count % max(1, total_len // 10) == 0:
                progress = (complete_count / total_len) * 100
                self.progress_updated.emit(f"线程：{self.thread_id} 二维码生成进度: {progress:.1f}%")
        self.progress_updated.emit(f"线程：{self.thread_id} 二维码生成完成 {complete_count} / {total_len}")


class FileProcessThread(QThread):
    progress_updated = pyqtSignal(str)  # 用于发送进度消息

    def __init__(self, chunks, frame_rate, qr_count, data_chunk_size, width, height, thread_count, qr_pice_wrapper, stop_event):
        super().__init__()
        self.chunks = chunks
        self.frame_rate = frame_rate
        self.qr_count = qr_count
        self.data_chunk_size = data_chunk_size
        self.width = width
        self.height = height
        self.thread_count = thread_count
        self.running = True  # 添加控制标志
        self.qr_pice_wrapper = qr_pice_wrapper  # 用于收集数据的实例
        self.stop_event = stop_event  # 用于控制线程停止

    def stop(self):
        """停止线程"""
        self.running = False
        self.wait()  # 等待线程结束

    def run(self):
        try:
            # 开始计时
            total_start_time = time.time()
            
            if not self.running:
                return
            if self.stop_event.is_set():
                return

            # 开始生成二维码计时
            qr_gen_start_time = time.time()

            threads = []
            # 计算每个线程处理的块数
            chunks_per_thread = math.ceil(len(self.chunks) / self.thread_count)
            
            # 创建并启动线程
            for i in range(self.thread_count):
                if not self.running:
                    return
                if self.stop_event.is_set():
                    return
                start_idx = i * chunks_per_thread
                end_idx = min((i + 1) * chunks_per_thread, len(self.chunks))
                
                thread = QRCodeGeneratorThread2(
                    chunks=self.chunks,
                    start_idx=start_idx,
                    end_idx=end_idx,
                    width=self.width,
                    height=self.height,
                    thread_id = i + 1, 
                    qr_pice_wrapper = self.qr_pice_wrapper, 
                    progress_updated = self.progress_updated,
                    stop_event=self.stop_event
                )

                threads.append(thread)
                thread.start()

            # 如果线程被停止，提前退出
            if not self.running:
                return
            if self.stop_event.is_set():
                return
            # 等待所有线程完成
            for thread in threads:
                thread.wait()
            if self.stop_event.is_set():
                return
            # 计算耗时统计
            qr_gen_time = time.time() - qr_gen_start_time
            total_time = time.time() - total_start_time
            
            # 发送耗时统计信息
            self.progress_updated.emit("\n耗时统计:")
            self.progress_updated.emit(f"二维码生成耗时: {qr_gen_time:.2f}秒")
            self.progress_updated.emit(f"总耗时: {total_time:.2f}秒")
            self.progress_updated.emit(f"平均每个二维码生成耗时: {(qr_gen_time/len(self.chunks)*1000):.2f}毫秒")

        except Exception as e:
            self.progress_updated.emit(f"错误: {str(e)}")
        finally:
            if self.stop_event.is_set():
                return
            # 确保所有子线程都被清理
            for thread in threads:
                thread.quit()
                thread.wait()

def send_file(file_path, frame_rate, qr_count, data_chunk_size, gui_instance, width, height, thread_count):
    # 创建并启动文件处理线程
    process_thread = FileProcessThread(file_path, frame_rate, qr_count, data_chunk_size, width, height, thread_count)
    process_thread.progress_updated.connect(gui_instance.log_message)
    process_thread.qr_codes_ready.connect(gui_instance.on_qr_codes_ready)
    gui_instance.process_thread = process_thread  # 保存线程引用
    process_thread.start()
    return []

def read_chunk(formatted_chunk):
    # 读取序号 (4字节)
    index = int.from_bytes(formatted_chunk[:4], byteorder='big')
    # 读取数据长度 (2字节)
    data_length = int.from_bytes(formatted_chunk[4:6], byteorder='big')
    # 读取数据内容
    data_content = formatted_chunk[6:6 + data_length].decode()
    # 读取 CRC32 校验码 (4字节)
    crc32_checksum = int.from_bytes(formatted_chunk[6 + data_length:10 + data_length], byteorder='big')
    return index, data_length, data_content, crc32_checksum