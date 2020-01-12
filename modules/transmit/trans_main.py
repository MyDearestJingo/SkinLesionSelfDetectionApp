import os
import time
import tools
from tools import Status
from transfer import Transferer
from transfer import PredictorCom
from transfer import ClientCom

aliyun = "120.26.147.239"
aliyun_inside = "172.16.71.30"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"

img_filenames = ["ISIC_0012086.jpg", "ISIC_0012092.jpg", "ISIC_0012095.jpg"]
# img_filenames = ["pixiv57735171_12.jpg", "pixiv57735171_11.jpg", "pixiv57735171_6.jpg"]

trans = Transferer(virtual,9999,9998,os.getcwd()+'/'+"test")
# try:
#     trans.connet_pred_dev()
#     while True:
#         # send_task()
#         trans.send_task(client_id="%WAIT%")
#         # _, result_data = tools.recv_data(trans.pred_socket)
#         time.sleep(5)
# finally:
#     # task_socket.close()
#     # trans_socket.close()
#     if trans.pred_socket is not None:
#         trans.pred_socket.close()
#     trans.socket_1.close()
#     trans.socket_2.close()

pred_dev = PredictorCom(trans)
client_dev = ClientCom(trans)
try:
    pred_dev.start()
    client_dev.start()
finally:
    pred_dev.join()
    client_dev.join()

