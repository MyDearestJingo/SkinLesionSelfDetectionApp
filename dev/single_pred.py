"""
测试运行时接收单张照片，对其进行判断
输入：照片文件路径
输出：该照片对应的类别及其概率
"""

import torch
from torch.utils.data import DataLoader
from PIL import Image
import csv
from torchvision import transforms
import time
import os
from InputData import InputData
import sys
sys.path.append("../")

data_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229, 0.224, 0.225])
])

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

model_l = torch.load('F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_l_3c.pkl')
model_l = model_l.to(device)
model_l.eval()

model_g = torch.load('F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_g.pkl')
model_g = model_g.to(device)
model_g.eval()

eval_loss = 0.
eval_acc = 0.

preds_dataset = InputData(csv_path="F:/MyDearest/Project/Skin_Lesion_Detection/ResNet/project_data/test.csv",
                        img_folder="F:/MyDearest/Project/Skin_Lesion_Detection/ResNet/project_data/test_data",
                        dataset="project_test",
                        data_transforms=data_transform)
dataset_size = len(preds_dataset)
preds_loader = DataLoader(preds_dataset,
                        batch_size=dataset_size,
                        shuffle=False)


print("dataset_size: {}".format(dataset_size))
class0 = 0
class1 = 0
class2 = 0

begin_time = time.time()
inputs = []
prob_tensor = torch.randn(dataset_size, 3)
result = []

for item in preds_loader:
    inputs, labels = item

    input_g = inputs[0].to(device) # global
    input_l1 = inputs[1].to(device) # local 1
    input_l2 = inputs[2].to(device) # local 2
    input_l3 = inputs[3].to(device) # local 3

    output_g = model_g(input_g)
    output_l1 = model_l(input_l1)
    output_l2 = model_l(input_l2)
    output_l3 = model_l(input_l3)

    prob_tensor = prob_tensor.to(device)
    for i in range(dataset_size): # 对每张图像进行决策判断
        for j in range(3): # make local decision; j: class_j
            decision_l = max(output_l1[i,j], output_l2[i,j], output_l3[i,j])
            prob_tensor[i,j] = decision_l/2 + output_g.data[i, j]/2

preds_value, preds = torch.max(prob_tensor, 1)
preds_sum = torch.sum(prob_tensor,0)
preds_avg = torch.mean(prob_tensor,0)
print("preds_avg:", preds_avg)
for i in range(dataset_size):
    # prob = float(preds_value[i].item())/preds_sum[i].item()
    prob = 1.0/3.0 * (1+preds_value[i].item()-preds_avg[i].item())
    # result.append([preds_dataset.imgs[i][0], preds[i].item(), prob])
    result.append([preds[i].item(), prob])
print(result)