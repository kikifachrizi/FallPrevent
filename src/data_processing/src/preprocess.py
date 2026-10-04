import numpy as np
import cv2
import os

HEIGHT = 180
WIDTH = 240
RESIZE = 64
SEQ_LEN = 90

# ===== LOAD BIN =====
def load_bin(path):
    data = np.fromfile(path, dtype=np.float32)
    frames = data.reshape(-1, HEIGHT, WIDTH)
    return frames

# ===== PREPROCESS 1 SEQUENCE =====
def preprocess_sequence(frames):
    processed = []

    for i in range(1, len(frames)):
        curr = np.nan_to_num(frames[i])
        prev = np.nan_to_num(frames[i-1])

        # 🔥 FIX ORIENTATION
        curr = np.flipud(np.fliplr(curr))
        prev = np.flipud(np.fliplr(prev))

        # 🔥 CLAMP
        curr = np.clip(curr, 100, 4000)
        prev = np.clip(prev, 100, 4000)

        # 🔥 DIFFERENCING
        diff = curr - prev

        # 🔥 RESIZE
        diff = cv2.resize(diff, (RESIZE, RESIZE))

        # 🔥 NORMALIZE
        diff = diff / 4000.0

        processed.append(diff)

    return np.array(processed)  # (T-1, 64, 64)

# ===== BUILD DATASET =====
def build_dataset(folder, label):
    X = []
    y = []

    for file in os.listdir(folder):
        if file.endswith(".bin"):
            path = os.path.join(folder, file)

            frames = load_bin(path)

            if len(frames) < SEQ_LEN:
                continue  # skip data jelek

            seq = preprocess_sequence(frames)

            X.append(seq)
            y.append(label)

    return X, y

# ===== MAIN =====

fall_path = "/home/kiki/dataset/fall"
non_fall_path = "/home/kiki/dataset/non_fall"

X_fall, y_fall = build_dataset(fall_path, 1)
X_non, y_non = build_dataset(non_fall_path, 0)

X = np.array(X_fall + X_non)
y = np.array(y_fall + y_non)

print("Dataset shape:", X.shape)
print("Labels shape:", y.shape)

# SAVE
np.save("X.npy", X)
np.save("y.npy", y)

print("Dataset saved!")