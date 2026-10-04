# tof_tools: skrip pengambilan data ToF

**Dokumen ini hanya cara menjalankan skrip.** Protokol (partisipan, area uji dan tes grid, kriteria klip valid, skema dataset, keputusan terbuka) ada di `Skenario_Uji_Pengambilan_Data_ToF_36_Klip.md`. Bila perintah di dua dokumen berbeda, ikuti README ini.

**Status pengujian:** skrip bash **belum pernah dijalankan di Pi lo** (sandbox tidak punya ROS). Hanya dicek sintaks (`bash -n`). `extract_clips.py` sudah diuji dengan bag MCAP **sintetis** (Image 16UC1/32FC1 + PointCloud2 terorganisir), belum dengan data driver Arducam asli.

**Tidak ada package ROS baru.** Yang dipakai: driver Arducam (`arducam_rclpy_tof_pointcloud`), `ros2 bag` bawaan, dan skrip bash ini. Satu-satunya instalasi tambahan: plugin MCAP bila `-s mcap` error (`sudo apt install ros-jazzy-rosbag2-storage-mcap`) dan `pip install mcap mcap-ros2-support numpy` untuk `extract_clips.py`.

## Isi folder

| File | Dijalankan di | Fungsi |
|---|---|---|
| `config.sh` | (di-source skrip lain) | Satu tempat untuk topik, FPS, durasi buffer, folder data. **Edit sekali.** |
| `check_topics.sh` | Pi | Daftar topik, QoS, encoding, ukuran, `fields` PointCloud2, hz dan bandwidth riil |
| `rec_clip.sh` | Pi | Rekam **1 klip = 1 bag**, dengan aba-aba GO dan catatan waktu (`cue_log.csv`) |
| `validate_clip.sh` | Pi | Cek otomatis cepat: bag terbaca, durasi, jumlah pesan |
| `run_rep.sh` | Pi | Loop 9 klip (N1..N8b) untuk 1 partisipan 1 rep, dengan validasi dan ulang otomatis (maks 3x) |
| `extract_clips.py` | PC/Pi | Ubah bag MCAP jadi `depth.npy`, `t.npy`, `meta.json` (+ peta lantai dari klip REF) |
| `templates/clips_template.csv` | PC | 36 baris klip sudah terisi (id, kode, label, jenis jatuh, kecepatan, arah). Sisanya diisi saat anotasi |
| `templates/sessions_template.csv` | PC | Header + 2 baris contoh sesi (tinggi/pitch kamera, pakaian, dll.) |

## Setup sekali (di Pi)

```bash
scp -r tof_tools <user>@<ip_pi>:~/
ssh <user>@<ip_pi>
cd ~/tof_tools && chmod +x *.sh
```

**Terminal 1: driver (biarkan hidup)**
```bash
source /opt/ros/jazzy/setup.bash
source ~/Arducam_tof_camera/ros2_publisher/install/setup.bash
ros2 run arducam_rclpy_tof_pointcloud tof_pointcloud
```

**Terminal 2: cek topik, lalu isi config**
```bash
cd ~/tof_tools
./check_topics.sh
nano config.sh      # isi TOPIC_DEPTH, TOPIC_CLOUD, FPS_NOMINAL
```
Lihat di output: `height/width` depth harus 180/240; `encoding` (16UC1 = mm, 32FC1 = meter); PointCloud2 terorganisir bila `height=180`, `width=240`; `bw` untuk perkiraan ukuran per klip.

## Alur penggunaan

**1. Uji teknis (sebelum sesi sungguhan)**
```bash
./rec_clip.sh TEST_1 3
./validate_clip.sh TEST_1 3
```
Ulangi 2-3x, juga dengan `REC_CLOUD=0` dan `REC_CLOUD=1` di config. Bandingkan fps efektif dan ukuran. Pilih mana yang dipakai. Hapus `~/tof_data/bags/TEST_*` setelahnya.

**2. Klip REF (tanpa orang, per sesi)**
```bash
./rec_clip.sh P1S1_REF 0
```

**3. Rekam per rep**
```bash
./run_rep.sh P1 1     # P1 rep 1: N1 -> N8b (urutan tetap)
./run_rep.sh P1 2     # P1 rep 2
```
Urutan lain diatur operator: tekan `s` untuk melewati klip, atau rekam klip tertentu langsung dengan `./rec_clip.sh <nama> <detik_aksi>`. Durasi aksi: N1 5, N2 5, N3 3, N4 1, N5 3, N6 1, N7 3, N8a 1, N8b 3.
Per klip: Enter = mulai, `s` = lewati, `q` = keluar. Partisipan **diam** sampai terdengar/terlihat `>>> GO <<<`, lalu beraksi, lalu **tahan posisi akhir** sampai `SELESAI`. Setelah itu skrip menjalankan validasi otomatis dan menanyakan "valid [y/n]" (cek aksi benar, tubuh tidak terpotong, tidak ada orang lain). Jawaban `n` mengganti nama bag jadi `_x1`, `_x2`, ... dan mengulang slot yang sama.

Hasil di `~/tof_data/`: `bags/` (1 folder per klip), `cue_log.csv` (waktu GO per klip, jam sistem Pi), `clip_log.csv` (keputusan valid/tidak), `last_rec.log` (output `ros2 bag record` terakhir, untuk debug).

**4. Akhir sesi: backup**
```bash
rsync -av ~/tof_data/ <user>@<ip_pc>:/path/backup_tof/
```

**5. Di PC: anotasi dan ekstraksi**
```bash
pip install mcap mcap-ros2-support numpy
python3 extract_clips.py --bags ~/backup_tof/bags --out ~/dataset_tof_fall \
    --depth-topic /TOPIK_DEPTH --cloud-topic /TOPIK_CLOUD --cloud-first 30
```
`--cloud-first 30` menyimpan 30 frame cloud pertama per klip (berguna untuk klip REF, untuk fit bidang lantai dan pitch). Hilangkan kedua opsi cloud bila tidak dipakai. Klip `_xN` otomatis dilewati. Salin `templates/*.csv` ke folder dataset, isi `t_onset_s` dan `t_end_s` dari Foxglove, lalu lengkapi `n_frames`/`fps_est` dari `clips_index.csv`. Langkah rinci mengisi `clips.csv`: Skenario, Bagian 5.

## Hal yang perlu lo ketahui

- **Ambang `validate_clip.sh`** (durasi ±1,5 dtk, pesan ≥ 90% × `FPS_NOMINAL` × durasi) adalah usulan awal. `FPS_NOMINAL` harus angka riil dari `ros2 topic hz`, bukan spek.
- **Format output `ros2 bag info`** yang dibaca `validate_clip.sh` diasumsikan seperti di Jazzy ("Duration:", "Topic: ... Count: N"). Jika `HASIL: GAGAL ... durasi tidak terbaca`, tempel output `ros2 bag info` ke chat dan skripnya disesuaikan.
- **`timeout -s INT` + `ros2 bag record`** belum terbukti menutup bag bersih di setup lo. `rec_clip.sh` memeriksa `metadata.yaml` sebagai penanda; bila hilang, muncul PERINGATAN.
- **Amplitude tidak tersedia** (hanya depth Image dan PointCloud2), jadi `Q(x)` dihitung tanpa amplitude (pakai rasio piksel valid, edge-touch, kontinuitas).
- **Klip bernama `*REF*`** otomatis menghasilkan `ref/<nama>_floor_ref.npy` (median per-piksel, 0 = tidak valid).
- **Arah jatuh** di `clips_template.csv` (menjauhi kamera / menyamping) adalah usulan; ubah bila lo putuskan lain.
