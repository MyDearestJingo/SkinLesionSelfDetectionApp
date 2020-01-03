"""
分别对全局和局部网络进行测试
"""

import torch
import torch._utils
try:
    torch._utils._rebuild_tensor_v2
except AttributeError:
    def _rebuild_tensor_v2(storage, storage_offset, size, stride, requires_grad, backward_hooks):
        tensor = torch._utils._rebuild_tensor(storage, storage_offset, size, stride)
        tensor.requires_grad = requires_grad
        tensor._backward_hooks = backward_hooks
        return tensor
    torch._utils._rebuild_tensor_v2 = _rebuild_tensor_v2
from torch.utils.data import DataLoader
from dataset_G import MyDataset_G
from dataset_L_center import MyDataset_L
from PIL import Image
import csv
from torchvision import transforms
from torch.autograd import Variable
import time
import random

TEST_IMG_PATH = "/home/ly/Skin_Lesion_Detection/dataset/2017/ISIC-2017_Test_v2_Data"
TEST_CSV_PATH = "/home/ly/Skin_Lesion_Detection/dataset/2017/ISIC-2017_Test_v2_Part3_GroundTruth.csv"
GLO_MOD_PATH = "/home/ly/Skin_Lesion_Detection/isic_resnet_g.pkl"

data_transforms = {
    'train': transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'test': transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def default_loader(path):
    return Image.open(path).convert('RGB')

# 暂时没有局部方法的模型
# model_l = torch.load('/home/xf/model/isic_resnet_l_3c.pkl')
# model_l = model_l.to(device)
# model_l.eval()

model_g = torch.load(GLO_MOD_PATH)
model_g = model_g.to(device)
model_g.eval()

eval_loss = 0.
eval_acc = 0.
batch_size = 10

test_dataset_g = MyDataset_G(csv_path=TEST_CSV_PATH,
                             image_path=TEST_IMG_PATH,
                             data_transforms=data_transforms,
                             dataset='test')

test_loader_g = DataLoader(test_dataset_g,
                           batch_size=batch_size,
                           shuffle=True)

# test_dataset_l = MyDataset_L(csv_path="/home/xf/ISIC-data2017/test.csv",
#                              image_path="/home/xf/ISIC-data2017/test",
#                              data_transforms=data_transforms,
#                              dataset='test')

# test_loader_l = DataLoader(test_dataset_l,
#                            batch_size=batch_size,
#                            shuffle=True)

dataset_size = len(test_dataset_g)

begin_time = time.time()

# 局部方法部分
# running_corrects = 0
# class0 = 0
# class1 = 0
# class2 = 0
# class0all = 0
# class1all = 0
# class2all = 0

# inputs = []
# for data in test_loader_l:
#     # get the inputs
#     inputs, labels = data

#     input1 = inputs[0].to(device)
#     input2 = inputs[1].to(device)
#     input3 = inputs[2].to(device)

#     labels = labels.to(device)

#     output1 = model_l(input1)
#     output2 = model_l(input2)
#     output3 = model_l(input3)

#     out_tensor = torch.randn(batch_size, 3)
#     out_tensor = out_tensor.to(device)
#     i = 0
#     while i < batch_size:
#         j = 0
#         while j < 3:
#             temp = output1.data[i, j]
#             if output2.data[i, j] > temp:
#                 temp = output2.data[i, j]
#             if output3.data[i, j] > temp:
#                 temp = output3.data[i, j]
#             out_tensor[i, j] = temp
#             j = j + 1
#         i = i + 1

#     preds_value, preds = torch.max(out_tensor, 1)
#     class0all += torch.sum(labels.data == 0)
#     class1all += torch.sum(labels.data == 1)
#     class2all += torch.sum(labels.data == 2)

#     for k in range(batch_size):
#         if labels.data[k] == 0:
#             if preds[k] == 0:
#                 class0 += 1
#         if labels.data[k] == 1:
#             if preds[k] == 1:
#                 class1 += 1
#         if labels.data[k] == 2:
#             if preds[k] == 2:
#                 class2 += 1

#     running_corrects += torch.sum(preds == labels.data)

# acc0 = float(class0) / class0all
# acc1 = float(class1) / class1all
# acc2 = float(class2) / class2all

# print('{} all:{} testnum:{} Acc: {:.4f}'.format('class0', class0all, class0, acc0))
# print('{} all:{} testnum:{} Acc: {:.4f}'.format('class1', class1all, class1, acc1))
# print('{} all:{} testnum:{} Acc: {:.4f}'.format('class2', class2all, class2, acc2))
# epoch_acc = float(running_corrects) / dataset_size
# print('{}  Acc: {:.4f} Time: {:.4f}s'.format('test_l', epoch_acc, time.time() - begin_time))

running_corrects = 0
class0 = 0
class1 = 0
class2 = 0
class0all = 0
class1all = 0
class2all = 0
for data in test_loader_g:
    # get the inputs
    input0, labels = data

    input0 = input0.to(device)
    labels = labels.to(device)

    outputs = model_g(input0)

    preds_value, preds = torch.max(outputs, 1)
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

print('{} all:{} testnum:{} Acc: {:.4f}'.format('class0', class0all, class0, float(class0) / class0all))
print('{} all:{} testnum:{} Acc: {:.4f}'.format('class1', class1all, class1, float(class1) / class1all))
print('{} all:{} testnum:{} Acc: {:.4f}'.format('class2', class2all, class2, float(class2) / class2all))

epoch_acc = float(running_corrects) / dataset_size
print('{}  Acc: {:.4f} Time: {:.4f}s'.format('test_g', epoch_acc, time.time() - begin_time))
