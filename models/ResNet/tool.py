import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import csv
from torchvision import transforms
from torch.autograd import Variable
import time
import random

from tensorboardX import SummaryWriter

import tensorflow as tf

class0 = 0.
acc = 0.
class0 = 94
classall0 = 117
acc = class0 / classall0
print('{} all:{} testnum:{} Acc: {:.4f}'.format('class0', classall0, class0, acc))
