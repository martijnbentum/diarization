import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.layers import Dense, concatenate

def generate_multidimensional_time_series(num_samples=100, seq_length=50, num_features=3):
    X = np.zeros((num_samples, seq_length, 3))
    y = np.zeros(num_samples)
    for i in range(num_samples):
        if np.random.random() < 0.5:
            X[i, :, 0] = np.sin(np.linspace(0, 4 * np.pi, seq_length))
            X[i, :, 1] = np.cos(np.linspace(0, 4 * np.pi, seq_length))
            X[i, :, 2] = np.cos(np.linspace(0, 4 * np.pi, seq_length))
            y[i] = 0  # Class A
        else:
            X[i, :, 0] = np.cos(np.linspace(0, 4 * np.pi, seq_length))
            X[i, :, 1] = np.sin(np.linspace(0, 4 * np.pi, seq_length))
            X[i, :, 2] = np.cos(np.linspace(0, 4 * np.pi, seq_length))
            y[i] = 1  # Class B
    return X, y

X, y = generate_multidimensional_time_series()
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, 
    random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, 
    random_state=42)

# model definition
#----------------- 

# Define the input shape for the time series data
input_shape = (X_train.shape[1], X_train.shape[2])  
# Shape: (sequence_length, num_features)

# Create two separate branches for the Conv1D layers
input_layer = Input(shape=input_shape)

# First Conv1D branch (e.g., for the sequence dimension)
conv1d_branch1 = Conv1D(filters=32, kernel_size=3, activation='relu')(input_layer)
maxpool1d_branch1 = MaxPooling1D(pool_size=2)(conv1d_branch1)

# Second Conv1D branch (e.g., for the feature dimension)
conv1d_branch2 = Conv1D(filters=64, kernel_size=3, activation='relu', 
    data_format='channels_last')(input_layer)
maxpool1d_branch2 = MaxPooling1D(pool_size=2)(conv1d_branch2)

# Concatenate the outputs from the two branches
concatenated = concatenate([maxpool1d_branch1, maxpool1d_branch2], axis=2)

# Flatten and add fully connected layers
flatten_layer = Flatten()(concatenated)
dense_layer1 = Dense(64, activation='relu')(flatten_layer)
output_layer = Dense(1, activation='sigmoid')(dense_layer1)

# Create the model
model = tf.keras.Model(inputs=input_layer, outputs=output_layer)

# Compile the model and specify loss, optimizer, and metrics
model.compile(loss='binary_crossentropy', optimizer='adam', 
    metrics=['accuracy'])

def train_model(model = model):
    history = model.fit(X_train_reshaped, y_train, 
        validation_data=(X_val_reshaped, y_val), epochs=20, batch_size=32)
    return history
    
