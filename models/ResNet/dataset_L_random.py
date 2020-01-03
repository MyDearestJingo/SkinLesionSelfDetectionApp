from torch.utils.data import Dataset, DataLoader
from PIL import Image
import csv
import random


def default_loader(path):
    return Image.open(path).convert('RGB')


class MyDataset_L(Dataset):
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

        self.imgs = imgs

        self.data_transforms = data_transforms
        self.target_transform = target_transform
        self.loader = loader
        self.dataset = dataset

    def __getitem__(self, index):
        fn, label = self.imgs[index]
        img = self.loader(fn)
        sp = img.size
        width = sp[0]
        height = sp[1]

        if width > 1100:
            new_width = 1100
            w_to_h = float(width) / new_width
            new_height = int(height / w_to_h)
        else:
            new_width = width
            new_height = height
        img = img.resize((new_width, new_height))
        img_temp = []  # 三个局部块图像
        h = 224
        w = 224
        i = 0
        while i < 8:
            # 随机产生x,y   此为像素内范围产生
            x = random.randint(1, new_width - 224)
            y = random.randint(1, new_height - 224)
            # 裁剪
            box = (x, y, w + x, h + y)
            imgi = img.crop(box)
            if self.data_transforms is not None:
                try:
                    imgi = self.data_transforms[self.dataset](imgi)
                except:
                    print("Cannot transform image: {}".format(fn))
            img_temp.append(imgi)
            i = i + 1
        return img_temp, label

    def __len__(self):
        return len(self.imgs)
