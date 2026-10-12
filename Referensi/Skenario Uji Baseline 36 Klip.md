# Skenario Uji — Pengambilan Data Baseline ToF (36 Klip)

**Status:** draf kerja. Angka bertanda *(usulan)* adalah tebakan awal yang harus dikunci/diubah setelah uji teknis (Bagian 7, langkah 1–3). Bagian bertanda *(belum diuji)* belum pernah dijalankan.

**Cakupan set ini:** 9 aktivitas baseline (N1–N8b) × 2 partisipan × 2 repetisi = **36 klip** (24 jatuh, 12 non-jatuh).

**Yang bisa dibuktikan set ini:** pipeline akuisisi → anotasi → ekstraksi berjalan; base classifier masuk akal pada data bersih; kualitas observasi `Q(x)` tinggi pada kondisi baseline.

**Yang TIDAK bisa dibuktikan:** klaim inti (Sistem C vs B pada kondisi observation-limited) dan false alarm pada hard-negative. Itu butuh set kedua (HN1–HN5, OL1–OL4).

---

## 1. Setup

### 1.1 Hardware

| Item | Spesifikasi / catatan |
|---|---|
| Sensor | Arducam ToF (240×180, FOV 70° diagonal, mode 2 m / 4 m). **Pakai mode 4 m** — jarak miring ke lantai jauh dari ketinggian 2,5 m melewati 2 m |
| Komputer sensor | Raspberry Pi 5 4 GB, Ubuntu 24.04, ROS 2 Jazzy |
| Catu daya | Sesuai spek Arducam dan Pi 5. Cek throttling/undervoltage sebelum sesi (mis. `vcgencmd get_throttled` bila tersedia) — hipotesis: power kurang → frame drop |
| Penyimpanan | SSD/SD dengan ruang kosong ≥ 20 GB *(usulan; estimasi kasar; ukuran riil diukur di uji teknis dan sangat bergantung pada rekam cloud atau tidak)* |
| Mounting | Tripod; kamera + raspi dalam 1 box. Titik acuan tinggi = **pusat lensa** |
| Tinggi / sudut | Tinggi ±2,5 m (tinggi plafon kamar mandi representatif perlu diukur). Pitch awal 60° dari horizontal (= 30° dari vertikal) **sementara**: keputusan akhir pitch, orientasi box (landscape/portrait), dan titik pasang menunggu hasil tes grid (Bagian 2.6). **Angka pasti diukur tiap sesi** |
| Alat ukur | Meteran/laser meter, lakban penanda lantai, (opsional) inclinometer / app level |
| Properti | Matras (area jatuh), kursi (N3), penanda posisi mulai partisipan |
| Opsional | Rekaman video HP sebagai pembantu menentukan `t_onset` *(hanya dengan persetujuan partisipan; simpan terpisah dari dataset)* |

### 1.2 ROS (di Pi)

| Item | Detail |
|---|---|
| Driver | Package bawaan Arducam: `arducam_rclpy_tof_pointcloud` (node `tof_pointcloud`), dibuild dari `Arducam_tof_camera/ros2_publisher` dengan `colcon build --merge-install` (sesuai wiki resmi Arducam). Tidak ada package akuisisi baru |
| Topik direkam | **Tersedia (dikonfirmasi): PointCloud2 dan depth Image.** Amplitude tidak tersedia; `camera_info` belum dicek. Data utama = depth Image (ringan). PointCloud2 opsional (`REC_CLOUD`), berguna untuk fit bidang lantai dan pitch dari klip REF, tapi lebih berat (ukuran/fps diukur di uji teknis). Nama topik diisi di `tof_tools/config.sh` |
| Format bag | MCAP (`-s mcap`), **1 bag per klip** |
| QoS | Cek QoS publisher; bila best-effort/sensor_data, pastikan `ros2 bag record` menerima (override QoS bila perlu) *(belum diuji)* |
| Parameter driver | Mode jarak, fps, filter (mis. confidence threshold bila ada) **dikunci dan dicatat**; tidak diubah antar sesi |
| Beban Pi | Saat merekam: hanya driver + `ros2 bag record`. Matikan `foxglove_bridge`, RViz, dan proses lain *(usulan; dampaknya diverifikasi di uji teknis)* |
| Jam | `rec_clip.sh` dijalankan **di Pi yang sama** dengan rekaman, sehingga `t_cue` dan timestamp bag memakai jam yang sama |

Skrip rekam dan urutan perintah lengkap: lihat **Bagian 9**.

Catatan: `t_cue` hanya dipakai sebagai jendela pencarian. Sumber kebenaran awal jatuh adalah `t_onset` hasil anotasi.

### 1.3 Host PC

| Item | Detail |
|---|---|
| OS / tool | Ubuntu + ROS 2 Jazzy (atau Python `rosbags`) untuk ekstraksi; Foxglove untuk melihat dan anotasi |
| Koneksi | PC dan Pi di jaringan yang sama (SSH untuk menjalankan skrip; `foxglove_bridge` hanya untuk preview *sebelum* loop rekaman) |
| Fungsi | Preview posisi partisipan, cek bag setelah rekam, anotasi `t_onset`, ekstraksi mcap → npy |
| Backup | Salin `bags/` ke PC/drive kedua **setelah setiap sesi**, bukan di akhir semua sesi |

### 1.4 Lingkungan (dikunci)

- Ruang, posisi tripod, posisi matras, penanda lantai: tidak berubah antar sesi, atau perubahan dicatat di `sessions.csv`.
- Cahaya sekitar: ToF memakai IR 940 nm, jadi sinar matahari langsung berpotensi mengganggu *(hipotesis, belum diuji)*. Tutup jendela / rekam pada jam serupa, catat kondisi.
- Hanya partisipan di dalam frame. Operator/spotter di luar bidang pandang.

---

## 2. Cara Pengambilan Data

### 2.1 Partisipan

| Aspek | Ketentuan |
|---|---|
| Jumlah | 2 orang (keterbatasan, lihat Bagian 8) |
| Kriteria | Dewasa sehat, tanpa cedera/kondisi yang membuat jatuh simulasi berisiko; bersedia dan menyetujui secara tertulis |
| Etik | Persetujuan tertulis (informed consent); cek kebutuhan persetujuan etik di kampus *(belum diverifikasi)*. Data memakai kode P1/P2, tanpa nama di nama file |
| Catat per partisipan | Tinggi badan, pakaian (warna/bahan). Pakaian gelap menyerap IR dan dapat memengaruhi amplitudo *(hipotesis)*, jadi pakaian dijaga sama dalam satu sesi |
| Keselamatan | Matras tebal dan menutup area mendarat, area bebas benda keras, pemanasan, spotter, boleh berhenti kapan saja. Jeda istirahat ≥ 30–60 dtk antar jatuh *(usulan)* |
| Peran minimum | 1 partisipan + 1 operator/spotter (ideal 3 orang) |

### 2.2 Daftar klip (slot)

| Kode | Aksi                  | Arg durasi aksi (dtk) | Total rekam (2+5+aksi+5) |
| ---- | --------------------- | --------------------- | ------------------------ |
| N1   | Berdiri diam          | 5                     | 17 dtk                   |
| N2   | Jalan silang frame    | 5                     | 17 dtk                   |
| N3   | Duduk normal (tahan)  | 3                     | 15 dtk                   |
| N4   | Jatuh depan, cepat    | 1                     | 13 dtk                   |
| N5   | Jatuh depan, pelan    | 3                     | 15 dtk                   |
| N6   | Jatuh belakang, cepat | 1                     | 13 dtk                   |
| N7   | Jatuh belakang, pelan | 3                     | 15 dtk                   |
| N8a  | Jatuh samping, cepat  | 1                     | 13 dtk                   |
| N8b  | Jatuh samping, pelan  | 3                     | 15 dtk                   |

Definisi cepat/pelan *(usulan)*: cepat = awal jatuh sampai menyentuh matras ≤ 1 dtk; pelan = 1,5–3,5 dtk (simulasi lemas/pingsan).

**Arah jatuh** *(usulan; lo yang memutuskan)*: selalu menjauhi atau menyamping dari kamera agar mendarat di lantai yang tercakup.

- Depan: partisipan membelakangi kamera, jatuh ke depan.
- Belakang: partisipan menghadap kamera, jatuh ke belakang.
- Samping: tegak lurus arah kamera.

Posisi awal partisipan: di titik grid berkelas **UTUH** (Bagian 2.6). Setiap klip mencatat `start_node` dan `end_node` (kode titik grid).

### 2.3 Urutan sesi

1. **Persiapan ruang (sekali, sebelum sesi pertama):** ukur kamar mandi representatif dan tentukan titik pasang serta orientasi kamera (Bagian 2.6).
2. **Setup (tiap sesi):** pasang tripod, ukur tinggi lensa→lantai, nyalakan driver, cek `ros2 topic hz`, resolusi (harus 180×240), encoding depth.
3. **Tes grid** (Bagian 2.6): sekali per konfigurasi kamera; ulangi bila tinggi, pitch, orientasi, atau titik pasang berubah.
4. **Klip `REF`:** tanpa orang, matras dan properti di posisi final, ±10 dtk. Dipakai untuk peta lantai per-pixel dan fit bidang lantai (tinggi + pitch terukur).
5. **Latihan:** partisipan mencoba tiap gerakan 1–2× tanpa rekaman (atau rekam sebagai `_warmup`, tidak dihitung).
6. **Rep 1:** N1 → N8b (dari ringan ke berat).
7. Istirahat.
8. **Rep 2:** urutan **dibalik** (N8b → N1), supaya efek urutan/kelelahan tidak menumpuk pada kode yang sama *(usulan)*.
9. Backup bag + isi log sesi.

Perkiraan waktu: ±1 menit per klip termasuk reset, jadi ±40–60 menit per partisipan ditambah setup, REF, dan istirahat *(kasar)*.

### 2.4 Prosedur per klip

1. Partisipan di posisi awal, diam.
2. Operator: `./rec_clip.sh P1_R1_N4 1`
3. Partisipan tetap **diam selama pre-buffer** (±5 dtk), mulai aksi hanya setelah aba-aba "GO".
4. Selesai aksi, **tahan posisi akhir** sampai skrip menutup bag (±5 dtk).
5. Operator langsung: `ros2 bag info bags/<nama>` dan cek ringkas (Bagian 3).
6. Valid → lanjut. Tidak valid → beri suffix `_xN` (N = percobaan ke-), catat alasan, ulangi slot yang sama (maks 3 percobaan per slot; bila gagal terus, hentikan dan cari sebabnya).

### 2.5 Grid pelacakan (centang saat klip VALID)

| Kode | P1-R1 | P1-R2 | P2-R1 | P2-R2 |
|---|---|---|---|---|
| N1 | ☐ | ☐ | ☐ | ☐ |
| N2 | ☐ | ☐ | ☐ | ☐ |
| N3 | ☐ | ☐ | ☐ | ☐ |
| N4 | ☐ | ☐ | ☐ | ☐ |
| N5 | ☐ | ☐ | ☐ | ☐ |
| N6 | ☐ | ☐ | ☐ | ☐ |
| N7 | ☐ | ☐ | ☐ | ☐ |
| N8a | ☐ | ☐ | ☐ | ☐ |
| N8b | ☐ | ☐ | ☐ | ☐ |

### 2.6 Area uji dan tes grid

**Prinsip:** area uji = lantai bebas di kamar mandi representatif ∩ jangkauan kamera. Ukuran persegi **tidak ditetapkan dulu**; ukuran ruang riil yang menentukan. Sebagai konteks: dari pencarian umum, kamar mandi minimal ±1,5 × 1,5 m dan "ideal" ≥ 2 × 2 m. Sumbernya artikel properti dan jurnal, bukan standar yang diverifikasi, jadi 2 × 2 m hanya batas atas yang wajar.

**Langkah**

1. Ukur ruang: panjang × lebar, tinggi plafon, posisi kloset/shower/pintu.
2. Pilih titik pasang dan orientasi box (landscape/portrait). Pojok atau sisi pintu bisa memberi jarak lebih jauh ke area uji *(hipotesis)*.
3. Lakban grid dengan titik tiap 0,5 m: kolom A, B, C... dari kiri ke kanan; baris 1, 2, 3... dari dekat ke jauh. Baris 1 = 0,5 m di depan dasar kamera, garis tengah segaris dengan dasar kamera. Batasi pada lantai bebas dan jangkauan kamera. Hitungan teoretis pada 60° / 2,5 m: maju sampai ±2,5 m, lebar ±1,3 m (dekat) sampai ±1,9 m (di 2,5 m); mengasumsikan batas 4 m = jarak miring, **belum diverifikasi**.
4. Partisipan (tinggi badan dicatat) berdiri menghadap kamera di tiap titik ±5 dtk, sementara lo melihat live di RViz/Foxglove. Catat per titik: kepala terlihat? kaki terlihat?
5. Kelas per titik: **UTUH** (kepala dan kaki terlihat), **BAWAH** (kaki/pinggul saja), **KELUAR** (tidak atau hampir tidak terlihat).

**Lembar catatan (kolom):** `node, maju_m, lateral_m, kepala (y/n), kaki (y/n), kelas, catatan`.

**Prediksi sebagai pembanding** (60°, landscape, orang 1,7 m; hitungan teoretis): UTUH hanya di sekitar 0,3–1,05 m maju dan ±0,4–0,55 m ke samping (±0,7 × 0,9 m). Hasil tes menggantikan prediksi ini.

**Dipakai untuk:**

- Klip N (berdiri dan awal jatuh) hanya mulai dari titik UTUH.
- Jatuh mendarat di titik yang masih terlihat (tubuh rebah boleh di titik BAWAH).
- OL1 (tubuh terpotong) sengaja memakai titik BAWAH atau tepi.
- Setiap klip mencatat `start_node` dan `end_node`.

**Jika zona UTUH terlalu kecil** untuk gerak natural (mis. N2 jalan silang): ubah geometri (pitch 45°, box portrait, atau titik pasang lebih jauh), lalu **ulangi tes grid**. Hitungan kasar: portrait + 45° memberi kedalaman UTUH 0,7–2,85 m dengan lebar ±0,3 m (dekat) sampai ±0,9 m (jauh); belum diuji. Setiap perubahan dicatat di `sessions.csv`.

---

## 3. Kriteria Data Valid (Done) dan Tidak Valid

Semua ambang adalah *(usulan awal)* dan dikalibrasi ulang setelah uji teknis.

### 3.1 Klip VALID bila SEMUA terpenuhi

**File dan akuisisi**

- Bag terbuka normal (`ros2 bag info` sukses), `metadata.yaml` ada, tidak corrupt.
- Topik depth Image (dan PointCloud2 bila `REC_CLOUD=1`) ada.
- Durasi bag = total rekam rencana ±1,5 dtk.
- Jumlah frame ≥ 90% dari (fps terukur sebelum sesi × durasi).
- Tidak ada jeda antar-frame > 3× interval median pada jendela [`t_cue` − 1 dtk, akhir aksi + 3 dtk].

**Prosedur**

- Entri `cue_log.csv` ada untuk klip ini.
- Partisipan diam ≥ 3 dtk sebelum "GO" dan ≥ 3 dtk setelah aksi selesai.
- Aksi dimulai ≤ 3 dtk setelah "GO".

**Kesesuaian aksi** (dicek di Foxglove)

- Aksi sesuai kode: arah jatuh benar, kecepatan dalam rentang cepat/pelan, N2 benar-benar menyeberang.
- Jatuh mendarat di area matras yang tercakup frame.

**Kondisi baseline bersih (kelompok N)**

- Seluruh tubuh (kepala sampai kaki) terlihat selama [`t_cue`, akhir aksi]; **tidak ada bagian tubuh terpotong tepi frame**. Bila terpotong, klip itu sebenarnya observation-limited dan tidak boleh masuk baseline.
- Klip N mulai dari titik berkelas UTUH (`start_node`, Bagian 2.6).
- Tidak ada orang atau objek bergerak lain di frame.
- Matras/properti tidak bergeser dari penanda lantai (±5 cm).

**Metadata**

- Sesi memiliki tinggi dan pitch terukur, serta klip `REF`.
- `clips.csv` terisi lengkap: label, `t_end`, dan `t_onset` untuk klip jatuh.

### 3.2 Klip TIDAK VALID (beri suffix `_xN` (N = percobaan ke-), jangan dihapus)

| Penyebab | Contoh |
|---|---|
| File | Bag terpotong/corrupt; topik hilang; frame drop besar; durasi meleset |
| Prosedur | Partisipan bergerak sebelum "GO"; tidak diam di akhir; cue tidak tercatat |
| Aksi | Arah/kecepatan salah; partisipan berhenti/ragu di tengah; mendarat di luar matras/frame |
| Baseline tidak bersih | Tubuh terpotong tepi frame; orang lain masuk frame; properti bergeser |
| Sesi | Tinggi/pitch tidak tercatat; tidak ada klip `REF`; parameter driver berubah di tengah sesi → seluruh sesi tidak bisa dipakai untuk analisis geometri |
| Anotasi | `t_onset` tidak bisa ditentukan dengan yakin dari data |

**Klip dengan anomali kualitas (bukan otomatis invalid):** rasio piksel invalid (depth = 0) pada seluruh frame rata-rata > 2× median sesi → tandai untuk review manual. **`Q(x)` tidak dipakai sebagai kriteria valid/invalid** karena akan menjadi sirkular (metode yang diuji menentukan data yang dipakai untuk menguji).

### 3.3 Set 36 klip dinyatakan DONE bila

- [ ] Seluruh grid 9 × 2 × 2 terisi klip valid (36/36).
- [ ] Setiap sesi memiliki `REF`, tinggi, pitch terukur, dan parameter driver tercatat.
- [ ] `clips.csv` dan `sessions.csv` lengkap, tanpa sel kosong yang wajib.
- [ ] Ekstraksi ke `clips/` sukses; `shape` array dan jumlah frame konsisten dengan metadata.
- [ ] Backup kedua ada dan terverifikasi (checksum atau ukuran cocok).

Selain itu → **belum done**.

---

## 4. Skema Dataset

### 4.1 Struktur folder

```
dataset_tof_fall/
├── raw/                          # mcap mentah, TIDAK diubah
│   ├── S1_REF/
│   └── P1_R1_N4/ ...
├── clips/                        # hasil ekstraksi; 1 folder = 1 klip
│   └── P1_R1_N4/
│       ├── depth.npy             # (T,180,240) uint16, mm, 0 = invalid
│       ├── meta.json             # n_frames, fps_est, encoding
│       ├── cloud_xyz_firstN.npy  # opsional, N frame cloud pertama (klip REF)
│       └── t.npy                 # (T,) int64, ns (log time bag)
├── ref/
│   └── S1_floor_ref.npy          # (180,240) median depth lantai dari klip REF
├── sessions.csv
├── clips.csv
├── frames.csv                    # turunan
└── splits.csv
```

`raw/` adalah sumber kebenaran; `clips/` dapat dibuat ulang dari `raw/`.

### 4.2 Format array

`uint16` dalam mm (bukan float32): error sensor ±2 cm, float tidak menambah informasi dan menggandakan ukuran. **Cek encoding driver dulu** (32FC1 dalam meter vs 16UC1 dalam mm) sebelum menulis skrip ekstraksi.

### 4.3 Tabel metadata

**sessions.csv** — 1 baris per sesi

`session_id, date, participant, participant_height_cm, clothing, bathroom_L_m, bathroom_W_m, ceiling_m, camera_position, camera_orientation, camera_height_m, pitch_deg, pitch_method, mat_layout, ambient_light, driver_params, grid_test_ref, ref_clip_id, notes`

**clips.csv** — 1 baris per klip (anotasi manual)

`clip_id, session_id, participant, rep, code, group, label, fall_type, speed, direction, start_node, end_node, t_cue_s, t_onset_s, t_end_s, n_frames, fps_est, valid, invalid_reason, notes`

- `group` = N / HN / OL; `label` = fall / no_fall.
- `pitch_deg` = sudut sumbu optik di bawah garis horizontal (0° = menghadap lurus ke depan, 90° = menghadap lurus ke bawah).
- Waktu dalam **detik relatif dari awal bag** (cara menentukannya: Bagian 5, langkah 3).
- `t_onset_s` kosong untuk non-jatuh.

**frames.csv** — turunan, 1 baris per frame

`clip_id, frame_idx, t_s, phase, valid_ratio, edge_touch, continuity, Q, P_fall`

`phase` = pre / action / post, dihitung dari `t_onset_s` dan `t_end_s`.

**splits.csv**

`clip_id, split_group, split, fold` — `split_group` = partisipan. Aturan split (opsi A/B/C untuk 2 partisipan) belum diputuskan; skema ini tidak mengunci itu.

### 4.4 Alur data

`raw/*.mcap` → ekstraksi → `clips/` → anotasi `clips.csv` → hitung `Q` dan `P(fall|x)` → `frames.csv` → evaluasi Sistem A/B/C.

Bedanya dengan dataset Elna (folder gambar per kelas, tanpa info klip/partisipan): setiap frame di sini terlacak ke klip dan partisipan, sehingga frame bertetangga dari klip yang sama tidak bisa tersebar ke train dan test sekaligus.

---

## 5. Anotasi: cara mengisi `clips.csv` dan definisi `t_onset`

**Wajib diisi untuk N1–N8b:** `t_onset_s` (24 klip jatuh saja), `t_end_s` (36 klip), `valid` (36 klip). Kolom lain (`session_id`, `start_node`, `end_node`, `t_cue_s`, `n_frames`, `fps_est`, `notes`) boleh dikosongkan.

**Langkah**

1. Salin `tof_tools/templates/clips_template.csv` ke folder dataset dan ganti nama jadi `clips.csv`. Buka dengan Excel/LibreOffice/Sheets, simpan tetap sebagai CSV (UTF-8, pemisah koma). Jangan ubah nama kolom atau urutan baris.
2. Per klip: Foxglove → Open local file → pilih `.mcap` di `bags/<nama_klip>/`. Tambahkan panel Image untuk topik depth (PointCloud2 di panel 3D bila perlu).
3. Tentukan waktu awal bag (`Start` di `ros2 bag info bags/<nama_klip>`). Semua waktu di CSV adalah **detik dari awal bag**. Foxglove bisa menampilkan waktu absolut; bila begitu, kurangi dengan waktu awal bag *(tampilan waktu Foxglove belum gw verifikasi)*.
4. **`t_onset_s`** (klip jatuh saja): scrub sampai frame pertama saat kepala/bahu mulai turun terus-menerus menuju lantai. Tulis detiknya.
5. **`t_end_s`** (semua klip): frame saat tubuh berhenti bergerak di posisi akhir. Untuk klip non-jatuh (N1, N2, N3): saat aksi selesai (diam berdiri sampai dihentikan, selesai menyeberang, selesai duduk).
6. **`valid`**: `y` bila tubuh utuh dan aksi sesuai kode; bila tidak, `n` + isi `invalid_reason`, lalu rekam ulang slot itu (bag lama diganti nama `_xN`). Jawaban y/n di `clip_log.csv` hanya acuan awal; keputusan akhir dari pemeriksaan di Foxglove.
7. **Cek per baris:** `t_onset_s` < `t_end_s`; `t_onset_s` kira-kira 7–10 dtk (aba-aba GO jatuh sekitar INIT + PRE = 7 dtk dari awal bag); `t_end_s` ≤ durasi bag (13–17 dtk). Angka di luar rentang itu berarti cek ulang.

**Definisi `t_onset`:** awal jatuh = frame pertama setelah titik terakhir tubuh stabil, di mana turunnya titik tertinggi tubuh (kepala/bahu) berlangsung terus-menerus menuju lantai tanpa berhenti. *(usulan; dikunci sebelum menganotasi 24 klip jatuh agar konsisten)*. `t_end` = frame saat tubuh berhenti bergerak di posisi akhir.

---

## 6. Hasil yang Diharapkan dari Set Ini

- Pipeline terbukti: rekam → validasi → ekstraksi → anotasi.
- Estimasi fps efektif dan ukuran data riil di Pi 5.
- Distribusi `Q(x)` pada kondisi bersih (batas bawah untuk menentukan `tau_q` nanti).
- Gambaran awal base classifier pada 24 klip jatuh vs 12 non-jatuh. Dengan n sekecil ini hasilnya **bersifat kelayakan, bukan klaim performa** (interval kepercayaan lebar).

---

## 7. Next Action (berurutan)

| # | Aksi | Output |
|---|---|---|
| 1 | Jalankan `check_topics.sh`: topik sudah dikonfirmasi (PointCloud2 + depth Image); tinggal encoding, fps, bandwidth, `camera_info` | `config.sh` terisi |
| 2 | **Uji teknis `rec_clip.sh`** (klip dummy): `timeout` + SIGINT menutup bag bersih, `ros2 bag info` terbaca `validate_clip.sh`, ukuran/klip, fps efektif (cloud vs tanpa cloud) | Skrip final + angka fps/ukuran |
| 3 | Ukur kamar mandi representatif, tentukan titik pasang dan orientasi kamera | Dimensi ruang + posisi kamera |
| 4 | **Tes grid** (Bagian 2.6) + ukur tinggi, fit pitch dari `REF` | Peta UTUH/BAWAH/KELUAR + `camera_height_m`, `pitch_deg` |
| 5 | Kunci arah jatuh, definisi cepat/pelan, definisi `t_onset` | Dokumen protokol final |
| 6 | Siapkan consent partisipan dan cek kebutuhan etik kampus | Consent tertandatangani |
| 7 | **Ambil 36 klip** sesuai Bagian 2, validasi tiap klip (Bagian 3) | Grid 36/36 |
| 8 | Ekstraksi dengan `extract_clips.py` (sudah ada, diuji dengan bag sintetis; jalankan pada data asli) | `clips/` terisi |
| 9 | Anotasi: 24 `t_onset_s`, 36 `t_end_s`, 36 `valid` di Foxglove (langkah: Bagian 5) | `clips.csv` lengkap |
| 10 | Hitung `Q(x)` (dengan peta lantai per-pixel dari `REF`) pada klip baseline; periksa distribusi | Ringkasan `Q` baseline |
| 11 | Rancang set kedua: HN1–HN5 dan OL1–OL4 (set yang menguji klaim inti) | Draf protokol set 2 |

**Catatan implementasi `Q(x)`:** `floor_depth_ref` harus berupa **peta per-pixel** (bukan skalar, karena kamera miring), margin segmentasi tubuh dari matras awalnya ±5–8 cm bukan 15 cm, lalu dituning.

---

## 8. Keputusan Terbuka dan Keterbatasan

| Item | Status |
|---|---|
| Strategi split dengan 2 partisipan (A: pilot/kelayakan; B: split per sesi; C: tambah partisipan) | **Belum diputuskan** |
| Arah jatuh relatif kamera | Usulan, menunggu keputusan |
| Ambang valid (Bagian 3) | Usulan, dikalibrasi di uji teknis |
| Arsitektur base classifier | Belum dikunci |
| Kebutuhan etik kampus | Belum diverifikasi |
| Ukuran kamar mandi representatif, titik pasang, dan orientasi kamera | **Belum ditentukan**; menentukan area uji |
| Pitch final (60° sementara) | Menunggu tes grid |
| Prediksi geometri (zona UTUH ±0,7 × 0,9 m pada 60°) | Teoritis, menunggu tes grid |

**Keterbatasan yang harus ditulis di naskah:** 2 partisipan (tidak ada klaim generalisasi lintas-orang), jatuh simulasi (bukan jatuh nyata), satu posisi kamera, satu ruangan, set baseline tanpa hard-negative dan observation-limited.

---

## 9. Urutan Perintah dan File Pendukung — *skrip bash belum diuji di Pi*

Semua file ada di folder **`tof_tools/`** (lihat `tof_tools/README_PENGGUNAAN.md` untuk penjelasan tiap file). **Tidak ada package ROS baru**: akuisisi memakai driver Arducam (`arducam_rclpy_tof_pointcloud`), rekam memakai `ros2 bag`, dan sisanya skrip bash. Instalasi tambahan hanya bila perlu: plugin MCAP (`ros-jazzy-rosbag2-storage-mcap`) dan `pip install mcap mcap-ros2-support numpy` untuk ekstraksi.

| File | Fungsi |
|---|---|
| `config.sh` | Topik, FPS, buffer, folder data (edit sekali) |
| `check_topics.sh` | Cek topik, QoS, encoding, hz, bw |
| `rec_clip.sh` | Rekam 1 klip dengan aba-aba GO dan `cue_log.csv` |
| `validate_clip.sh` | Cek otomatis durasi dan jumlah pesan |
| `run_rep.sh` | Loop 9 klip N1..N8b per partisipan per rep, dengan ulang otomatis |
| `extract_clips.py` | Bag MCAP → `depth.npy`, `t.npy`, `meta.json`, peta lantai REF |
| `templates/*.csv` | `clips.csv` (36 baris terisi sebagian) dan `sessions.csv` |

**Urutan perintah (di Pi, kecuali dinyatakan lain)**

```bash
# 0. Salin paket ke Pi (dari PC), lalu:
cd ~/tof_tools && chmod +x *.sh

# 1. Terminal 1: driver (biarkan hidup)
source /opt/ros/jazzy/setup.bash
source ~/Arducam_tof_camera/ros2_publisher/install/setup.bash
ros2 run arducam_rclpy_tof_pointcloud tof_pointcloud

# 2. Terminal 2: cek topik, lalu isi config.sh (TOPIC_DEPTH, TOPIC_CLOUD, FPS_NOMINAL)
./check_topics.sh
nano config.sh

# 3. Uji teknis (ulangi 2-3x; coba REC_CLOUD=0 dan 1), hapus bags/TEST_* sesudahnya
./rec_clip.sh TEST_1 3
./validate_clip.sh TEST_1 3

# 3b. Sebelum rekam sungguhan: ukur ruangan + tes grid (Bagian 2.6), tanpa skrip

# 4. Per sesi: klip REF (tanpa orang)
./rec_clip.sh P1S1_REF 0

# 5. Per rep: 9 klip, rep 2 urutan dibalik
./run_rep.sh P1 1 fwd
./run_rep.sh P1 2 rev

# 6. Akhir sesi: backup ke PC
rsync -av ~/tof_data/ <user>@<ip_pc>:/path/backup_tof/

# 7. Di PC: anotasi di Foxglove, lalu ekstraksi
python3 extract_clips.py --bags <backup>/bags --out <dataset> \
  --depth-topic <TOPIK_DEPTH> --cloud-topic <TOPIK_CLOUD> --cloud-first 30
```

**Status verifikasi:** `extract_clips.py` sudah lolos uji dengan bag MCAP sintetis (Image 16UC1/32FC1 dan PointCloud2 terorganisir). Skrip bash baru dicek sintaksnya; perilaku `timeout` + SIGINT dengan `ros2 bag record` dan format `ros2 bag info` di Jazzy lo harus dibuktikan di langkah 3.
