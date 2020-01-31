import socket
import tools
import time
import csv
import base64
import json

work_dir = "C:/Users/MyDearest Surface/Documents/Project/SkinLesionSelfDetectionApp/dev/sim_client"
def send_req(client_id, work_dir, out_socket, data_stream=None):
        req_pack = {"id": client_id,
                    "n_imgs": 0,
                    "name_imgs": [],
                    "data_imgs": []
                    }
        bstream = None
        if data_stream is None:
            if client_id != "%WAIT%":
                req_dir = work_dir
                csv_reader = csv.reader(open(req_dir+'/'+'csv.csv',"r"))
                for item in csv_reader:
                    filename = item[0]
                    req_pack["name_imgs"].append(filename)
                    req_pack["n_imgs"] += 1
                    with open(req_dir +'/' +filename, "rb") as img_file:
                        b_img = base64.b64encode(img_file.read())
                        req_pack["data_imgs"].append(b_img.decode("utf-8"))
                        img_file.close()
            bstream = json.dumps(req_pack).encode('utf-8')
        else:
            bstream = data_stream
        size = len(bstream)
        print("Sending Task of {} | size: {}B".format(client_id, size))

        try:
            tools.send_data(out_socket, bstream)
        except KeyboardInterrupt as KBI:
            print(KBI)
            raise KeyboardInterrupt
        except Exception as E:
            raise E
        # finally:
        #     req_socket.close()
def recv_result(in_socket):
    recv_stat, bstream = tools.recv_data(in_socket)
    result = json.loads(bstream.decode('utf-8'))
    return result


virtual = "192.168.109.131"
aliyun = "120.26.147.239"
localhost = "127.0.0.1"
port =  9998
transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
transmit_socket.connect((localhost, port))

client_id = "TEST_"+str(int(time.time()))
send_req(client_id, work_dir, out_socket=transmit_socket)
print(recv_result(transmit_socket))

transmit_socket.close()