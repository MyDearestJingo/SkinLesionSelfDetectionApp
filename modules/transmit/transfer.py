'''
中转服务器
12.30.2019: 字节流图片发送至RTX测试
'''
import sys
sys.path.append("..")

import socket
import base64
import time
import json
import tools
import os
import csv
import threading

aliyun = "120.26.147.239"
aliyun_inside = "172.16.71.30"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"

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
        self.req_list = []
        self.result_list = []
        self.req_lock = threading.Lock()
        self.result_lock = threading.Lock()

    def connet_pred_dev(self, max_link=1):
        self.socket_1.listen(max_link)
        self.pred_socket, pred_addr = self.socket_1.accept()
        return pred_addr

    def disconnect_pred_dev(self):
        self.pred_socket.close()

    def connet_client_dev(self, max_link=1):
        self.socket_2.listen(max_link)
        self.client_socket, client_addr = self.socket_2.accept()
        return client_addr

    def disconnect_client_dev(self):
        self.client_socket.close()

    def recv_req(self): # 从客户端接收任务请求
        n_timeout = 0
        recv_stat, req_data = tools.recv_data(self.client_socket)
        req_pack = json.loads(req_data.decode('utf-8'))

        # 创建任务目录
        client_id = req_pack["id"]
        req_dir = os.path.join(self.work_dir,client_id)
        os.mkdir(req_dir)

        # 写入文件
        for idx in range(req_pack["n_imgs"]):
            img_filename = req_pack["name_imgs"][idx]
            with open(req_dir+'/'+img_filename, "wb") as img_file:
                b_img = req_pack["data_imgs"][idx].encode('utf-8')
                b_img = base64.b64decode(b_img)
                img_file.write(b_img)
                img_file.close()
        
        file_list = []
        for file_name in req_pack["name_imgs"]:
            file_list.append([file_name, -1])
        print(file_list)
        with open(req_dir+"/"+"csv.csv","w",newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(file_list,)
        
        return {"id": client_id, "data": req_data}

    def send_task(self, client_id, data_stream=None, out_socket=None):
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

        if out_socket is None:
            out_socket = self.pred_socket
        try:
            tools.send_data(out_socket, bstream)
        except KeyboardInterrupt as KBI:
            print(KBI)
            raise KeyboardInterrupt
        except Exception as E:
            raise E
        # finally:
        #     task_socket.close()

    def recv_result(self):
        try:
            _, data=tools.recv_data(self.pred_socket) # data is json in encoding of UTF-8
            result = json.loads(data.decode('utf-8')) 
            return result
        finally:
            pass

    def send_result(self, result):
        bstream = json.dumps(result).encode('utf-8')
        print("Sending result of client: {} | size: {}B".format(result["id"], len(bstream)))
        try:
            tools.send_data(self.client_socket, bstream)
        finally:
            pass

class PredictorCom(threading.Thread):
    def __init__(self, transferer):
        threading.Thread.__init__(self)
        self.transferer = transferer

    def run(self):
        try:
            self.transferer.connet_pred_dev()
            while True:
                self.transferer.req_lock.acquire()
                if len(self.transferer.req_list)==0 :
                    self.transferer.req_lock.release()
                    self.transferer.send_task(client_id="%WAIT%")
                    time.sleep(1)
                else:
                    self.transferer.send_task(client_id=self.transferer.req_list[0]["id"],
                                            data_stream=self.transferer.req_list[0]["data"])
                    self.transferer.req_list.pop(0)
                    self.transferer.req_lock.release()
                    print("Waiting for Result")
                    result = self.transferer.recv_result()
                    self.transferer.result_lock.acquire()
                    self.transferer.result_list.append(result)
                    self.transferer.result_lock.release()
        finally:
            self.transferer.disconnect_pred_dev()
            pass

class ClientCom(threading.Thread):
    def __init__(self, transferer):
        threading.Thread.__init__(self)
        self.transferer = transferer

    def run(self):
        print("Client Socket Start. Waiting for Connecting")
        try:
            while True:
                addr = self.transferer.connet_client_dev()
                print("Connected by client: {}".format(addr))
                req = self.transferer.recv_req()
                self.transferer.req_lock.acquire()
                client_id = req["id"]
                self.transferer.req_list.append(req)
                self.transferer.req_lock.release()
                is_complete = False
                while not is_complete:
                    if self.transferer.pred_socket is not None:
                        self.transferer.result_lock.acquire()
                        if len(self.transferer.result_list)==0:
                            self.transferer.result_lock.release()
                            time.sleep(2)
                            continue
                        else:
                                for idx in range(len(self.transferer.result_list)):
                                    if self.transferer.result_list[idx]["id"] == client_id:
                                        result = self.transferer.result_list.pop(idx)
                                        self.transferer.result_lock.release()
                    else:
                        self.transferer.req_lock.acquire()
                        self.transferer.req_list.pop(0)
                        self.transferer.req_lock.release()
                        req_pack = json.loads(req["data"].decode('utf-8'))
                        # req_pack = req
                        result = []
                        for filename in req_pack["name_imgs"]:
                            result.append([filename, -2])
                        result = {"id": client_id, "result": result}
                    self.transferer.send_result(result)
                    self.transferer.disconnect_client_dev()
                    is_complete = True
        except Exception as E:
            raise E
        finally:
            pass

if __name__ == "__main__":
    # workdir = os.getcwd()+'/'+"test"
    workdir = "C:/Users/MyDearest Surface/Documents/Project/SkinLesionSelfDetectionApp/dev/test"
    trans = Transferer(aliyun_inside,9999,9998,)
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
