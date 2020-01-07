'''
中转服务器
12.30.2019: 字节流图片发送至RTX测试
'''

import socket
import base64
import time
import json
import tools
import os
import csv

aliyun = "120.26.147.239"
aliyun_inside = "172.16.71.30"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"

host = aliyun_inside
port = 9999

img_filenames = ["ISIC_0012086.jpg", "ISIC_0012092.jpg", "ISIC_0012095.jpg"]
# img_filenames = ["pixiv57735171_12.jpg", "pixiv57735171_11.jpg", "pixiv57735171_6.jpg"]


class Transferer():
    def __init__(self, local_ip, pred_port, client_port, work_dir):
        self.ip = local_ip
        self.pred_port = pred_port
        self.client_port = client_port
        self.socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_1.bind((self.ip, self.pred_port))
        self.socket_2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_2.bind((self.ip, self.client_port))
        self.pred_socket = None
        self.client_socket = None
        self.work_dir = work_dir

    def connet_pred_dev(self, max_link=1):
        self.socket_1.listen(max_link)
        self.pred_socket, pred_addr = self.socket_1.accept()
        return pred_addr

    def connet_client_dev(self, max_link=1):
        self.socket_2.listen(max_link)
        self.client_socket, client_addr = self.socket_2.accept()
        return client_addr

    def recv_req(self): # 从客户端接收任务请求
        pass

    def send_task(self, client_id, data_stream=None):
        task_pack = {"id": client_id,
                    "n_imgs": 0,
                    "name_imgs": [],
                    "data_imgs": []
                    }
        bstream = None
        if data_stream is None:
            if client_id != "%WAIT%":
                task_dir = os.path.join(self.work_dir, client_id)
                csv_reader = csv.reader(open(task_dir+'/'+'csv.csv',"r"))
                for item in csv_reader:
                    filename = item[0]
                    task_pack["name_imgs"].append(filename)
                    task_pack["n_imgs"] += 1
                    with open(task_dir +'/' +filename, "rb") as img_file:
                        b_img = base64.b64encode(img_file.read())
                        task_pack["data_imgs"].append(b_img.decode("utf-8"))
                        img_file.close()
            bstream = json.dumps(task_pack).encode('utf-8')
        else:
            bstream = data_stream
        size = len(bstream)
        print("Sending Task of {} | size: {}B".format(client_id, size))

        try:
            tools.send_data(self.pred_socket, bstream)
        except KeyboardInterrupt as KBI:
            print(KBI)
            raise KeyboardInterrupt
        except Exception as E:
            print(E)
        # finally:
        #     task_socket.close()

    def recv_result(self):
        try:
            _, data=tools.recv_data(self.pred_socket)
            tools.send_data(self.client_socket, data)
        finally:
            pass
        

if __name__ == "__main__":
    trans = Transferer(aliyun_inside,9999,9998,os.getcwd()+'/'+"test")
    try:
        while True:
            trans.connet_pred_dev()
            trans.send_task(client_id="TEST")
            _, result_data = tools.recv_data(trans.pred_socket)
    except ConnectionResetError:
        pass
    finally:
        if trans.pred_socket is not None:
            trans.pred_socket.close()
        trans.socket_1.close()
        trans.socket_2.close()
