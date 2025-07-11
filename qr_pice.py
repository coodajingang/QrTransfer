from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSize

class QRPice(): 
    def __init__(self, idx):
        self.qr_code = None
        self.is_collected = False
        self.idx = idx
        self.qr_code_ready = False  # 是否已生成二维码
    
    def set_qr_code(self, qr_code):
        self.qr_code = qr_code
        self.qr_code_ready = True
    
    def clear_qr_code(self):
        self.qr_code = None
        self.is_collected = True
    def ready_to_collect(self, qr_code):
        self.qr_code = qr_code
        self.is_collected = False
        self.qr_code_ready = True  # 重置二维码状态
    def reset_qr_ready(self):
        self.is_collected = False
        self.qr_code_ready = True  # 重置二维码状态
    
class QRPiceWrapper():
    def __init__(self):
        self.qr_pices = None
        self.chunks = None
        self.chunk_count = 0
        self.empty_qr_code = None
        self.qr1_loop_array = [] 
        self.qr2_loop_array = [] 
        self.qr3_loop_array = [] 
        self.qr4_loop_array = [] 

    def get_empty_qr(self):
        return self.empty_qr_code
    
    def init_empty_qr_img(self, img_width, img_height):
        self.empty_qr_code = QPixmap(QSize(img_width, img_height))  # 空的二维码，默认值

    def init_chunks(self, chunks):
        """初始化分块"""
        self.chunks = chunks
        self.chunk_count = len(chunks)
        self.qr_pices = [QRPice(i) for i in range(self.chunk_count)]
    
    def update_qr_code(self, index, qr_code):
        """更新二维码"""
        self.qr_pices[index].set_qr_code(qr_code)

    def set_ready_to_collecte(self, index, qr_code):
        self.qr_pices[index].ready_to_collect(qr_code)
    
    def get_qr_code(self, index):
        """获取二维码"""
        return self.qr_pices[index].qr_code if self.qr_pices[index].qr_code_ready else self.empty_qr_code
    
    def has_qr_code(self, index): 
        """检查index对应的qr_code是否已经存在 """
        return self.qr_pices[index].qr_code is not None 
    
    def update_ready_to_collecte_status(self, index):
        """更新index对应的采集状态""" 
        self.qr_pices[index].reset_qr_ready()

    def get_next_qr_code(self, index, start, end):
        """获取下一个可用的二维码"""
        ''' 从index开始 到end 查找可用的二维码 ，没有的话，从start开始查找到index ，若还没有，返回空的码'''
        for i in range(index, end + 1):
            pice = self.qr_pices[i]
            if pice.qr_code_ready and not pice.is_collected:
                return pice.qr_code
        for i in range(start, index):
            pice = self.qr_pices[i]
            if pice.qr_code_ready and not pice.is_collected:
                return pice.qr_code
        # 如果没有找到可用的二维码，返回空的二维码
        return self.empty_qr_code

    def clear_already_collected(self, collected):
        if collected:
            # self.log_message(f"清除已收集的二维码: {collected}")
            for ii in collected: 
                i= int(ii)
                if i < 0 or i > self.chunk_count:
                    continue
                self.qr_pices[i].clear_qr_code()
    
    def fill_qr_loop_array(self, qr_idx, start, end):
        if qr_idx == 1: 
            self.qr1_loop_array.clear()
            for i in range(start, end + 1):
                pice = self.qr_pices[i]
                if pice.qr_code_ready and not pice.is_collected:
                    self.qr1_loop_array.append(i)
        elif qr_idx == 2:
            self.qr2_loop_array.clear()
            for i in range(start, end + 1):
                pice = self.qr_pices[i]
                if pice.qr_code_ready and not pice.is_collected:
                    self.qr2_loop_array.append(i)
        elif qr_idx == 3:
            self.qr3_loop_array.clear()
            for i in range(start, end + 1):
                pice = self.qr_pices[i]
                if pice.qr_code_ready and not pice.is_collected:
                    self.qr3_loop_array.append(i)
        elif qr_idx == 4:
            self.qr4_loop_array.clear()
            for i in range(start, end + 1):
                pice = self.qr_pices[i]
                if pice.qr_code_ready and not pice.is_collected:
                    self.qr4_loop_array.append(i)
        
    def get_next_qr_code_from_not_collected(self, start, end, cur_idx, qr_idx):
        if qr_idx == 1:
            if len(self.qr1_loop_array) == 0:
                self.fill_qr_loop_array(1, start, end) 
                if len(self.qr1_loop_array) == 0:
                    return (self.empty_qr_code, start)
            for tmp in self.qr1_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)
            self.fill_qr_loop_array(1, start, end)
            for tmp in self.qr1_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)
            if len(self.qr1_loop_array) > 0:
                tmp = self.qr1_loop_array[0]
                return (self.qr_pices[tmp].qr_code, tmp)
            else: 
                return (self.empty_qr_code, start)
        elif qr_idx == 2:
            if len(self.qr2_loop_array) == 0:
                self.fill_qr_loop_array(2, start, end) 
                if len(self.qr2_loop_array) == 0:
                    return (self.empty_qr_code, start)
            
            for tmp in self.qr2_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)
            self.fill_qr_loop_array(2, start, end)
            for tmp in self.qr2_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)
            if len(self.qr2_loop_array) > 0:
                tmp = self.qr2_loop_array[0]
                return (self.qr_pices[tmp].qr_code, tmp)
            else: 
                return (self.empty_qr_code, start)
        elif qr_idx == 3:
            if len(self.qr3_loop_array) == 0:
                self.fill_qr_loop_array(3, start, end) 
                if len(self.qr3_loop_array) == 0:
                    return (self.empty_qr_code, start)
            for tmp in self.qr3_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)
            self.fill_qr_loop_array(3, start, end)
            for tmp in self.qr3_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)
            if len(self.qr3_loop_array) > 0:
                tmp = self.qr3_loop_array[0]
                return (self.qr_pices[tmp].qr_code, tmp)
            else: 
                return (self.empty_qr_code, start)
        elif qr_idx == 4:
            if len(self.qr4_loop_array) == 0:
                self.fill_qr_loop_array(4, start, end) 
                if len(self.qr4_loop_array) == 0:
                    return (self.empty_qr_code, start)
            for tmp in self.qr4_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)
            self.fill_qr_loop_array(4, start, end)
            for tmp in self.qr4_loop_array:
                if tmp > cur_idx: 
                    return (self.qr_pices[tmp].qr_code, tmp)    
            if len(self.qr4_loop_array) > 0:
                tmp = self.qr4_loop_array[0]
                return (self.qr_pices[tmp].qr_code, tmp)
            else: 
                return (self.empty_qr_code, start)

