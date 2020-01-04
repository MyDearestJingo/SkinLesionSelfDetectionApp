'''
接收从客户端发送来的图像，并生成.csv文件，生成任务包发送至预测模块
'''
import socket
import base64
import csv
import os
import json
import tools

MAX_CLINET_ID = 32
MAX_IMG_FILENAME = 32
MAX_RECV = 4096
MAX_TIMEOUT = 5
MAX_RETRANS = 5

STAT_PROCESSING = 1
STAT_RECV_COMPLETE = 2
STAT_KEYBORDINTERRUPT = -3
STAT_TIMEOUT = -2
STAT_FAILURE = -1
STAT_NOEEROR = 0

class TaskManager:
    def __init__(self, host, port, work_dir):
        # 定义socket
        self.t_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.t_socket.settimeout(MAX_TIMEOUT)
        self.host = host
        self.port = port
        self.work_dir = work_dir
        self.task_list = []
        pass
    
    def connect(self):
        self.t_socket.connect((self.host, self.port))
    
    def close(self):
        self.t_socket.close()

    ''' def 从socket接收任务数据并写入磁盘 '''
    def recv_task(self, max_seg_recv=0):
        self.connect()
        is_success = False
        n_timeout = 0
        recv_stat, task_pack = tools.recv_data(self.t_socket)
        # while not is_success:
        #     if n_timeout > MAX_RETRANS:
        #         self.close()
        #         return STAT_TIMEOUT
        #     try:
        #         size = int.from_bytes(self.t_socket.recv(4),byteorder="little") # 报头后数据长度（包括校验和）
        #         task_pack = bytes()
        #         recv_size = 0
        #         recv_buff = bytes()
        #         _MAX_SEG_RECV = size if max_seg_recv <= 0 else max_seg_recv
        #         while recv_size < size:
        #             next_size = _MAX_SEG_RECV if size-recv_size > _MAX_SEG_RECV else size-recv_size
        #             recv_buff = self.t_socket.recv(next_size)
        #             recv_size += len(recv_buff)
        #             task_pack += recv_buff
        #             print("size: {}B | recv: {}B".format(size, recv_size),end='\r')
        #         print('\nChecking...',end='\r')
        #         cs = self.get_checksum(task_pack[:-1])
        #         recv_cs = task_pack[-1]
        
        #         # 异常测试
        #         # cs = 0
        #         # cs = cs.to_bytes(1,"little")
        #         l = 2
        #         feedback = l.to_bytes(4,"little")+cs.to_bytes(1,"little")
        #         feedback += tools.get_checksum(cs.to_bytes(1,"little")).to_bytes(1,"little")
        #         self.t_socket.send(feedback)
        #         # tools.send_data(self.t_socket,cs.to_bytes(1,"little"),check_method=None)
        #         if cs != recv_cs:
        #             print("Data Error, need to retransfer")
        #         else:
        #             print("Checking Success. Transfer Complete")
        #             self.close()
        #             is_success = True
        #     except socket.timeout:
        #         print("Timeout, retry in {} time(s)".format(MAX_RETRANS-n_timeout))
        #         n_timeout += 1
        
        task_pack = json.loads(task_pack)

        # 创建任务目录
        task_dir = os.path.join(self.work_dir,task_pack["id"])
        os.mkdir(task_dir)

        # 写入文件
        for idx in range(task_pack["n_imgs"]):
            img_filename = task_pack["name_imgs"][idx]
            with open(task_dir+'/'+img_filename, "wb") as img_file:
                b_img = task_pack["data_imgs"][idx].encode('utf-8')
                b_img = base64.b64decode(b_img)
                img_file.write(b_img)
                img_file.close()
        
        file_list = []
        for file_name in task_pack["name_imgs"]:
            file_list.append([file_name, -1])
        with open(task_dir+"/"+"csv.csv","w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(file_list)
        self.task_list.append(task_pack["id"])
        
        return STAT_NOEEROR

    def get_checksum(self, bstream):
        cs = 0 # checksum
        for byte in bstream:
            cs ^= byte
        return cs

    ''' def 任务数据解包与任务包生成 '''
    def get_task(self):
        return self.task_list.pop(0) # 返回当前任务列表中最先提交任务的用户ID

    ''' def 接收预测结果并从socket回传 '''
    def send_result(self, result):
        self.connect()
        feedback = {"msg": result}
        bstream = json.dumps(feedback)

        pass

aliyun = "120.26.147.239"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"

if __name__ == "__main__":
    work_dir = "F:/MyDearest/Project/SkinLesionSelfDetectionApp/dev/test"
    tm = TaskManager(vps_jp,9999, work_dir)
    stat_flag = -1
    while True:
        try:
            # tm.recv_task()
            stat_flag = tm.recv_task(max_seg_recv=0)
        except KeyboardInterrupt:
            tm.close()
            break
        except socket.timeout:
            pass

        finally:
            if not stat_flag:
                break

    