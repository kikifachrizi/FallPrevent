# Penyelarasan Repo FallPrevent dengan Data Asli

Hasil pemeriksaan repo `github.com/kikifachrizi/FallPrevent` (commit `9032cc8`) terhadap data P1_R1 asli, pada 2026-10-12. Lanjutan dari [[Alur Pasca Pengambilan Data]].

## Peta pipeline: rencana vs status nyata

| Blok (PLAN_OVERVIEW) | Rencana | Status nyata | Yang perlu dilakukan |
|---|---|---|---|
| 1. Sensor + ROS 2 | PointCloud2 + depth **Image** | Depth berupa `Float32MultiArray` (meter). Cloud = reproyeksi depth yang sama persis | Perbarui dokumen. **`REC_CLOUD=0` aman** (lihat intrinsik di bawah) |
| 2. Rekam | `rec_clip.sh`, belum diuji | Sudah dipakai untuk P1_R1. Bag tertutup bersih (13/13 punya `metadata.yaml` dan footer MCAP) | Perbaiki sinkronisasi GO (lihat di bawah) dan `check_topics.sh` |
| 3. Dataset + anotasi | `extract_clips.py`, Foxglove | Ekstraksi gagal untuk format asli. Anotasi belum | Tambah pembaca Float32MultiArray. Onset semi-otomatis (opsi B) sudah bisa dari kurva tinggi |
| 4. Preprocessing | REF median per-piksel, selisih > margin, komponen terbesar | Prototipe ada (background dari frame kosong, ambang 0,25 m) | Butuh klip REF. Margin 5–8 cm **terlalu kecil** untuk noise ~10 cm |
| 5a. P(jatuh\|x) | Fitur: tinggi p95, luas, aspect ratio, dh/dt, centroid. Model: logistik | Prototipe fitur tinggi dan dh/dt sudah jalan ([[P1_R1 Analisis]]) | Tambah luas, aspect ratio, dan centroid 3D. N3 (duduk) mirip N5 |
| 5b. Q(x) | valid_ratio, edge_touch, continuity | Belum | `edge_touch` harus relatif ke **elips area valid**, bukan tepi gambar 240×180 |
| 6–7. Keputusan, evaluasi | Sistem A/B/C, unit = klip | Belum | – |
| 8. Real-time | rclpy, C++ bila perlu | Ada node C++ lama di `archive/` (tidak cocok, lihat di bawah) | – |

## Fakta teknis baru

### Intrinsik kamera (terverifikasi, galat 0 mm)
Cloud `/point_cloud` = setiap piksel depth valid, diurutkan per baris, dengan rumus:

```
x = (u - 120) * z / 190.9      u = kolom 0..239
y = (v - 90)  * z / 191.3      v = baris 0..179
z = depth (m)
```

Artinya: koordinat 3D bisa dihitung dari depth saja. Rekaman cloud **tidak perlu**, dan ukuran data turun sekitar separuh (~5 MB/dtk → ~2,5 GB untuk 36 klip). Ini menjawab keputusan terbuka #2 (`REC_CLOUD`). Frame cloud = frame optik kamera (meski labelnya `map`). Untuk tinggi di atas lantai, masih perlu fit bidang lantai dari REF (tinggi + pitch).

### Orientasi
Kode lama memakai `flipud(fliplr())` (rotasi 180°), jadi kamera terpasang terbalik di box. Konsistenkan di seluruh pipeline, terutama untuk `edge_touch` (tepi mana yang dianggap "bawah").

### Sinkronisasi GO pada `rec_clip.sh`
Skrip menunggu `INIT+PRE` = 7 dtk dari saat `ros2 bag record` **diluncurkan**, bukan dari saat rekaman benar-benar mulai. Kalau startup recorder lambat, GO jatuh lebih awal di timeline bag. Ini menjelaskan N6/N7 (bag −2,7 sampai −4,7 dtk, GO sekitar detik 2,3–4,3, sehingga pre-buffer < 5 dtk dan validasi durasi gagal).
**Perbaikan:** tunggu sampai recorder benar-benar menulis (misalnya log "Recording..." muncul di `last_rec.log`, atau file `.mcap` mulai bertambah) sebelum menghitung PRE. Simpan juga `t_cue` relatif terhadap awal bag: `t_cue_s = cue_epoch − bag_start`.

## Bug di kode lama (`src/venvRos`, `archive/`)

| File | Masalah |
|---|---|
| `src/venvRos/X.npy` | Shape (3,89,64,64), **seluruhnya bernilai 0**. `y` = [1,1,1], jadi hanya kelas jatuh, 3 sampel |
| `preprocess.py`, `preprocess_node.cpp` | `clip(100, 4000)` mengasumsikan mm, padahal data dalam meter (0–4). Semua piksel menjadi 100, sehingga diff = 0. Inilah sebab X.npy kosong |
| `data_processing_node.cpp` | Jendela 90 frame stride 45, label dari topik `/activity_label`. Tidak terlacak per klip/partisipan (bertentangan dengan skema baru) |
| `archive/rosbag2_2026_03_10…` | Hanya depth, 463 pesan dalam 109 dtk = **4,3 Hz** (konfigurasi lama). Sekarang 30 Hz |

Kesimpulan: jalur lama (diff frame → CNN, opsi E di PLAN) sudah ditinggalkan. Kode lama hanya berguna sebagai referensi orientasi dan format.

## Inkonsistensi dokumen ↔ skrip

| Hal | Dokumen | Skrip |
|---|---|---|
| Urutan Rep 2 | Repo (versi peneliti): N1→N8b, "urutan diatur operator". Draf lama di vault: dibalik | ✅ `run_rep.sh` kini mendukung `fwd` (default) dan `rev` |
| Topik depth | `config.sh`: "sensor_msgs/msg/Image" | Aslinya `/depth_frame` Float32MultiArray. `check_topics.sh` hanya mencari tipe Image, jadi depth tidak terdeteksi |
| Klip ulang | `_xN` | P1_R1 memakai `_RETRY1`, yang tidak dilewati oleh `extract_clips.py` (hanya `_x\d+`) |
| Error sensor | ±2 cm | Noise lantai ~10 cm |
| Versi Skenario | **Koreksi:** versi repo adalah versi yang sudah diedit peneliti (disederhanakan). `Referensi/Skenario Uji Baseline 36 Klip.md` adalah draf lama yang lebih panjang (kriteria valid rinci, bagian anotasi) | ✅ Repo diperbarui dengan temuan pilot; pakai `tof_tools/Skenario_Uji_Pengambilan_Data_ToF_36_Klip.md` sebagai acuan |

## Daftar perbaikan (urut prioritas)

> [!success] Status 12 Okt 2026 (branch `fix/pilot-p1r1`)
> Poin 1–4 sudah dikerjakan dan diuji di PC: `extract_clips.py` (bag pilot asli, galat 0 mm), `rec_clip.sh` (publisher dummy), `check_topics.sh`, `run_rep.sh rev`, plus `qc_clip.py` baru. Dua bug lama ikut diperbaiki: `set -u` + `source setup.bash` membuat skrip keluar diam-diam, dan SIGINT ke recorder background diabaikan. Belum: uji di Pi dengan driver asli (poin 6).

1. `extract_clips.py`: dukung `Float32MultiArray` (reshape 180×240, ×1000 → uint16 mm), skip cloud, abaikan `_RETRY\d+` atau ganti namanya jadi `_xN`.
2. `rec_clip.sh`: GO disinkronkan ke rekaman yang sudah berjalan. `config.sh`: `TOPIC_DEPTH=/depth_frame`, `TOPIC_CLOUD=/point_cloud`, `REC_CLOUD=0` (cloud direkam hanya di klip REF, untuk verifikasi).
3. `check_topics.sh`: deteksi juga `std_msgs/msg/Float32MultiArray`.
4. `run_rep.sh`: tambahkan argumen `fwd`/`rev`.
5. Margin segmentasi: kalibrasi dari noise riil (std per-piksel di REF), jangan dipatok 5–8 cm.
6. Saat P2 dan rekaman ulang: cek mode 2 m/4 m dan filter driver karena noise ~10 cm.
7. Set HN (duduk, jongkok, berbaring sengaja) penting, karena N3 sudah menunjukkan duduk mirip jatuh pelan.
