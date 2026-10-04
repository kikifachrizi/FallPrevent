import numpy as np
import matplotlib.pyplot as plt

# load
X = np.load("X.npy")
y = np.load("y.npy")

print("X shape:", X.shape)
print("y shape:", y.shape)

# ambil 1 sample
sample = X[0]

print("1 sample shape:", sample.shape)
print("label:", y[0])

# visualisasi sequence
plt.ion()

for i in range(len(sample)):
    plt.clf()
    plt.imshow(sample[i], cmap='jet')
    plt.title(f"Frame {i}")
    plt.colorbar()
    plt.pause(0.05)

plt.ioff()
plt.show()