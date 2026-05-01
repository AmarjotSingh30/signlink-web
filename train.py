import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, Dropout
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from keras.utils import to_categorical
import os

# 1. Load the Dataset
csv_file = 'hand_landmarks.csv'
print(f"Loading data from {csv_file}...")
# Added encoding bypass and .dropna() to remove any corrupted blank rows
data = pd.read_csv(csv_file, encoding='unicode_escape').dropna()

# Extract labels (Column 0) and features (Columns 1 to 63)
X = data.iloc[:, 1:].values
y = data.iloc[:, 0].values

# 2. Encode Labels (Converts 'A', 'B', 'C' into 0, 1, 2)
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
y_categorical = to_categorical(y_encoded)
num_classes = y_categorical.shape[1]

# 3. Split the Data (80% for training, 20% for testing)
X_train, X_test, y_train, y_test = train_test_split(X, y_categorical, test_size=0.2, random_state=42)

# 4. Build the Dense Neural Network
model = Sequential()
# Input layer matches the 63 coordinates (21 landmarks * 3 axes)
model.add(Dense(128, activation='relu', input_shape=(63,)))
model.add(Dropout(0.2)) # Prevents overfitting
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(32, activation='relu'))
model.add(Dense(num_classes, activation='softmax')) # Output layer matches your number of signs

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 5. Train the Model
print("Starting training...")
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))

# 6. Save the Model and the Label Classes
if not os.path.exists("model"):
    os.makedirs("model")

# Save Keras Model
with open("model/model-mp.json", "w") as json_file:
    json_file.write(model.to_json())
model.save_weights('model/model-mp.h5')

# Save the encoder classes so app.py knows what letters the model is predicting
np.save('model/classes.npy', encoder.classes_)

print("Model and classes saved successfully to the 'model' folder!")