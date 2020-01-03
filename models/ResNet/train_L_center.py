"""
提取局部特征,从每个图像中心取3个224*224大小的块放入预训练的ResNet-50中
损失在第个周期左右收敛
得到局部训练的模型
"""

import torch
from torch import nn
import torchvision.models as models
from dataset_L_center import MyDataset_L, DataLoader
from torchvision import transforms
import time
import torch.optim as optim
import os
from tensorboardX import SummaryWriter
from datetime import datetime

data_transforms = {
    'train': transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

batch_size = 30
num_class = 3
num_epochs = 100

TIMESTAMP = "{0:%Y-%m-%dT%H-%M-%S/}".format(datetime.now())
writer = SummaryWriter('./log/' + TIMESTAMP, comment='centerline')

image_datasets = {x: MyDataset_L(csv_path="/home/xf/ISIC-data2017/" + x + ".csv",
                                 image_path="/home/xf/ISIC-data2017/" + x,
                                 data_transforms=data_transforms,
                                 dataset=x) for x in ['train', 'val']}

# wrap your data and label into Tensor
dataloders = {x: DataLoader(image_datasets[x],
                            batch_size=batch_size,
                            shuffle=True) for x in ['train', 'val']}
# train_dataloader = DataLoader(dataset=train_dataset)
# val_dataloader = DataLoader(dataset=val_dataset)
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}

# train_dataset_size = len(train_dataset)
# val_dataset_size = len(val_dataset)

# 调用模型
model = models.resnet50(pretrained=True)
# 提取fc层中固定的参数
fc_features = model.fc.in_features
# 修改类别为3
model.fc = nn.Linear(fc_features, 3)

model = model.to(device)
# define cost function
criterion = nn.CrossEntropyLoss()
# Observe that all parameters are being optimized
optimizer = optim.SGD(model.parameters(), lr=0.005, momentum=0.9)

# train model
since = time.time()

best_model_wts = model.state_dict()
best_acc = 0.0

for epoch in range(num_epochs):
    begin_time = time.time()
    count_batch = 0
    class0 = 0
    class1 = 0
    class2 = 0
    print('Epoch {}/{}'.format(epoch + 1, num_epochs))
    print('-' * 10)

    # Each epoch has a training and validation phase
    for phase in ['train', 'val']:
        if phase == 'train':
            model.train(True)  # Set model to training mode
            batch_size = 30
        else:
            model.train(False)  # Set model to evaluate mode
            batch_size = 15

        running_loss = 0.0
        running_corrects = 0

        for inputs, labels in dataloders[phase]:
            count_batch += 1
            # get the inputs
            labels = labels.to(device)
            # zero the parameter gradients
            optimizer.zero_grad()
            i = 0
            while i < 3:
                input0 = inputs[i].to(device)
                output0 = model(input0)
                _, preds = torch.max(output0.data, 1)  # 找出每行中最大的那个类
                loss = criterion(output0, labels)
                # backward + optimize only if in training phase
                if phase == 'train':
                    loss.backward()
                    optimizer.step()
                i = i + 1
                # statistics

            running_loss += float(loss.item())
            running_corrects += torch.sum(preds == labels.data)
            if phase == 'val':
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
            # print result every 10 batch
            if count_batch % 10 == 0:
                batch_loss = float(running_loss) / (batch_size * count_batch)
                batch_acc = float(running_corrects) / (batch_size * count_batch)
                print('{} Epoch [{}] Batch [{}] Loss: {:.4f} Acc: {:.4f} Time: {:.4f}s'. \
                      format(phase, epoch + 1, count_batch, batch_loss, batch_acc, time.time() - begin_time))
                begin_time = time.time()
            del inputs
            del labels

        epoch_loss = float(running_loss) / dataset_sizes[phase]
        epoch_acc = float(running_corrects) / dataset_sizes[phase]
        print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase, epoch_loss, epoch_acc))

        # save model
        if phase == 'train':
            writer.add_scalar('loss_center/epoch', epoch_loss, epoch)
            if (epoch + 1) % 5 == 0:
                if not os.path.exists('/home/xf/model'):
                    os.makedirs('/home/xf/model')
                torch.save(model, '/home/xf/model/resnet18_epoch{}_l_3c.pkl'.format(epoch + 1))
        # # 改变学习率
        # if phase == 'train':
        #     if epoch == 20:
        #         optimizer = optim.SGD(model.parameters(), lr=0.005, momentum=0.9)
        # deep copy the model
        if phase == 'val':
            writer.add_scalar('acc0/epoch', float(class0) / 78, epoch)
            writer.add_scalar('acc1/epoch', float(class1) / 30, epoch)
            writer.add_scalar('acc2/epoch', float(class2) / 42, epoch)
            if epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = model.state_dict()

writer.close()
time_elapsed = time.time() - since
print('Training complete in {:.0f}m {:.0f}s'.format(
    time_elapsed // 60, time_elapsed % 60))
print('Best val Acc: {:4f}'.format(best_acc))

# load best model weights
model.load_state_dict(best_model_wts)

# save best model
torch.save(model, "/home/xf/model/isic_resnet18_l_3c.pkl")
