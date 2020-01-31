import os
import time
# import tools
# from tools import Status
from transfer import Transferer
from transfer import PredictorCom
from transfer import ClientCom
import sys
sys.path.append("..")

aliyun = "120.26.147.239"
aliyun_inside = "172.16.71.30"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"
localhost = "127.0.0.1"

workdir = "C:/Users/MyDearest Surface/Documents/Project/SkinLesionSelfDetectionApp/dev/test"
# workdir = "/root/SkinLesionSelfDetectionApp/dev/test"
trans = Transferer(localhost,9999,9998, workdir)

pred_dev = PredictorCom(trans)
client_dev = ClientCom(trans)
try:
    pred_dev.start()
    client_dev.start()
finally:
    pred_dev.join()
    client_dev.join()

