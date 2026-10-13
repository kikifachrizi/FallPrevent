# Alur Pasca Pengambilan Data

Diringkas dari [[Skenario Uji Baseline 36 Klip]] (Bagian 3–5, 7, 9), lalu disesuaikan dengan format data asli yang ditemukan di [[P1_R1 Analisis]].

## Urutan kerja

| # | Langkah | Output | Status P1_R1 |
|---|---|---|---|
| 1 | Validasi cepat per klip, langsung setelah rekam (`ros2 bag info`, `validate_clip.sh`) | Valid → lanjut, tidak valid → `_xN` lalu rekam ulang | Sudah dijalankan |
| 2 | Backup `bags/` ke PC setelah setiap sesi, lalu verifikasi checksum (`sha256sum` atau `md5sum`) | Salinan kedua terverifikasi | Ada di server dan di Drive, ukuran cocok |
| 3 | Cek integritas file: harus diakhiri magic MCAP `894d434150300d0a` (`tail -c 8 f.mcap \| xxd -p`) | Semua bag utuh | ✅ 13/13 utuh di server |
| 4 | Pemeriksaan isi di Foxglove: arah dan kecepatan jatuh sesuai kode, tubuh utuh dalam frame, diam ≥ 3 dtk sebelum GO dan sesudah aksi | Kolom `valid` dan `invalid_reason` | Analisis otomatis selesai, cek visual belum |
| 5 | Ekstraksi `raw/*.mcap` → `clips/<id>/depth.npy` (T,180,240) uint16 mm, `t.npy`, `meta.json` | Folder `clips/` | ❗ `extract_clips.py` perlu disesuaikan (lihat di bawah) |
| 6 | Peta lantai per-piksel dari klip `REF` → `ref/S1_floor_ref.npy` | Floor map + fit tinggi dan pitch | ❌ Klip REF belum ada |
| 7 | Anotasi `clips.csv`: `t_onset_s` (24 klip jatuh), `t_end_s` dan `valid` (36 klip) | `clips.csv` lengkap | Ada draf dari analisis otomatis |
| 8 | Hitung `Q(x)` dan `P(fall\|x)` per frame → `frames.csv` (`phase` = pre/action/post) | Distribusi Q baseline | Belum |
| 9 | `splits.csv` dengan grup per partisipan (opsi A/B/C belum diputuskan) | Split | Belum |
| 10 | Evaluasi Sistem A/B/C | Hasil | Belum |

Alur data: `raw/*.mcap` → ekstraksi → `clips/` → anotasi `clips.csv` → `Q`, `P_fall` → `frames.csv` → evaluasi.

## Struktur dataset target

```
dataset_tof_fall/
├── raw/            # mcap mentah, tidak diubah (sumber kebenaran)
├── clips/<id>/     # depth.npy (T,180,240) uint16 mm, t.npy (T,) int64 ns, meta.json
├── ref/            # S1_floor_ref.npy (180,240), median depth lantai dari REF
├── sessions.csv    # 1 baris per sesi (tinggi kamera, pitch, pakaian, driver params, ...)
├── clips.csv       # 1 baris per klip (label, t_onset_s, t_end_s, valid, ...)
├── frames.csv      # turunan: valid_ratio, edge_touch, continuity, Q, P_fall
└── splits.csv
```

## Kriteria klip valid (ringkas)

- File: bag terbuka, topik lengkap, **durasi = rencana ±1,5 dtk**, jumlah frame ≥ 90% dari yang diharapkan, tidak ada jeda antar-frame > 3× median di jendela aksi.
- Prosedur: ada entri `cue_log.csv`, diam ≥ 3 dtk sebelum GO dan sesudah aksi, aksi dimulai ≤ 3 dtk setelah GO.
- Aksi: sesuai kode. Cepat = sampai di matras dalam ≤ 1 dtk, pelan = 1,5–3,5 dtk.
- Baseline bersih: seluruh tubuh terlihat, mulai dari titik grid UTUH, tidak ada orang atau objek lain, properti tidak bergeser.
- Klip tidak valid **diberi suffix `_xN`, tidak dihapus** (aturan protokol).
- `Q(x)` **tidak** dipakai sebagai kriteria valid (supaya tidak sirkular).

Durasi rencana: N1/N2 17 dtk, N3/N5/N7/N8b 15 dtk, N4/N6/N8a 13 dtk (2 init + 5 pre + aksi + 5 post). GO jatuh sekitar detik ke-7 dari awal bag, jadi `t_onset_s` wajar di sekitar 7–10 dtk.

## Perbedaan protokol dengan kenyataan (harus diperbaiki)

| Asumsi di protokol | Kenyataan di data |
|---|---|
| Depth berupa `sensor_msgs/Image` (16UC1/32FC1) | `/depth_frame` bertipe `std_msgs/Float32MultiArray`, 43.200 float (180×240), satuan meter, 0 = invalid, `layout` kosong |
| PointCloud2 terorganisir | `/point_cloud` tidak terorganisir (height=1), hanya titik valid (~15–17 ribu), xyz di frame kamera tapi diberi label `map` |
| `extract_clips.py` siap pakai | Tidak bisa membaca format ini, jadi `image_to_mm` dan `cloud_to_xyz` perlu disesuaikan |
| Klip gagal diberi suffix `_xN` | Dipakai di N2 dan N4, tapi N6 dan N7 malah diberi nama `_RETRY1` sementara bag aslinya tidak diganti nama |
| Ada `REF`, `cue_log.csv`, `clips.csv`, `sessions.csv` | Belum ada untuk P1 |
| Error sensor ±2 cm | Noise lantai temporal sekitar 10–11 cm (perlu dicek mode 2 m/4 m dan filter driver) |
| Ukuran data | Sekitar 10,8 MB/dtk (separuhnya cloud), 100–180 MB per klip |

## Catatan geometri

- Kamera sekitar 2,5 m, pitch 60°, lantai sekitar 3,0 m sepanjang sumbu optik.
- Selisih depth terhadap background melebihkan tinggi vertikal sekitar 1/sin 60° (≈15%), jadi kalikan 0,87 sebagai pendekatan, atau pakai peta lantai per-piksel dari REF.
- Hanya sekitar 35–39% piksel valid, membentuk elips di tengah frame.

## Setup Pi

Lihat [[Setup Raspi 5 Arducam ToF]]: `ROS_DOMAIN_ID=42`, driver `arducam_rclpy_tof_pointcloud`, `ros2 bag record /point_cloud /depth_frame`, Foxglove bridge di port 9090 (matikan saat merekam).
