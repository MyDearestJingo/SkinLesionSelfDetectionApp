'''
接收从客户端发送来的图像，并生成.csv文件，生成任务包发送至预测模块
'''
import socket
import base64
import csv
import os
import json
import tools
from tools import Status

MAX_CLINET_ID = 32
MAX_IMG_FILENAME = 32
MAX_RECV = 4096
MAX_TIMEOUT = 5
MAX_RETRANS = 5

# self.stat.STAT_PROCESSING = 1
# self.stat.STAT_RECV_COMPLETE = 2
# self.stat.STAT_KEYBORDINTERRUPT = -3
# self.stat.STAT_TIMEOUT = -2
# self.stat.STAT_FAILURE = -1
# self.stat.STAT_NOERROR = 0

class TaskManager:
    def __init__(self, host, port, work_dir):
        # 定义socket
        self.t_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.t_socket.settimeout(MAX_TIMEOUT)
        self.host = host
        self.port = port
        self.work_dir = work_dir
        self.task_list = []
        self.stat = Status()
        pass
    
    def connect(self):
        self.t_socket.connect((self.host, self.port))
    
    def close(self):
        self.t_socket.close()

    ''' def 从socket接收任务数据并写入磁盘 '''
    def recv_task(self, max_seg_recv=0):
        recv_stat, task_pack = tools.recv_data(self.t_socket)
        task_pack = json.loads(task_pack)

        if task_pack["id"] == "%WAIT%":
            return self.stat.STAT_WAIT # status flag of waiting

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
        print(file_list)
        with open(task_dir+"/"+"csv.csv","w",newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(file_list)
        self.task_list.append(task_pack["id"])
        
        return self.stat.STAT_NOERROR

    def get_checksum(self, bstream):
        cs = 0 # checksum
        for byte in bstream:
            cs ^= byte
        return cs

    ''' def 任务数据解包与任务包生成 '''
    def get_task(self):
        return self.work_dir+'/'+self.task_list[0] # 返回当前任务列表中最先提交任务的用户ID

    ''' def 接收预测结果并从socket回传 '''
    def send_result(self, result):
        # self.connect()
        client_id = self.task_list.pop(0)
        feedback = {"id": client_id,"msg": result}
        bstream = json.dumps(feedback).encode('utf-8')
        send_stat,_ = tools.send_data(self.t_socket, bstream)
        if send_stat != self.stat.STAT_NOERROR:
            print("Reuslt of {} send failed".format(client_id))
        # self.task_list.pop[0]
        pass

aliyun = "120.26.147.239"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"


if __name__ == "__main__":
    work_dir = "F:/MyDearest/Project/SkinLesionSelfDetectionApp/dev/test"
    tm = TaskManager(aliyun,9999, work_dir)
    self.stat.STAT_flag = -1
    while True:
        try:
            # tm.recv_task()
            self.stat.STAT_flag = tm.recv_task(max_seg_recv=0)
        except KeyboardInterrupt:
            tm.close()
            break
        except socket.timeout:
            pass

        finally:
            if not self.stat.STAT_flag:
                break

    