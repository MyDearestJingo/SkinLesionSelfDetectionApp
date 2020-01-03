from torch.utils.data import Dataset, DataLoader
from PIL import Image
import csv
import torch
import random

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def default_loader(path):
    return Image.open(path).convert('RGB')


class MyDataset_G(Dataset):
    def __init__(self, csv_path, image_path, dataset='', data_transforms=None, target_transform=None,
                 loader=default_loader):
        # 1. 初始化文件路径，并将文件名和标签值放入一个列表Initialize file path or list of file names.
        # 2. 初始化自身参数
        imgs = []
        # 读取csv至字典
        csvFile = open(csv_path, "r")
        reader = csv.reader(csvFile)

        for item in reader:
            # 忽略第一行
            if reader.line_num == 1:
                continue
            temp = 0
            if item[1] == '1.0':
                temp = 1
            if item[2] == '1.0':
                temp = 2
            imgs.append((image_path + "/" + item[0] + ".jpg", temp))
            if temp != 0 and dataset == 'train':
                imgs.append((image_path + "/" + item[0] + ".jpg", temp))
        self.imgs = imgs

        self.data_transforms = data_transforms
        self.target_transform = target_transform
        self.loader = loader
        self.dataset = dataset

    def __getitem__(self, index):
        fn, label = self.imgs[index]
        img = self.loader(fn)
        sp = img.size

        # 图像大小调整
        newIm = img.resize((224, 224))
        # print("现size:  {} ", newIm.size)
        if self.data_transforms is not None:
            try:
                img = self.data_transforms[self.dataset](newIm)
            except:
                print("Cannot transform image: {}".format(fn))
        return img, label

    def __len__(self):
        return len(self.imgs)
