'''
预测器：接收TaskManager整理的任务包，并执行预测任务
'''

import torch
from torch.utils.data import DataLoader
import csv
from torchvision import transforms
import time
import os
from InputData import InputData

class Predictor:
    def __init__(self, global_model_path, local_model_path):        
        # 申请GPU
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        # 模型载入
        self.data_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.485,0.456,0.406],[0.229, 0.224, 0.225])
        ])
        model_l = torch.load(local_model_path)
        self.model_l = model_l.to(self.device)
        self.model_l.eval()
        model_g = torch.load(global_model_path)
        self.model_g = model_g.to(self.device)
        self.model_g.eval()

        self.dataset_loader = None
        self.dataset_size = None
        self.client_id = None
        self.work_dir = None
        self.pic_list = []
        self.result = None

    def load_data(self, work_dir, client_id="TEST"):
        self.client_id = client_id
        self.work_dir = work_dir
        dataset = InputData(csv_path=work_dir+"csv.csv", 
                            img_folder=work_dir, 
                            dataset=client_id, 
                            data_transforms=self.data_transform
        )
        self.pic_list = dataset.pic_list
        self.dataset_size = len(dataset)
        self.dataset_loader = DataLoader(dataset, batch_size=self.dataset_size, shuffle=False)

    def predict(self):
        begin_time = time.time()
        inputs = []
        prob_tensor = torch.randn(self.dataset_size, 3)
        result = []

        for item in self.dataset_loader:
            inputs, labels = item

            input_g = inputs[0].to(self.device) # global
            input_l1 = inputs[1].to(self.device) # local 1
            input_l2 = inputs[2].to(self.device) # local 2
            input_l3 = inputs[3].to(self.device) # local 3

            output_g = self.model_g(input_g)
            output_l1 = self.model_l(input_l1)
            output_l2 = self.model_l(input_l2)
            output_l3 = self.model_l(input_l3)

            prob_tensor = prob_tensor.to(self.device)
            for i in range(self.dataset_size): # 对每张图像进行决策判断
                for j in range(3): # make local decision; j: class_j
                    decision_l = max(output_l1[i,j], output_l2[i,j], output_l3[i,j])
                    prob_tensor[i,j] = decision_l/2 + output_g.data[i, j]/2

        preds_value, preds = torch.max(prob_tensor, 1)
        # preds_sum = torch.sum(prob_tensor,0)
        # preds_avg = torch.mean(prob_tensor,0)
        # print("preds_avg:", preds_avg)
        for i in range(self.dataset_size):
            # prob = float(preds_value[i].item())/preds_sum[i].item()
            # prob = 1.0/3.0 * (1+preds_value[i].item()-preds_avg[i].item())
            # result.append([preds_dataset.imgs[i][0], preds[i].item(), prob])
            result.append([self.pic_list[i][0], preds[i].item()])
        self.result = result
    
    def output_result(self):
        if self.client_id is not None and self.result is not None:
            with open(self.work_dir+"result.csv","w") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(self.result)
                return True
        return False

if __name__ == "__main__":
    local_model_path = 'F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_l_3c.pkl'
    global_model_path = 'F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_g.pkl'
    predictor = Predictor(global_model_path ,local_model_path)
    predictor.load_data(work_dir="../project_data/TEST/")
    predictor.predict()
    predictor.output_result()
    pass

