# Panduan Arducam ToF: ROS 2, Foxglove, dan Rekam Data

	Panduan ini berdasarkan history terminal Raspberry Pi dan kode publisher lokal. Setup memakai ROS 2 Jazzy dengan `ROS_DOMAIN_ID=42`. History mencatat perintah yang pernah dijalankan, bukan bukti bahwa setiap perintah berhasil.

## 1. Jalankan kamera di Raspberry Pi
```bash

cd ~/Arducam_tof_camera/ros2_publisher

source /opt/ros/jazzy/setup.bash

source install/setup.bash

export ROS_DOMAIN_ID=42

ros2 run arducam_rclpy_tof_pointcloud tof_pointcloud

```

Biarkan terminal ini berjalan selama menampilkan atau merekam data.  
Domain yang dipakai PC dan Pi adalah `42` (dikonfirmasi 13 Okt 2026). Bila `.bashrc` Pi masih berisi `7`, ganti ke `42`; domain berbeda membuat PC tidak melihat topik Pi.
Jika muncul error izin akses kamera, hentikan percobaan sebelumnya, lalu jalankan dari terminal yang sama:
```bash

sudo -E ./run.sh

```

## 2. Cek aliran data
Buka terminal lain di Raspberry Pi:
```bash

source /opt/ros/jazzy/setup.bash

export ROS_DOMAIN_ID=42

ros2 topic list

ros2 topic hz /point_cloud

```

Publisher mengirim dua topic:
- `/point_cloud`: titik 3D, dengan tipe `sensor_msgs/msg/PointCloud2`.

- `/depth_frame`: array kedalaman dalam meter, dengan tipe `std_msgs/msg/Float32MultiArray`.

Tekan `Ctrl+C` untuk menghentikan pengecekan frekuensi topic. Kamera tetap berjalan di terminal pertama.

## 3. Tampilkan di laptop lewat Foxglove

Dengan kamera tetap berjalan, buka terminal lain di Raspberry Pi:
```bash

source /opt/ros/jazzy/setup.bash

export ROS_DOMAIN_ID=42

ros2 run foxglove_bridge foxglove_bridge --ros-args -p port:=9090

```

Biarkan bridge berjalan. Untuk melihat alamat IP Pi, gunakan terminal terpisah:

```bash

hostname -I

```

Di Foxglove pada laptop:

1. Buat koneksi Foxglove WebSocket ke `ws://<IP_PI>:9090`. Ganti `<IP_PI>` dengan alamat Pi yang bisa diakses dari laptop.

2. Tambahkan panel **3D**.

3. Pilih topic `/point_cloud`.

4. Gunakan frame `map`, sesuai header point cloud pada kode publisher.

Laptop harus bisa menjangkau Pi pada port `9090`.

## 4. Rekam data di Raspberry Pi
Dengan kamera tetap berjalan, buka terminal lain:
```bash

source /opt/ros/jazzy/setup.bash

export ROS_DOMAIN_ID=42

ros2 bag record -o ~/rekaman_tof_baru /point_cloud /depth_frame

```

Tekan `Ctrl+C` untuk menghentikan dan menyelesaikan rekaman. Gunakan nama folder baru untuk setiap sesi rekaman.

Rekaman lama tersedia di:
```text

/home/diagonalrobotics/record_data_thesis_nanas/baseline/

├── baseline_0.mcap

└── metadata.yaml

```

Perintah playback yang pernah digunakan:
```bash

source /opt/ros/jazzy/setup.bash

export ROS_DOMAIN_ID=42

cd ~/record_data_thesis_nanas/baseline

ros2 bag play baseline_0.mcap

```

Hentikan publisher kamera saat menampilkan rekaman agar data live dan playback tidak bercampur pada topic yang sama.