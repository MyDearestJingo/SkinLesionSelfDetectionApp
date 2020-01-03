'''
接收从客户端发送来的图像，并生成.csv文件，生成任务包发送至预测模块
'''
import socket
import base64
import csv
import os
import json

MAX_CLINET_ID = 32
MAX_IMG_FILENAME = 32
MAX_RECV = 4096
MAX_TIMEOUT = 5
MAX_RETRANS = 5

STAT_PROCESSING = 1
STAT_RECV_COMPLETE = 2

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

    ''' def 从socket接收任务数据 '''
    def recv_task(self):
        self.t_socket.connect((self.host, self.port))

        # 接收用户ID
        client_id_len = int.from_bytes(self.t_socket.recv(1),byteorder="little")
        client_id = self.t_socket.recv(client_id_len).decode("utf-8")
        print("client_id: {}".format(client_id))
        
        # 创建任务目录
        # os.mkdir(self.work_dir+"/"+client_id)
        task_dir = os.path.join(self.work_dir,client_id)
        os.mkdir(task_dir)
        # task_dir = self.work_dir+client_id+"/"

        # 接收本次任务所含图像数
        n_img = int.from_bytes(self.t_socket.recv(1),byteorder="little")

        img_list = []
        for i in range(n_img): # todo: 加入异常处理以应对图像传输失败导致数量不符的情况
            # 接收图像文件名
            img_name_size = int.from_bytes(self.t_socket.recv(1),byteorder="little")
            img_name = self.t_socket.recv(img_name_size).decode("utf-8")
            
            # 接收图像文件大小
            img_size = int.from_bytes(self.t_socket.recv(4), byteorder="little")
            # print("Client: {} | {} of {} | name: {} | size: {} Bytes".format(client_id, i+1, n_img, img_name, img_size))
            
            # 分段接收文件，每段大小不超过MAX_RECV字节
            recv_size = 0
            b_img = bytes()
            recv_buff = bytes()
            recv_success = False
            while not recv_success:
                while recv_size < img_size:
                    next_size = MAX_RECV if img_size-recv_size > MAX_RECV else img_size-recv_size
                    recv_buff = self.t_socket.recv(next_size)
                    recv_size += len(recv_buff)
                    b_img += recv_buff
                    # t_socket.send(STAT_PROCESSING.to_bytes(1,"little"))
                    print("Client: {} | {} of {} | name: {} | size: {}B | recv: {}B".format(client_id, i+1, n_img, img_name, img_size, recv_size),end='\r')
                # t_socket.send(STAT_RECV_COMPLETE.to_bytes(1,"little"))
                print("\n Trans Complete. Checking data ...",end='\r')
                cs = self.get_checksum(b_img).to_bytes(1,"little")
                # print("Recv size: {}".format(recv_size))
                if cs != self.t_socket.recv(1):
                    # 图像数据中存在错误，需要重传
                    print("Data of img {} has error, need retransfer".format(img_name),end='\r')
                else: 
                    recv_success = True
                    print('Check Complete',end='\r')
                self.t_socket.send(cs)
            img = base64.b64decode(b_img)
            with open(task_dir+"/"+img_name, "wb") as img_file: 
                img_file.write(img)
                img_file.close
            img_list.append([img_name,-1])
        self.t_socket.close()
        with open(task_dir+"/"+"csv.csv","w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(img_list)
        self.task_list.append(client_id)
    
    def recv_task_with_json(self):
        self.connect()
        is_success = False
        n_timeout = 0
        while not is_success:
            if n_timeout > MAX_RETRANS:
                break
            try:
                size = int.from_bytes(self.t_socket.recv(4),byteorder="little")
                task_pack = bytes()
                recv_size = 0
                recv_buff = bytes()
                while recv_size < size:
                    next_size = MAX_RECV if size-recv_size > MAX_RECV else size-recv_size
                    recv_buff = self.t_socket.recv(next_size)
                    recv_size += len(recv_buff)
                    task_pack += recv_buff
                    print("size: {}B | recv: {}B".format(size, recv_size),end='\r')
                print('\nChecking...')
                cs = self.get_checksum(task_pack).to_bytes(1,"little")

                # 异常测试
                # cs = 0
                # cs = cs.to_bytes(1,"little")
                self.t_socket.send(cs)
                if cs != self.t_socket.recv(1):
                    print("Data Error, need to retransfer")
                else:
                    print("Transfer Complete")
                    self.close()
                    is_success = True
            except socket.timeout:
                print("Timeout")
                n_timeout += 1
        
        task_pack = json.loads(task_pack)

        # 创建任务目录
        # os.mkdir(self.work_dir+"/"+client_id)
        task_dir = os.path.join(self.work_dir,task_pack["id"])
        os.mkdir(task_dir)
        # task_dir = self.work_dir+client_id+"/"

        # 写入文件
        for idx in range(task_pack["n_imgs"]):
            img_filename = task_pack["name_imgs"][idx]
            with open(task_dir+'/'+img_filename, "wb") as img_file:
                b_img = task_pack["data_imgs"][idx].encode('utf-8')
                b_img = base64.b64decode(b_img)
                img_file.write(b_img)
                img_file.close()
        
        return True
        



    def get_checksum(self, bstream):
        cs = 0 # checksum
        for byte in bstream:
            cs ^= byte
        return cs

    ''' def 任务数据解包与任务包生成 '''

    ''' def 接收预测结果并从socket回传 '''





if __name__ == "__main__":
    work_dir = "F:/MyDearest/Project/Skin_Lesion_Detection/ResNet/project_src"
    tm = TaskManager("198.13.44.143",9999, work_dir)
    while True:
        try:
            # tm.recv_task()
            is_complete = False
            is_complete = tm.recv_task_with_json()
        except KeyboardInterrupt:
            tm.close()
            break
        except socket.timeout:
            pass

        finally:
            if is_complete:
                break

    