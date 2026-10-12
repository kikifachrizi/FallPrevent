# Skenario Uji : Pengambilan Data Baseline ToF (36 Klip)

**Status:** 
Draft uji baseline data , belum dataset fix. Sesi pilot P1_R1 (9 Okt 2026) sudah direkam dan dianalisis; temuannya diringkas di **Bagian 9** dan sudah dimasukkan ke bagian terkait.

**Cakupan set ini:** 
- 9 aktivitas baseline (N1–N8b) × 2 partisipan × 2 repetisi = **36 klip** (24 jatuh, 12 non-jatuh).

**Yang bisa dibuktikan set ini:** 
- pipeline **akuisisi → rekam → ekstraksi berjalan**
- base classifier masuk akal pada data bersih
- kualitas observasi `Q(x)` tinggi pada kondisi baseline.

**Yang TIDAK bisa dibuktikan:** 
- Hard Negative (HN) dan Observation Limits (OL) , untuk membuktikan dapat membedakan jatuh dan jongkok/duduk dan menunda pendeteksian ketika gambar terpotong.

---
## 1. Setup

### 1.1 Hardware

| Item           | Spesifikasi / catatan                                                                                                                                                                                 |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sensor         | Arducam ToF (240×180, FOV 70° diagonal, mode 2 m / 4 m). **Default mode 4 m**                                                                                                                         |
| Komputer       | Raspberry Pi 5 4 GB, Ubuntu 24.04, ROS 2 Jazzy                                                                                                                                                        |
| Tinggi / sudut | - Tinggi ±2,5 m (tinggi plafon kamar mandi representatif perlu diukur). <br>- Pitch awal 60° dari horizontal (= 30° dari vertikal)<br>- Square Floor (2x2m) : **belum di test grid untuk yg rebahan**<br>- Pilot P1_R1: fit bidang lantai memberi **2,84 m / pitch ±76°**, beda dari rencana. Ukur ulang dengan meteran dan catat di `sessions.csv` |
| Alat ukur      | meteran dan penggaris sudut                                                                                                                                                                           |
| Properti       | Matras (area jatuh), kursi (N3), penanda posisi mulai partisipan (lakban)                                                                                                                             |

### 1.2 ROS (di Pi)

| Item              | Detail                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Driver            | Package bawaan Arducam: `arducam_rclpy_tof_pointcloud` (node `tof_pointcloud`), dibuild dari `Arducam_tof_camera/ros2_publisher` dengan `colcon build --merge-install` (sesuai wiki resmi Arducam). Tidak ada package akuisisi baru                                                                                                                                                                                                                                                                |
| Topik direkam     | **Dikonfirmasi pilot P1_R1:** `/depth_frame` = `std_msgs/Float32MultiArray` (43200 nilai = 180×240, meter, 0 = invalid, 30 Hz) dan `/point_cloud` = PointCloud2 tidak terorganisir. Amplitude dan `camera_info` tidak ada. Cloud ternyata **reproyeksi depth yang sama persis** (galat 0 mm) dengan intrinsik fx 190,92 · fy 191,25 · cx 120 · cy 90, jadi koordinat 3D cukup dihitung dari depth: **`REC_CLOUD=0`**, cloud hanya direkam di klip REF (`REC_CLOUD_REF=1`). Nama topik dan intrinsik ada di `tof_tools/config.sh` |
| Format bag        | MCAP (`-s mcap`), **1 bag per klip**                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| QoS               | Cek QoS publisher; bila best-effort/sensor_data, pastikan `ros2 bag record` menerima (override QoS bila perlu) *(belum diuji)*                                                                                                                                                                                                                                                                                                                                                                     |
| Prosedur<br>Rekam | Saat merekam: **hanya driver + `ros2 bag record`**. monitoring dilakukan melalu device ROS lain dengan **ROS_DOMAIN_ID=7**                                                                                                                                                                                                                                                                                                                                                                         |
| Jam               | `rec_clip.sh` dijalankan **di Pi yang sama** dengan rekaman, sehingga `t_cue` dan timestamp bag memakai jam yang sama                                                                                                                                                                                                                                                                                                                                                                              |
| Parameter driver  | Mode jarak, filter, dan confidence **dicatat di `sessions.csv` (`driver_params`)** dan tidak diubah antar sesi. Pilot menunjukkan depth terkuantisasi kuat (20–25% piksel tepat 3,000 m, noise lantai ±12 cm): cek parameter ini sebelum sesi berikutnya. `check_topics.sh` menampilkan jumlah level nilai unik |

Skrip rekam dan urutan perintah lengkap: lihat **Bagian 8**.

### 1.3 Host PC

| Item | Detail |
|---|---|
| OS / tool | Ubuntu + ROS 2 Jazzy (atau Python `rosbags`) untuk ekstraksi; Foxglove untuk melihat klip |
| Koneksi | PC dan Pi di jaringan yang sama (SSH untuk menjalankan skrip; `foxglove_bridge` hanya untuk preview *sebelum* loop rekaman) |
| Fungsi | Preview posisi partisipan, cek bag setelah rekam, ekstraksi mcap → npy |
| Backup | Salin `bags/` ke PC/drive kedua **setelah setiap sesi**, bukan di akhir semua sesi |

### 1.4 Lingkungan (dikunci)

- Ruang, posisi tripod, posisi matras, penanda lantai: tidak berubah antar sesi, atau perubahan dicatat di `sessions.csv`.
- Cahaya sekitar: ToF memakai IR 940 nm, jadi sinar matahari langsung berpotensi mengganggu *(hipotesis, belum diuji)*. Tutup jendela / rekam pada jam serupa, catat kondisi.
- Hanya partisipan di dalam frame. Operator/spotter di luar bidang pandang.
- illustrasi pemasangan kamera :
<table>
  <tr>
    <td><img src="images/Picture1.png" width="142" alt="Pemasangan kamera 1"></td>
    <td><img src="images/Picture2.png" width="142" alt="Pemasangan kamera 2"></td>
    <td><img src="images/Picture3.png" width="142" alt="Pemasangan kamera 3"></td>
    <td><img src="images/Picture4.png" width="142" alt="Pemasangan kamera 4"></td>
  </tr>
</table>

---

## 2. Cara Pengambilan Data

### 2.1 Partisipan

| Aspek                | Ketentuan                                                                                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Jumlah               | 2 orang (keterbatasan, lihat Bagian 7)                                                                                                                           |
| Catat per partisipan | - Tinggi badan<br>- pakaian (warna/bahan). Pakaian gelap menyerap IR dan dapat memengaruhi amplitudo *(hipotesis)*, jadi pakaian dijaga sama dalam satu sesi. Pilot: 20–50% piksel tubuh tanpa depth, kemungkinan rambut/pakaian gelap. Bandingkan dengan pakaian terang     |
| Keselamatan          | Matras tebal dan menutup area mendarat, area bebas benda keras, pemanasan, spotter, boleh berhenti kapan saja. Jeda istirahat ≥ 30–60 dtk antar jatuh *(usulan)* |
| Peran minimum        | 1 partisipan + 1 operator/spotter (ideal 3 orang)                                                                                                                |

### 2.2 Daftar klip (slot)

| Kode | Aksi | Arg durasi aksi (dtk) | Durasi bag (5+aksi+5) |
|---|---|---|---|
| N1 | Berdiri diam | 5 | 15 dtk |
| N2 | Jalan silang frame | 5 | 15 dtk |
| N3 | Duduk normal (tahan) | 3 | 13 dtk |
| N4 | Jatuh depan, cepat | 1 | 11 dtk |
| N5 | Jatuh depan, pelan | 3 | 13 dtk |
| N6 | Jatuh belakang, cepat | 1 | 11 dtk |
| N7 | Jatuh belakang, pelan | 3 | 13 dtk |
| N8a | Jatuh samping, cepat | 1 | 11 dtk |
| N8b | Jatuh samping, pelan | 3 | 13 dtk |

`rec_clip.sh` versi baru menunggu sampai recorder benar-benar merekam (biasanya < 1 dtk, maks `INIT_MAX`), baru menghitung PRE 5 dtk. Waktu tunggu itu tidak masuk bag, jadi GO selalu sekitar detik ke-5 dari awal bag.

Definisi cepat/pelan : 
- cepat = awal jatuh sampai menyentuh matras ≤ 1 dtk
- pelan = 1,5–3,5 dtk (simulasi lemas/pingsan).
- Durasi diukur dari 10% sampai 90% penurunan tinggi kepala/bahu, dan dicek otomatis oleh `qc_clip.py` setelah tiap klip.
- Pilot: N4 dan N6 sudah cepat (0,7–0,8 dtk), tetapi tidak ada klip pelan yang masuk rentang (N5 1,3 · N8b 1,2 · N7 0,7 dtk). Latih gerakan pelan sebelum merekam.

**Arah jatuh** : selalu menjauhi atau menyamping dari kamera agar mendarat di lantai yang tercakup.
- Depan: partisipan membelakangi kamera, jatuh ke depan.
- Belakang: partisipan menghadap kamera, jatuh ke belakang.
- Samping: membelakangi kamera, jatuh ke kanan / kiri.

Posisi awal partisipan: titik yang sudah dicek kepala dan kaki terlihat (Bagian 2.5).

### 2.3 Urutan sesi

1. **Persiapan ruang (sekali, sebelum sesi pertama):** ukur kamar mandi representatif dan tentukan titik pasang serta orientasi kamera (Bagian 2.5).
2. **Setup (tiap sesi):** pasang tripod, ukur tinggi lensa→lantai, nyalakan driver, cek `ros2 topic hz`, resolusi (harus 180×240), encoding depth.
3. **Tes grid** (Bagian 2.5): sekali per konfigurasi kamera; ulangi bila tinggi, pitch, orientasi, atau titik pasang berubah.
4. **Klip `REF`:** tanpa orang, matras dan properti di posisi final, ±10 dtk. Dipakai untuk peta lantai per-pixel dan fit bidang lantai (tinggi + pitch terukur).
5. **Latihan:** partisipan mencoba tiap gerakan 1–2× tanpa rekaman (atau rekam sebagai `_warmup`, tidak dihitung). Untuk N5/N7/N8b, rekam `_warmup` dan ulangi sampai `qc_clip.py` menunjukkan durasi turun 1,5–3,5 dtk.
6. **Rep 1:** N1 → N8b (dari ringan ke berat).
7. Istirahat.
8. **Rep 2:** N1 → N8b lagi (`./run_rep.sh P1 2`). Urutan diatur operator; urutan klip tidak diseimbangkan, sebutkan di keterbatasan. Bila ingin dibalik: `./run_rep.sh P1 2 rev`.
9. Backup bag + isi log sesi.

Perkiraan waktu: ±1 menit per klip termasuk reset, jadi ±40–60 menit per partisipan ditambah setup, REF, dan istirahat *(kasar)*.

### 2.4 Prosedur per klip

1. Partisipan **sudah di posisi awal dan diam sebelum** operator menekan Enter. Di pilot, partisipan baru berjalan ke posisi saat pre-buffer, sehingga hanya 2 dari 10 klip yang diam ≥ 3 dtk sebelum GO.
2. Operator: `./rec_clip.sh P1_R1_N4 1` (atau lewat `run_rep.sh`)
3. Partisipan tetap **diam selama pre-buffer** (±5 dtk), mulai aksi hanya setelah aba-aba "GO".
4. Selesai aksi, **tahan posisi akhir** sampai skrip menutup bag (±5 dtk).
5. Operator langsung: `./validate_clip.sh <nama> <detik_aksi>` (otomatis di `run_rep.sh`). Skrip ini mengecek durasi, jumlah pesan, dan file MCAP tertutup, lalu menjalankan `qc_clip.py`: diam sebelum GO, waktu reaksi, kecepatan jatuh, tubuh menyentuh tepi, dan piksel tubuh invalid. Hasil QC hanya saran.
6. Valid → lanjut. Tidak valid → beri suffix `_xN` (N = percobaan ke-), catat alasan, ulangi slot yang sama (maks 3 percobaan per slot; bila gagal terus, hentikan dan cari sebabnya). **Jangan pakai nama lain seperti `_RETRY1`**: `extract_clips.py` hanya melewati `_xN`, sehingga bag gagal yang tidak diganti nama ikut terekstraksi.
### 2.5 Area uji dan tes grid 
#### dilakukan sebelum pengujian untuk memastikan validitas data

**Prinsip:** area uji = lantai bebas di kamar mandi representatif ∩ jangkauan kamera. Ukuran persegi 2x2m sebagai acuan standar kamar mandi (belum diuji di lingkungan kamar mandi sesungguhnya).

**Langkah**
1. Ukur ruang: panjang × lebar, tinggi plafon, posisi kloset/shower/pintu.
2. Pilih titik pasang dan orientasi box (landscape/portrait). Pojok atau sisi pintu bisa memberi jarak lebih jauh ke area uji *(hipotesis)*.
3. Lakban grid dengan titik tiap 0,5 m: kolom A, B, C... dari kiri ke kanan; baris 1, 2, 3... dari dekat ke jauh. Baris 1 = 0,5 m di depan dasar kamera, garis tengah segaris dengan dasar kamera. Batasi pada lantai bebas dan jangkauan kamera. Hitungan teoretis pada 60° / 2,5 m: maju sampai ±2,5 m, lebar ±1,3 m (dekat) sampai ±1,9 m (di 2,5 m); mengasumsikan batas 4 m = jarak miring, **belum diverifikasi**.
4. Partisipan (tinggi badan dicatat) berdiri menghadap kamera di tiap titik ±5 dtk, sementara lo melihat live di RViz/Foxglove. Catat per titik: kepala terlihat? kaki terlihat?
5. Kelas per titik: **UTUH** (kepala dan kaki terlihat), **BAWAH** (kaki/pinggul saja), **KELUAR** (tidak atau hampir tidak terlihat).

**Dipakai untuk:**
- Klip N (berdiri dan awal jatuh) hanya mulai dari titik UTUH.
- Jatuh mendarat di titik yang masih terlihat (tubuh rebah boleh di titik BAWAH).
- OL1 (tubuh terpotong) sengaja memakai titik BAWAH atau tepi.
- Setiap klip mencatat `start_node` dan `end_node`.

---

## 3. Kriteria Data Valid (Done) dan Tidak Valid

### 3.1 Set 36 klip dinyatakan DONE bila

- [ ] Seluruh grid 9 × 2 × 2 terisi klip valid (36/36).
- [ ] Setiap sesi memiliki `REF`, tinggi, pitch terukur, dan parameter driver tercatat.
- [ ] `clips.csv` kolom `valid` terisi untuk 36 klip.
- [ ] `cue_log.csv` punya entri untuk setiap klip (waktu GO), dan `sessions.csv` terisi (tinggi, pitch, pakaian, `driver_params`).
- [ ] Backup kedua ada dan terverifikasi (checksum atau ukuran cocok).

Selain itu → **belum done**.

---

## 4. Skema Dataset

### 4.1 Struktur folder

```
dataset_tof_fall/
├── raw/                    # mcap mentah, TIDAK diubah
│   ├── S1_REF/
│   └── P1_R1_N4/ ...
├── clips/                  # hasil ekstraksi; 1 folder = 1 klip
│   └── P1_R1_N4/
│       ├── depth.npy       # (T,180,240) uint16, mm, 0 = invalid
│       ├── meta.json       # n_frames, fps_est, encoding
│       ├── cloud_xyz_firstN.npy  # opsional, N frame cloud pertama (klip REF)
│       └── t.npy           # (T,) int64, ns (log time bag)
├── ref/
│   └── S1_floor_ref.npy    # (180,240) median depth lantai dari klip REF
├── sessions.csv
├── clips.csv
├── frames.csv              # turunan
└── splits.csv
```

`raw/` adalah sumber kebenaran; `clips/` dapat dibuat ulang dari `raw/`.

### 4.2 Format array

`uint16` dalam mm (bukan float32): float tidak menambah informasi dan menggandakan ukuran. Driver Arducam mengirim `Float32MultiArray` dalam meter, dan `extract_clips.py` mengubahnya ke mm (pembulatan, galat 0 mm terhadap data asli). Resolusi efektif sensor ternyata lebih kasar dari spek ±2 cm: noise lantai ±12 cm karena kuantisasi (lihat Bagian 9). `meta.json` menyimpan intrinsik dan `valid_ratio`.

### 4.3 Tabel metadata

**sessions.csv** — 1 baris per sesi
`session_id, date, participant, participant_height_cm, clothing, bathroom_L_m, bathroom_W_m, ceiling_m, camera_position, camera_orientation, camera_height_m, pitch_deg, pitch_method, mat_layout, ambient_light, driver_params, grid_test_ref, ref_clip_id, notes`

**clips.csv** — 1 baris per klip
`clip_id, session_id, participant, rep, code, group, label, fall_type, speed, direction, start_node, end_node, t_cue_s, t_onset_s, t_end_s, n_frames, fps_est, valid, invalid_reason, notes`

- `group` = N / HN / OL; `label` = fall / no_fall.
- `pitch_deg` = sudut sumbu optik di bawah garis horizontal (0° = menghadap lurus ke depan, 90° = menghadap lurus ke bawah).
- `t_onset_s` kosong untuk non-jatuh.

**frames.csv** — turunan, 1 baris per frame
`clip_id, frame_idx, t_s, phase, valid_ratio, edge_touch, continuity, Q, P_fall`
`phase` = pre / action / post, dihitung dari `t_onset_s` dan `t_end_s`.

**splits.csv**
`clip_id, split_group, split, fold` — `split_group` = partisipan. Aturan split (opsi A/B/C untuk 2 partisipan) belum diputuskan; skema ini tidak mengunci itu.

### 4.4 Alur data

`raw/*.mcap` → ekstraksi → `clips/` → hitung `Q` dan `P(fall|x)` → `frames.csv` → evaluasi Sistem A/B/C.

Bedanya dengan dataset Elna (folder gambar per kelas, tanpa info klip/partisipan): setiap frame di sini terlacak ke klip dan partisipan, sehingga frame bertetangga dari klip yang sama tidak bisa tersebar ke train dan test sekaligus.

---
## 5. Hasil yang Diharapkan dari Set Ini

- Pipeline terbukti: rekam → validasi → ekstraksi.
- Estimasi fps efektif dan ukuran data riil di Pi 5.
- Distribusi `Q(x)` pada kondisi bersih (batas bawah untuk menentukan `tau_q` nanti).
- Gambaran awal base classifier pada 24 klip jatuh vs 12 non-jatuh. Dengan n sekecil ini hasilnya **bersifat kelayakan, bukan klaim performa** (interval kepercayaan lebar).

---

## 6. Next Action (berurutan)

| #   | Aksi                                                                                                                                                                          | Output                                                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 1   | ✅ Topik dan format dikonfirmasi dari pilot (Float32MultiArray, 30 Hz, intrinsik). Jalankan `check_topics.sh` lagi di Pi untuk cek kuantisasi                                  | `config.sh` terisi (sudah)                              |
| 2   | ✅ Uji `rec_clip.sh` dengan publisher dummy (12 Okt): bag tertutup bersih, GO tepat PRE setelah recorder siap. **Ulangi 1× di Pi dengan driver asli**                          | Skrip final (sudah) + cek di Pi                         |
| 2b  | Cek parameter driver (mode jarak, filter) dan pakaian terang vs gelap: jumlah level depth dan piksel tubuh invalid                                                              | `driver_params` di `sessions.csv`                       |
| 3   | Ukur kamar mandi representatif, tentukan titik pasang dan orientasi kamera                                                                                                    | Dimensi ruang + posisi kamera                           |
| 4   | **Tes grid** (Bagian 2.5) + ukur tinggi, fit pitch dari `REF`                                                                                                                 | Peta UTUH/BAWAH/KELUAR + `camera_height_m`, `pitch_deg` |
| 5   | Kunci arah jatuh, definisi cepat/pelan                                                                                                                                        | Dokumen protokol final                                  |
| 6   | Siapkan consent partisipan dan cek kebutuhan etik kampus                                                                                                                      | Consent tertandatangani                                 |
| 7   | **Ambil 36 klip** sesuai Bagian 2, validasi tiap klip (Bagian 3)                                                                                                              | Grid 36/36                                              |
| 8   | Ekstraksi dengan `extract_clips.py` (sudah ada, diuji dengan bag sintetis; jalankan pada data asli)                                                                           | `clips/` terisi                                         |
| 9   | Hitung `Q(x)` (dengan peta lantai per-pixel dari `REF`) pada klip baseline; periksa distribusi                                                                                | Ringkasan `Q` baseline                                  |
| 10  | Rancang set kedua: HN1–HN5 dan OL1–OL4 (set yang menguji klaim inti)                                                                                                          | Draf protokol set 2                                     |

**Catatan implementasi `Q(x)`:** `floor_depth_ref` harus berupa **peta per-pixel** (bukan skalar, karena kamera miring). Margin segmentasi awalnya direncanakan ±5–8 cm, tapi noise riil pilot ±12 cm, jadi kalibrasi margin dari std per-piksel klip REF. Piksel yang valid di REF tetapi invalid saat ada orang dihitung sebagai bagian tubuh, dan rasionya menjadi komponen utama `valid_ratio`. `edge_touch` diukur terhadap batas elips area valid (±37% frame), bukan tepi gambar.

---

## 7. Keputusan Terbuka dan Keterbatasan

| Item                                                                                             | Status                                   |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| Ambang valid (Bagian 3)                                                                          | Usulan, dikalibrasi di uji teknis        |
| Arsitektur base classifier                                                                       | Belum dikunci                            |
| tes grid untuk posisi kamera (60deg , LxWxH : 2.5x2x2)                                           | tes tidur terpotong atau tidak di kamera |
| Geometri kamera (pilot terukur 2,84 m / ±76°)                                                    | Ukur ulang dengan meteran, putuskan pitch final |
| Kuantisasi depth dan piksel tubuh invalid                                                        | Cek driver dan pakaian (Next Action 2b) |

---

## 8. Urutan Perintah dan File Pendukung — *diuji dengan publisher dummy di PC (12 Okt 2026), belum dengan driver asli di Pi*

Semua file ada di folder **`tof_tools/`** (lihat `tof_tools/README_PENGGUNAAN.md` untuk penjelasan tiap file). **Tidak ada package ROS baru**: akuisisi memakai driver Arducam (`arducam_rclpy_tof_pointcloud`), rekam memakai `ros2 bag`, dan sisanya skrip bash. Instalasi tambahan hanya bila perlu: plugin MCAP (`ros-jazzy-rosbag2-storage-mcap`) dan `pip install mcap mcap-ros2-support numpy` untuk ekstraksi.

| File               | Fungsi                                                            |
| ------------------ | ----------------------------------------------------------------- |
| `config.sh`        | Topik, FPS, buffer, folder data (edit sekali)                     |
| `check_topics.sh`  | Cek topik, QoS, encoding, hz, bw                                  |
| `rec_clip.sh`      | Rekam 1 klip dengan aba-aba GO dan `cue_log.csv`                  |
| `validate_clip.sh` | Cek otomatis durasi, jumlah pesan, MCAP tertutup, lalu `qc_clip.py` |
| `qc_clip.py`       | QC isi klip: diam sebelum GO, reaksi, kecepatan jatuh, tepi, piksel invalid (butuh `python3-scipy`) |
| `run_rep.sh`       | Loop 9 klip N1..N8b per partisipan per rep, dengan ulang otomatis |
| `extract_clips.py` | Bag MCAP → `depth.npy`, `t.npy`, `meta.json`, peta lantai REF     |
| `templates/*.csv`  | `clips.csv` (36 baris terisi sebagian) dan `sessions.csv`         |

**Urutan perintah (di Pi, kecuali dinyatakan lain)**
```bash
# 0. Salin paket ke Pi (dari PC), lalu:
cd ~/tof_tools && chmod +x *.sh

# 1. Terminal 1: driver (biarkan hidup)
source /opt/ros/jazzy/setup.bash
source ~/Arducam_tof_camera/ros2_publisher/install/setup.bash
ros2 run arducam_rclpy_tof_pointcloud tof_pointcloud

# 2. Terminal 2: cek topik (config.sh sudah terisi dari pilot; ubah hanya bila hasilnya beda)
export ROS_DOMAIN_ID=7
./check_topics.sh

# 3. Uji teknis (1-2x dengan driver asli), hapus bags/TEST_* sesudahnya
./rec_clip.sh TEST_1 3
./validate_clip.sh TEST_1 3

# 3b. Sebelum rekam sungguhan: ukur ruangan + tes grid (Bagian 2.5), tanpa skrip

# 4. Per sesi: klip REF (tanpa orang)
./rec_clip.sh P1S1_REF 0

# 5. Per rep: 9 klip (N1 -> N8b); tambahkan `rev` untuk urutan terbalik
./run_rep.sh P1 1
./run_rep.sh P1 2

# 6. Akhir sesi: backup ke PC
rsync -av ~/tof_data/ <user>@<ip_pc>:/path/backup_tof/

# 7. Di PC: ekstraksi
python3 extract_clips.py --bags <backup>/bags --out <dataset> \
    --depth-topic /depth_frame
```

**Status verifikasi (12 Okt 2026):**
- `extract_clips.py` membaca bag pilot P1_R1 asli (Float32MultiArray), dengan galat 0 mm terhadap data mentah.
- `rec_clip.sh`, `validate_clip.sh`, `check_topics.sh`, dan `run_rep.sh` diuji di PC (ROS 2 Jazzy) dengan publisher dummy `/depth_frame` 30 Hz.
- `qc_clip.py` diuji pada bag pilot dan memakai ±220 MB RAM.
- Dua bug lama ditemukan dan diperbaiki: skrip keluar diam-diam saat `source setup.bash` di bawah `set -u`, dan recorder background tidak bisa dihentikan dengan SIGINT langsung (sekarang lewat `timeout`).
- Yang belum: satu kali uji di Pi dengan driver asli.

---

## 9. Temuan Pilot P1_R1 (9 Okt 2026, dianalisis 12 Okt 2026)

10 klip (N1–N8b, termasuk N7_RETRY1; N2_x1, N4_x1, N6_RETRY1 sudah dihapus) dianalisis dengan latar dari frame kosong, fit bidang lantai, dan intrinsik di atas. Diagram dan rincian per klip ada di catatan vault `Data/P1_R1 Analisis.md` dan `Data/peta_jalan_fallprevent.html`.

| Temuan | Dampak ke protokol |
|---|---|
| Recorder terlambat mulai 0,6–4,7 dtk; skrip lama menghitung GO sejak peluncuran | Diperbaiki di `rec_clip.sh` (GO dihitung setelah recorder siap) |
| Hanya N1 dan N6 yang diam ≥ 3 dtk sebelum GO | Bagian 2.4 langkah 1: partisipan siap sebelum rekam dimulai |
| Klip pelan terlalu cepat (0,5–1,3 dtk) | Bagian 2.2 dan 2.3: latihan + cek `qc_clip.py` |
| Geometri terukur 2,84 m / ±76° (rencana 2,5 m / 60°) | Ukur ulang, catat di `sessions.csv` |
| Depth terkuantisasi, noise lantai ±12 cm | Cek parameter driver (Next Action 2b), margin segmentasi dikalibrasi |
| 20–50% piksel tubuh tanpa depth | Catat pakaian; komponen utama `Q(x)` |
| Cloud = reproyeksi depth | `REC_CLOUD=0`, data ±50% lebih kecil |
| Belum ada REF, `cue_log.csv`, `sessions.csv` | Wajib di sesi berikutnya (Bagian 3.1) |

Kesimpulan: P1_R1 dipakai sebagai **sesi pilot/uji teknis**, belum sebagai dataset. Rekam ulang P1 Rep 1 setelah perbaikan di atas.

