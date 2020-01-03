'''
中转服务器
12.30.2019: 字节流图片发送至RTX测试
'''

import socket
import base64
import time
import json

def getChecksum(bstream):
    cs = 0 # checksum
    for byte in bstream:
        cs ^= byte
    return cs

MAX_CLINET_ID = 32
MAX_IMG_FILENAME = 32
MAX_RECV = 1024
MAX_TIMEOUT = 5 # 这个时间还要调，除非发送端拆成多个小包（比如一个包4KB)多次发送，不然都是头疼的事
MAX_RETRANS = 5
MAX_SEG_SIZE = 4096 # 最大单次传输片段大小

STAT_KEYBORDINTERRUPT = -3
STAT_TIMEOUT = -2
STAT_FAILURE = -1
STAT_NOEEROR = 0
trans_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

aliyun = "120.26.147.239"
aliyun_inside = "172.16.71.30"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"

host = vps_jp
port = 9999

trans_socket.bind((host, port))
trans_socket.listen(5)


img_filenames = ["ISIC_0012086.jpg", "ISIC_0012092.jpg", "ISIC_0012095.jpg"]
# img_filenames = ["pixiv57735171_12.jpg", "pixiv57735171_11.jpg", "pixiv57735171_6.jpg"]

def send_data(send_socket, bstream, max_seg_size, timeout, max_retry):

    stat_flag = None

    pre_timeout = send_socket.gettimeout()
    # pre_timeout = None
    send_socket.settimeout(timeout)

    sent_size = 0
    data_size = len(bstream)
    
    n_retry = 0
    max_seg_size = data_size if max_seg_size <= 0 else max_seg_size
    while sent_size < data_size:
        next_size = max_seg_size if data_size-sent_size>max_seg_size else data_size-sent_size 
        try:
            sent_size += send_socket.send(bstream[sent_size:sent_size+next_size])
            # sent_size += next_size
            print("Total Size: {}B | Sent: {}B".format(data_size, sent_size), end='\r')
        except socket.timeout:
            n_retry += 1
            if n_retry >= max_retry:
                print("Timeout Error")
                stat_flag = STAT_TIMEOUT
                break 
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            stat_flag = STAT_KEYBORDINTERRUPT
            break
        except Exception as e:
            print("Exception Catched: ",e)
            stat_flag = STAT_FAILURE
            break
    send_socket.settimeout(pre_timeout)
    stat_flag = STAT_NOEEROR
    # print('\n')
    return (stat_flag, sent_size)

def send_task():
    try:
        task_socket, addr = trans_socket.accept()
        task_socket.settimeout(MAX_TIMEOUT)
        while True:
            client_id = "TEST"+str(int(time.time()))
            print("Sending Task of {}".format(client_id))
            client_id = client_id.encode('utf-8')
            n_img = len(img_filenames)
            
            # 发送用户ID
            client_id_size = len(client_id).to_bytes(1,"little", signed=False)
            task_socket.send(client_id_size)
            task_socket.send(client_id)

            # 发送本次任务所含图像数
            task_socket.send(n_img.to_bytes(1, "little", signed=False))

            for img_filename in img_filenames:
                with open(img_filename,"rb") as img_file:
                    b_img = base64.b64encode(img_file.read())

                    # 发送文件名
                    img_filename = img_filename.encode('utf-8')
                    task_socket.send(len(img_filename).to_bytes(1,"little",signed=False))
                    task_socket.send(img_filename)

                    # 发送文件长度
                    task_socket.send(len(b_img).to_bytes(4,"little",signed=False))

                    # 发送文件数据
                    send_success = False
                    while not send_success:
                        task_socket.sendall(b_img)
                        cs = getChecksum(b_img).to_bytes(1,"little")
                        task_socket.send(cs)
                        if cs == task_socket.recv(1):
                            send_success = True
                            print("SENT: {}".format(img_filename))
    except KeyboardInterrupt:
            task_socket.close()

def send_task_with_json():
    task_socket, addr = trans_socket.accept()
    # task_socket.settimeout(MAX_TIMEOUT)

    client_id = "TEST"+str(int(time.time()))
    # client_id = client_id.encode('utf-8')
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
    cs = getChecksum(bstream).to_bytes(1,"little")
    size = len(bstream).to_bytes(4,"little")
    bstream = size+bstream+cs
    is_success = False
    n_timeout = 0
    print("Sending Task of {} | size: {}B".format(client_id, int.from_bytes(size,"little")))
    while not is_success:
        if n_timeout > MAX_RETRANS:
            print("Connect Timeout")
            break
        try:
            '''
            task_socket.sendall(size+bstream+cs)
            task_socket.send(cs)
            '''
            stat_flag, sent_size = send_data(task_socket, bstream, 0, MAX_TIMEOUT, MAX_RETRANS)
            print("Sent: {}B, wait for checking...".format(sent_size),end='\r')
            if stat_flag == STAT_KEYBORDINTERRUPT:
                raise KeyboardInterrupt
                break
            if cs  == task_socket.recv(1):
                is_success = True
                print("Transmition of {} is successful".format(client_id))
                task_socket.close()
            time.sleep(1)
        except socket.timeout:
            print("Timeout")
            n_timeout += 1
        except KeyboardInterrupt:
            task_socket.close()
            print("KeybordInterrupt")
        if is_success:
            break
    # while not is_success:
    #     sent_size = send_data(task_socket, bstream, MAX_SEG_SIZE, MAX_TIMEOUT)
    #     print("Sent: {}B, wait for checking ... ".format(sent_size))
    pass
            
            


if __name__ == "__main__":
    try:
        # send_task()
        while True:
            send_task_with_json()
    except KeyboardInterrupt:
        task_socket.close()
        trans_socket.close()
        print("Socekt Closed")
        # break
    except ConnectionResetError:
        pass
    finally:
        task_socket.close()
        trans_socket.close()
