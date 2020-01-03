"""
全局和局部融合的测试


"""

import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import csv
from torchvision import transforms
import time
import random
import os

data_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def default_loader(path):
    return Image.open(path).convert('RGB')


class testDataset(Dataset):
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
            t = 0
            if item[1] == '1.0':
                t = 1
            if item[2] == '1.0':
                t = 2
            imgs.append((image_path + "/" + item[0] + ".jpg", t)) #imgs中保存元组，格式为(图像文件路径，图像所属类别)

        self.imgs = imgs

        self.data_transforms = data_transforms
        self.target_transform = target_transform
        self.loader = loader
        self.dataset = dataset

    def __getitem__(self, index):
        fn, label = self.imgs[index]
        img = self.loader(fn)
        img_temp = []  # 第一个存全局图像，后面三个是三个局部块图像

        sp = img.size
        width = sp[0]
        height = sp[1]

        # 图像大小调整
        newIm = img.resize((224, 224))
        if self.data_transforms is not None:
            try:
                newIm = self.data_transforms(newIm)
            except:
                print("Cannot transform image: {}".format(fn))
        img_temp.append(newIm)

        # 图像分块及选取
        if width > 1100:
            new_width = 1100
            w_to_h = float(width) / new_width
            new_height = int(height / w_to_h)
        else:
            new_width = width
            new_height = height
        img = img.resize((new_width, new_height))
        count = 1
        while 1:
            # 随机产生x,y   此为像素内范围产生
            x = random.randint(1, width - 224) # MD: 这里可能有错，应该是new_width和new_height
            y = random.randint(1, height - 224)
            # 裁剪
            box = (x, y, 224 + x, 224 + y)
            imgi = img.crop(box)
            if self.data_transforms is not None:
                try:
                    imgi = self.data_transforms(imgi)
                except:
                    print("Cannot transform image: {}".format(fn))
            img_temp.append(imgi)
            count += 1
            if count == 4:
                break
        return img_temp, label

    def __len__(self):
        return len(self.imgs)


model_l = torch.load('F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_l_3c.pkl')
model_l = model_l.to(device)
model_l.eval()

model_g = torch.load('F:/MyDearest/Project/Skin_Lesion_Detection/isic_resnet_g.pkl')
model_g = model_g.to(device)
model_g.eval()

eval_loss = 0.
eval_acc = 0.
batch_size = 10

test_dataset = testDataset(csv_path="F:/MyDearest/Project/Dataset/2017/ISIC-2017_Test_v2_Part3_GroundTruth.csv",
                           image_path="F:/MyDearest/Project/Dataset/2017/ISIC-2017_Test_v2_Data",
                           data_transforms=data_transform,
                           dataset='test')

test_loader = DataLoader(test_dataset,
                         batch_size=batch_size,
                         shuffle=True)

dataset_size = len(test_dataset)
count_batch = 0
running_corrects = 0
class0 = 0
class1 = 0
class2 = 0
class0all = 0
class1all = 0
class2all = 0
begin_time = time.time()

inputs = []
for data in test_loader:
    count_batch += 1
    # get the inputs
    inputs, labels = data

    input0 = inputs[0].to(device) # 全局图像
    input1 = inputs[1].to(device) # 局部图像I
    input2 = inputs[2].to(device) # 局部图像II
    input3 = inputs[3].to(device) # 局部图像III

    labels = labels.to(device)

    output0 = model_g(input0)

    output1 = model_l(input1)
    output2 = model_l(input2)
    output3 = model_l(input3)

    out_tensor = torch.randn(10, 3) # 10应该是batch_size
    out_tensor = out_tensor.to(device)
    i = 0
    while i < batch_size: # 对batch中的每一张图计算其分类概率
        j = 0
        while j < 3:
            # 选择三种分类结果里可能性最大的那个
            temp = output1.data[i, j]     # output1: local output 1
            if output2.data[i, j] > temp: # output2: local output 2
                temp = output2.data[i, j] 
            if output3.data[i, j] > temp: # output3: local output 3
                temp = output3.data[i, j]

            out_tensor[i, j] = temp / 2 + output0.data[i, j] / 2 # output1: global output; 另：局部判断结果和全局判断结果占的权重相同(1/2)
            # out_tensor[i, j] = temp
            # if temp < output0.data[i, j]:
            #     out_tensor[i, j] = output0.data[i, j]
            j = j + 1
        i = i + 1

    preds_value, preds = torch.max(out_tensor, 1) # torch.max(out_tensor, 1)返回各行最大元素以及其列索引
    running_corrects += torch.sum(preds == labels.data)
    class0all += torch.sum(labels.data == 0)
    class1all += torch.sum(labels.data == 1)
    class2all += torch.sum(labels.data == 2)
    for k in range(batch_size):
        if labels.data[k] == 0:
            if preds[k] == 0:
                class0 += 1
        if labels.data[k] == 1:
            if preds[k] == 1:
                class1 += 1
        if labels.data[k] == 2:
            if preds[k] == 2:
                class2 += 1

acc0 = float(class0) / class0all
acc1 = float(class1) / class1all
acc2 = float(class2) / class2all
# print('{} all:{} testnum:{} Acc: {:.4f}'.format('class0', class0all, class0, acc0))
# print('{} all:{} testnum:{} Acc: {:.4f}'.format('class1', class1all, class1, acc1))
# print('{} all:{} testnum:{} Acc: {:.4f}'.format('class2', class2all, class2, acc2))
print("{} all:{}".format("class0",class0all))
print("{} all:{}".format("class0",class1all))
print("{} all:{}".format("class0",class2all))

epoch_acc = float(running_corrects) / dataset_size
print('{}  Acc: {:.4f} Time: {:.4f}s'.format('test', epoch_acc, time.time() - begin_time))
