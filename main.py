'''
主程序
'''
import sys
sys.path.append("./modules")
sys.path.append("./models")
import time
from InputData import InputData
from Predictor import Predictor
from TaskManager import TaskManager
import tools

aliyun = "120.26.147.239"
virtual = "192.168.109.131"
vps_jp = "198.13.44.143"

local_model_path = 'F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_l_3c.pkl'
global_model_path = 'F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_g.pkl'

if __name__ == "__main__":
    predictor = Predictor(global_model_path ,local_model_path)
    work_dir = "F:/MyDearest/Project/SkinLesionSelfDetectionApp/dev/test"
    tm = TaskManager(virtual, 9999, work_dir)
    stat_tm = 0
    try:
        tm.connect()
        while True:
            print("Requesting Task from Transmitor ...")
            stat_tm = tm.recv_task()
            if stat_tm == tm.stat.STAT_WAIT:
                time.sleep(5)
                continue
            task_dir =  tm.get_task()
            print("Task Dir: {}".format(task_dir))
            predictor.load_data(work_dir=task_dir)
            result = predictor.predict()
            predictor.output_result()
            tm.send_result(result)
            break
    finally:
        tm.close()
    