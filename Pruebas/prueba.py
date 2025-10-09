from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
import tensorflow as tf
from sklearn import datasets
import matplotlib.pyplot as plt


data = datasets.load_breast_cancer()
X = data.data.astype(np.float32)
y = data.target.astype(np.float32)

# 1) Split con estratificación
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 2) Escalado: fit SOLO en train
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# 3) Modelo
D = X_train.shape[1]
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(D,)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 4) Entrenar SIEMPRE con X_train_scaled
model.fit(X_train_scaled, y_train, epochs=50, batch_size=32, verbose=0, validation_split=0.2)

# 5) Evaluar SIEMPRE con escalados
print("Train:", model.evaluate(X_train_scaled, y_train, verbose=0))
print("Test :", model.evaluate(X_test_scaled,  y_test,  verbose=0))

plt.plot(model.history.history['loss'], label='loss')
plt.plot(model.history.history['val_loss'], label='val_loss')