"""
全局特征,将整个图像压缩到224*224后放入预训练的ResNet-50中
损失在第35个周期左右收敛
得到全局训练的模型
"""

import torch
from torch import nn
import torchvision.models as models
from dataset_G import MyDataset_G, DataLoader
from torchvision import transforms
import time
import torch.optim as optim
import os
from tensorboardX import SummaryWriter

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
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

batch_size = 30

num_class = 3
num_epochs = 100

writer = SummaryWriter('./log', comment='Liner')

image_datasets = {x: MyDataset_G(csv_path="/home/xf/ISIC-data2017/" + x + ".csv",
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
# scheduler = lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.2)

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
            inputs = inputs.to(device)
            labels = labels.to(device)

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward
            outputs = model(inputs)
            _, preds = torch.max(outputs.data, 1)
            loss = criterion(outputs, labels)

            # backward + optimize only if in training phase
            if phase == 'train':
                loss.backward()
                optimizer.step()
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
            writer.add_scalar('loss/epoch', epoch_loss, epoch)
            if epoch == 30:
                optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
            if epoch == 60:
                optimizer = optim.SGD(model.parameters(), lr=0.0001, momentum=0.9)
            if (epoch+1) % 10 == 0:
                if not os.path.exists('/home/xf/model'):
                    os.makedirs('/home/xf/model')
                torch.save(model, '/home/xf/model/resnet50_epoch{}_gm.pkl'.format(epoch + 1))
        # deep copy the model
        if phase == 'val':
            writer.add_scalar('acc/epoch', epoch_acc, epoch)
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
torch.save(model, "/home/xf/model/isic_resnet50_gm.pkl")

"""
DataLoader(dataset, batch_size=1, shuffle=False, sampler=None, 
num_workers=0, collate_fn=default_collate, pin_memory=False, 
drop_last=False)

dataset：加载的数据集(Dataset对象) 
batch_size：batch size 
shuffle:：是否将数据打乱 
sampler： 样本抽样，后续会详细介绍 
num_workers：使用多进程加载的进程数，0代表不使用多进程 
collate_fn： 如何将多个样本数据拼接成一个batch，一般使用默认的拼接方式即可 
pin_memory：是否将数据保存在pin memory区，pin memory中的数据转到GPU会快一些 
drop_last：dataset中的数据个数可能不是batch_size的整数倍，drop_last为True会将多出来不足一个batch的数据丢弃

"""
