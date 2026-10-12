# tof_tools: skrip pengambilan data ToF

**Dokumen ini hanya cara menjalankan skrip.** Protokol (partisipan, area uji dan tes grid, kriteria klip valid, skema dataset, keputusan terbuka) ada di `Skenario_Uji_Pengambilan_Data_ToF_36_Klip.md`. Bila perintah di dua dokumen berbeda, ikuti README ini.

**Status pengujian (12 Okt 2026):** skrip bash diuji di PC dengan ROS 2 Jazzy dan publisher dummy `/depth_frame` (format sama dengan driver Arducam), **belum di Pi dengan driver asli**. `extract_clips.py` dan `qc_clip.py` diuji dengan bag pilot P1_R1 asli.

**Tidak ada package ROS baru.** Yang dipakai: driver Arducam (`arducam_rclpy_tof_pointcloud`), `ros2 bag` bawaan, dan skrip bash ini. Instalasi tambahan: plugin MCAP bila `-s mcap` error (`sudo apt install ros-jazzy-rosbag2-storage-mcap`), `bc` dan `python3-scipy` untuk `rec_clip.sh` dan `qc_clip.py` (`sudo apt install bc python3-scipy`), dan `pip install mcap mcap-ros2-support numpy` untuk `extract_clips.py`.

## Isi folder

| File | Dijalankan di | Fungsi |
|---|---|---|
| `config.sh` | (di-source skrip lain) | Satu tempat untuk topik, FPS, durasi buffer, folder data, intrinsik. Sudah terisi dari pilot P1_R1 |
| `check_topics.sh` | Pi | Daftar topik, QoS, ukuran, hz dan bandwidth riil. Untuk `/depth_frame` (Float32MultiArray): panjang data, piksel valid, jumlah level nilai (cek kuantisasi) |
| `rec_clip.sh` | Pi | Rekam **1 klip = 1 bag**. Menunggu recorder benar-benar merekam, lalu PRE → GO → aksi → POST. Waktu GO dicatat di `cue_log.csv` |
| `validate_clip.sh` | Pi | Cek otomatis cepat: bag terbaca, durasi, jumlah pesan, MCAP tertutup, lalu `qc_clip.py` (matikan dengan `QC=0`) |
| `qc_clip.py` | Pi/PC | QC isi klip: diam sebelum GO, reaksi, durasi turun cepat/pelan, tubuh menyentuh tepi, piksel tubuh invalid. Latar dari klip `*REF*` terbaru |
| `run_rep.sh` | Pi | Loop 9 klip (N1..N8b, atau terbalik dengan `rev`) untuk 1 partisipan 1 rep, dengan validasi dan ulang otomatis (maks 3x) |
| `extract_clips.py` | PC/Pi | Ubah bag MCAP (Image atau Float32MultiArray) jadi `depth.npy` (mm), `t.npy`, `meta.json` berisi intrinsik (+ peta lantai dari klip REF) |
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

**Terminal 2: cek topik**
```bash
cd ~/tof_tools
export ROS_DOMAIN_ID=7
./check_topics.sh
```
`config.sh` sudah terisi dari pilot P1_R1 (`TOPIC_DEPTH=/depth_frame`, `TOPIC_CLOUD=/point_cloud`, `REC_CLOUD=0`, `FPS_NOMINAL=30`, intrinsik). Ubah hanya bila output berbeda. Yang dilihat: panjang data `/depth_frame` harus 43200 (180×240), hz sekitar 30, dan jumlah level nilai unik. Bila level unik < 200 atau satu nilai > 15%, depth terkuantisasi: cek mode jarak dan filter driver, lalu catat di `sessions.csv`.

## Alur penggunaan

**1. Uji teknis (sebelum sesi sungguhan)**
```bash
./rec_clip.sh TEST_1 3
./validate_clip.sh TEST_1 3
```
Ulangi 1-2x dengan driver asli. Yang harus terlihat: "Recorder siap (x dtk setelah start)", lalu GO, lalu `validate_clip.sh` dengan durasi ≈ PRE+aksi+POST (= 13 dtk untuk aksi 3) dan "MCAP ... tertutup -> OK". Hapus `~/tof_data/bags/TEST_*` setelahnya.

**2. Klip REF (tanpa orang, per sesi)**
```bash
./rec_clip.sh P1S1_REF 0      # PRE 5 + POST 5 = 10 dtk tanpa orang; merekam cloud juga (REC_CLOUD_REF=1)
```
Klip REF dipakai `qc_clip.py` sebagai latar untuk semua klip berikutnya, jadi rekam REF **sebelum** klip partisipan.

**3. Rekam per rep**
```bash
./run_rep.sh P1 1     # P1 rep 1: N1 -> N8b
./run_rep.sh P1 2     # P1 rep 2 (tambahkan `rev` untuk N8b -> N1)
```
Urutan lain diatur operator: tekan `s` untuk melewati klip, atau rekam klip tertentu langsung dengan `./rec_clip.sh <nama> <detik_aksi>`. Durasi aksi: N1 5, N2 5, N3 3, N4 1, N5 3, N6 1, N7 3, N8a 1, N8b 3.
Per klip: partisipan **sudah diam di posisi** sebelum Enter ditekan. Enter = mulai, `s` = lewati, `q` = keluar. Partisipan tetap diam sampai `>>> GO <<<`, lalu beraksi, lalu **tahan posisi akhir** sampai `SELESAI`. Setelah itu skrip menjalankan validasi dan QC otomatis, lalu menanyakan "valid [y/n]". Perhatikan baris `SARAN` dari QC: misalnya "CEK -> kecepatan" berarti jatuh pelan terlalu cepat. Jawaban `n` mengganti nama bag jadi `_x1`, `_x2`, ... dan mengulang slot yang sama. Jangan mengganti nama manual dengan akhiran lain (mis. `_RETRY1`).

Hasil di `~/tof_data/`: `bags/` (1 folder per klip), `cue_log.csv` (header `clip_id,go_epoch,ready_epoch,launch_epoch,act_s`, jam sistem Pi; `t_cue_s` = `go_epoch` − awal bag), `clip_log.csv` (keputusan valid/tidak), `ref_cache/` (latar REF untuk QC), `last_rec.log` (output `ros2 bag record` terakhir, untuk debug).

**4. Akhir sesi: backup**
```bash
rsync -av ~/tof_data/ <user>@<ip_pc>:/path/backup_tof/
```

**5. Di PC: anotasi dan ekstraksi**
```bash
pip install mcap mcap-ros2-support numpy
python3 extract_clips.py --bags ~/backup_tof/bags --out ~/dataset_tof_fall --depth-topic /depth_frame
```
Depth `Float32MultiArray` (meter) diubah ke uint16 mm; bentuk frame diatur `--shape 180 240`. Cloud driver Arducam tidak terorganisir, jadi opsi `--cloud-first` dilewati dengan pesan INFO: koordinat 3D dihitung dari depth + intrinsik di `meta.json`. Klip `_xN` otomatis dilewati, dan skrip memberi peringatan bila satu slot punya lebih dari satu bag (mis. `N7` dan `N7_RETRY1`). Salin `templates/*.csv` ke folder dataset, isi `t_onset_s` dan `t_end_s` dari Foxglove, lalu lengkapi `n_frames`/`fps_est` dari `clips_index.csv`. Langkah rinci mengisi `clips.csv`: Skenario, Bagian 5.

## Hal yang perlu lo ketahui

- **Ambang `validate_clip.sh`** (durasi ±1,5 dtk, pesan ≥ 90% × `FPS_NOMINAL` × durasi) dan **ambang `qc_clip.py`** (diam ≥ 3 dtk, reaksi 0–3 dtk, cepat ≤ 1 dtk, pelan 1,5–3,5 dtk, edge touch < 0,15) adalah usulan. QC hanya saran; keputusan valid tetap dari operator.
- **Format output `ros2 bag info`** di Jazzy sudah dicek ("Duration: 5.13s", "Topic: ... Count: N").
- **Menghentikan recorder:** proses background di skrip non-interaktif mengabaikan SIGINT, jadi `rec_clip.sh` membungkus recorder dengan `timeout`, yang meneruskan SIGINT. Sudah diuji: bag tertutup bersih dan `metadata.yaml` terbentuk.
- **`set -u` dan ROS:** `source /opt/ros/jazzy/setup.bash` gagal di bawah `set -u` sehingga skrip lama keluar diam-diam dengan kode 1. Sekarang di-source dengan `set +u`.
- **Amplitude dan `camera_info` tidak tersedia**, jadi `Q(x)` dihitung tanpa amplitude (rasio piksel valid, edge touch, kontinuitas). Intrinsik diambil dari fit depth↔cloud (lihat `config.sh`).
- **Klip bernama `*REF*`** otomatis menghasilkan `ref/<nama>_floor_ref.npy` (median per-piksel, 0 = tidak valid).
- **Arah jatuh** di `clips_template.csv` (menjauhi kamera / menyamping) adalah usulan; ubah bila lo putuskan lain.
