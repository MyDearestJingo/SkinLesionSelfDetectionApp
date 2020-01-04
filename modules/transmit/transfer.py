'''
中转服务器
12.30.2019: 字节流图片发送至RTX测试
'''

import socket
import base64
import time
import json
import tools

MAX_CLINET_ID = 32
MAX_IMG_FILENAME = 32
MAX_RECV = 1024
MAX_TIMEOUT = 5 
MAX_RETRANS = 5
MAX_SEG_SIZE = 4096 # 最大单次传输片段大小

trans_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

aliyun = "120.26.147.239"
aliyun_inside = "172.16.71.30"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"

host = vps_jp
port = 9999

trans_socket.bind((host, port))
trans_socket.listen(5)


# img_filenames = ["ISIC_0012086.jpg", "ISIC_0012092.jpg", "ISIC_0012095.jpg"]
img_filenames = ["pixiv57735171_12.jpg", "pixiv57735171_11.jpg", "pixiv57735171_6.jpg"]


def send_task():
    task_socket, addr = trans_socket.accept()

    client_id = "TEST"+str(int(time.time()))
    n_img = len(img_filenames)
    
    task_pack = {"id": client_id,
                "n_imgs": len(img_filenames),
                "name_imgs":img_filenames,
                "data_imgs": []}
    
    for filename in task_pack["name_imgs"]:
        with open(filename, "rb") as img_file:
            b_img = base64.b64encode(img_file.read())
            task_pack["data_imgs"].append(b_img.decode("utf-8"))
            img_file.close()

    bstream = json.dumps(task_pack).encode('utf-8')
    size = len(bstream)
    print("Sending Task of {} | size: {}B".format(client_id, size))
    try:
        tools.send_data(task_socket, bstream)
    except KeyboardInterrupt as KBI:
        print(KBI)
        raise KeyboardInterrupt
    except Exception as E:
        print(E)
    finally:
        task_socket.close()
            


if __name__ == "__main__":
    try:
        while True:
            # send_task_with_json()
            send_task()
    except KeyboardInterrupt:
        # task_socket.close()
        trans_socket.close()
        print("Socekt Closed")
        # break
    except ConnectionResetError:
        pass
    finally:
        # task_socket.close()
        trans_socket.close()
