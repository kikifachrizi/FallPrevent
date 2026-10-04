import numpy as np
import matplotlib.pyplot as plt

file_path = "/home/kiki/dataset/fall/seq_1.bin"
height = 180
width = 240

data = np.fromfile(file_path, dtype=np.float32)

frame_size = height * width
num_frames = data.size // frame_size

frames = data.reshape((num_frames, height, width))

plt.ion()

for i in range(num_frames):
    frame = np.nan_to_num(frames[i])

    # 🔥 FIX ORIENTATION
    frame = np.flipud(np.fliplr(frame))  # vertical + horizontal

    plt.clf()
    plt.imshow(frame, cmap='jet')
    plt.title(f"Frame {i}")
    plt.colorbar()
    plt.pause(0.1)

plt.ioff()
plt.show()