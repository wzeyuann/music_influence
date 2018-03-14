from keras.layers import Input, Conv2D, Lambda, merge, Dense, Flatten, MaxPooling2D
from keras.models import Model, Sequential
from keras.regularizers import l2
from keras import backend as K
from keras.optimizers import SGD, Adam
from keras.losses import binary_crossentropy
from keras.callbacks import EarlyStopping, ModelCheckpoint
import numpy.random as random
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import pickle

# Set seed
random.seed(1234)

FEATURE_DIR = '/n/regal/rush_lab/xue/mel_spec_first/'

# Use 128x128 samples (~3 second samples) to speed up training
# TODO: Use full 30 second samples
INPUT_DIM = (128, 128, 1)
# Number of frames to sample
N_FRAMES = INPUT_DIM[1]

MODEL_SAVE_NAME = 'Siamese_FirstTrack_{}x{}.model'.format(INPUT_DIM[0], INPUT_DIM[1])

# Training configurations
BATCH_SIZE = 32

# Adapted from https://sorenbouma.github.io/blog/oneshot/
input_shape = INPUT_DIM
left_input = Input(input_shape)
right_input = Input(input_shape)

# Build convnet to use in each siamese 'leg'
convnet = Sequential()
convnet.add(Conv2D(64,(10,10),activation='relu',input_shape=input_shape, kernel_regularizer=l2(2e-4)))
convnet.add(MaxPooling2D()) 
convnet.add(Conv2D(128,(7,7),activation='relu', kernel_regularizer=l2(2e-4)))
convnet.add(MaxPooling2D())
convnet.add(Conv2D(128,(4,4),activation='relu',kernel_regularizer=l2(2e-4)))
convnet.add(MaxPooling2D())
convnet.add(Conv2D(256,(4,4),activation='relu',kernel_regularizer=l2(2e-4)))
convnet.add(Flatten())
convnet.add(Dense(4096,activation="sigmoid",kernel_regularizer=l2(1e-3)))

# Encode each of the two inputs into a vector with the convnet
encoded_l = convnet(left_input)
encoded_r = convnet(right_input)

# Merge two encoded inputs with the l1 distance between them
L1_distance = lambda x: K.abs(x[0]-x[1])
both = merge([encoded_l,encoded_r], mode = L1_distance, output_shape=lambda x: x[0])
prediction = Dense(1,activation='sigmoid')(both)
siamese_net = Model(input=[left_input,right_input],output=prediction)
#optimizer = SGD(0.0004,momentum=0.6,nesterov=True,decay=0.0003)

optimizer = Adam(0.00006)
siamese_net.compile(loss="binary_crossentropy",
                    optimizer=optimizer,
                    metrics=['accuracy'])

siamese_net.count_params()

# Create lookup dictionary mapping file id to artist id
file2id = {}

for filename in os.listdir(FEATURE_DIR):
    file2id[filename] = int(filename.split('.npy')[0]) 

id2file = {id:filename for (filename, id) in file2id.items()}

# Load positive and negative influence pairs
pos_train_rel, pos_val_rel, neg_train_rel, neg_val_rel = np.load('relationships/pos_train_rel.npy'), np.load('relationships/pos_val_rel.npy'), np.load('relationships/neg_train_rel.npy'), np.load('relationships/neg_val_rel.npy')

def sample_frames(melspec, n_frames):
    """Sample n_frames (contiguous) from a melspec representation"""
    total_frames = melspec.shape[1]
    sample_range = range(0, total_frames - n_frames + 1)
    sample_index = random.choice(sample_range)
    
    return melspec[:, sample_index:sample_index + n_frames]

def generator(pos_ex, neg_ex, batch_size=BATCH_SIZE, n_frames=N_FRAMES):
    """
        Infinite generator for batches of data containing equal numbers of
        positive and negative pairs of mel-spec sample pairs with influence
        relationships present and not present
    """
    # Create binary labels for examples
    labels = np.concatenate((np.ones(len(pos_ex)), np.zeros(len(neg_ex))))
    all_ex = list(zip(np.concatenate((pos_ex, neg_ex)), labels))
    examples, labels = zip(*all_ex)
    
    batch_first, batch_second, batch_Y = [], [], []
    
    while True:
        random.shuffle(all_ex)
        examples, labels = zip(*all_ex)
            
        for example, label in zip(examples, labels):
            # Extract sample of size N_FRAMES from mel_spec representation
            # for each example in pair
            pair_first, pair_second = [sample_frames(np.load(FEATURE_DIR + id2file[id]), n_frames) for id in example]
            batch_first.append(pair_first[:, :,np.newaxis])
            batch_second.append(pair_second[:, :, np.newaxis])
            batch_Y.append(label)
                
            if len(batch_first) == batch_size:
                yield [np.array(batch_first), np.array(batch_second)], np.array(batch_Y)
                batch_first, batch_second, batch_Y = [], [], []

# Define callbacks
early_stopping = EarlyStopping(monitor='val_loss', patience=5)
checkpoint = ModelCheckpoint(MODEL_SAVE_NAME, monitor='val_acc', verbose=1, save_best_only=True, mode='max')

history = siamese_net.fit_generator(generator = generator(pos_train_rel, neg_train_rel),
		    epochs = 100,
                    steps_per_epoch = len(pos_train_rel)//BATCH_SIZE,
                    validation_data = generator(pos_val_rel, neg_val_rel),
                    validation_steps = len(pos_val_rel)//BATCH_SIZE,
                    callbacks=[early_stopping, checkpoint])

# Save history callback object
with open('history.pickle', 'wb') as handle:
    pickle.dump(history, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Plots of training history
plt.plot(history.history['val_acc'])
plt.title('Validation Accuracy')
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.savefig('val_accuracy.png')
plt.close()

plt.plot(history.history['acc'])
plt.title('Training Accuracy')
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.savefig('train_accuracy.png')
plt.close()

plt.plot(history.history['val_loss'])
plt.title('Validation Loss')
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.savefig('val_loss.png')
plt.close()

plt.plot(history.history['loss'])
plt.title('Training Loss')
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.savefig('train_loss.png')
plt.close()
