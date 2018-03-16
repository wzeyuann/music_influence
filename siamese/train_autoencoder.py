import numpy as np
import os
from keras.models import Model
from keras.layers import Input
from keras.layers import Conv2D, MaxPooling2D, UpSampling2D
from keras.optimizers import Adadelta
from keras.callbacks import Callback, ModelCheckpoint, EarlyStopping
import matplotlib.pyplot as plt
import pickle

# Set seed
SEED = 1234
np.random.seed(SEED)

INPUT_SHAPE = (132, 1300, 1)
BATCH_SIZE = 8
MODEL_SAVE_NAME = "autoencoder.model"
FEATURE_DIR = "/home/ubuntu/music_influence/data/features/mel_spec_first/"
# FEATURE_DIR = "../data/features/mel_spec_first/"

# Train-val split
#all_filenames = os.listdir(FEATURE_DIR)
#train, val = train_test_split(all_filenames, test_size=0.25, random_state=SEED)
train, val = np.load('autoencoder_split/train_filenames.npy'), np.load('autoencoder_split/val_filenames.npy')

# Architecture adapted from 
# https://blog.keras.io/building-autoencoders-in-keras.html and
input_img = Input(INPUT_SHAPE)

# Encoder
encoded = Conv2D(16, (3, 3), input_shape=INPUT_SHAPE, activation='relu', padding='same')(input_img)
encoded = MaxPooling2D((2, 2), padding='same')(encoded)
encoded = Conv2D(8, (3, 3), input_shape=INPUT_SHAPE, activation='relu', padding='same')(encoded)
encoded = MaxPooling2D((2, 2), padding='same')(encoded)
encoded = Conv2D(8, (3, 3), input_shape=INPUT_SHAPE, activation='relu', padding='same')(encoded)
encoded = MaxPooling2D((2, 2), padding='same')(encoded)
encoder = Model(input=input_img, output=encoded)

# Decoder
decoded = Conv2D(8, (3, 3), activation='relu', padding='same')(encoded)
decoded = UpSampling2D((2, 2))(decoded)
decoded = Conv2D(8, (3, 3), activation='relu', padding='same')(decoded)
decoded = UpSampling2D((2, 2))(decoded)
decoded = Conv2D(16, (3, 3), activation='relu')(decoded)
decoded = UpSampling2D((2, 2))(decoded)
# TODO:
decoded = Conv2D(1, (3, 3), activation='relu', padding='same')(decoded)

# Create learning rate schedule and add it to the optimizer of choice
learning_rate = 1.0
epochs = 50
decay_rate = learning_rate / epochs
adadelta = Adadelta(lr=learning_rate, rho=0.95, epsilon=1e-08, decay=decay_rate)

callbacks = [
    EarlyStopping(monitor='val_loss', patience=5),
    ModelCheckpoint(MODEL_SAVE_NAME, monitor='val_loss', save_best_only=True, verbose=0),
]

# Build the full autoencoder
autoencoder = Model(input_img, decoded)
autoencoder.compile(optimizer=adadelta, loss='mean_squared_error')
autoencoder.summary()

def generator(paths, batch_size=BATCH_SIZE):
    """
        Infinite generator for batches of data
    """
    batch = []
    
    while True:            
        for path in paths:
            mel_spec = np.load(FEATURE_DIR + path)
            # Add zero padding
            mel_spec_padded = np.zeros(INPUT_SHAPE[:2])
            mel_spec_padded[:mel_spec.shape[0], :mel_spec.shape[1]] = mel_spec
            batch.append(mel_spec_padded[:, :, np.newaxis])
            
            if len(batch) == batch_size:
                yield np.array(batch), np.array(batch)
                batch = []

# Train model
history = autoencoder.fit_generator(
                    generator = generator(train),
                    epochs = 100,
                    steps_per_epoch = len(train)//BATCH_SIZE,
                    validation_data = generator(val),
                    validation_steps = len(val)//BATCH_SIZE,
                    callbacks=callbacks,
                    shuffle=True,
                    verbose=1
            )

# Save history callback object
with open('history.pickle', 'wb') as handle:
    pickle.dump(history.history, handle)
