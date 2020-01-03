import torch
from torch.utils.data import Dataset
from PIL import Image
import csv
from torchvision import transforms
import time
import random
import os
import sys
sys.path.append("../")

def default_loader(path):
    return Image.open(path).convert('RGB')

class InputData(Dataset):
    def __init__(self, csv_path, img_folder, dataset="", data_transforms=None, target_transform=None, 
                loader=default_loader):
        imgs = []
        self.pic_list = []
        # .csv 文件保存当前预测任务的所有图片的路径，并在预测后保存每张图片的预测结果概率
        csv_reader = csv.reader(open(csv_path,"r"))
        for item in csv_reader:
            imgs.append([img_folder + "\\" + item[0] + ".jpg", 0.0, 0.0, 0.0]) # 图片确切路径，属于类1的概率，属于类2的概率，属于类3的概率
            self.pic_list.append(item)
        self.imgs = imgs

        self.data_transforms = data_transforms
        self.target_transform = target_transform
        self.loader = loader
        self.dataset = dataset
    
    def __getitem__(self, index):
        img_path = self.imgs[index][0]
        img = self.loader(img_path)
        img_temp = [] # 用以暂存resize后的图像，随机3次crop后得到的3张图像
        
        w = img.size[0]
        h = img.size[1]

        # resize img
        resized_img = img.resize((224, 224))
        if self.data_transforms is not None:
            try:
                resized_img = self.data_transforms(resized_img)
            except:
                print("Cannot transform img: {}".format(img_path))
        img_temp.append(resized_img)

        # 图像分块
        if w > h:
            if w > 1100:
                new_w = 1100
                ratio = float(w)/new_w
                new_h = int(h/ratio)
            else:
                new_w = w
                new_h = h
        else:
            if h > 1100:
                new_h = 1100
                ratio = float(h)/new_h
                new_w = int(w/ratio)
            else:
                new_w = w
                new_h = h
        img = img.resize((new_w, new_h))
        box_size = 224
        for i in range(3):
            # 随机产生切割框的左上角坐标
            x = random.randint(1, new_w - box_size)
            y = random.randint(1, new_h - box_size)
            box = (x, y, x+box_size, y+box_size)
            sub_img = img.crop(box)
            if self.data_transforms is not None:
                try: 
                    sub_img = self.data_transforms(sub_img)
                except:
                    print("Cannot transform img: {}".format(img_path))
            img_temp.append(sub_img)

        return img_temp,0
    
    def __len__(self):
        return len(self.imgs)
        

