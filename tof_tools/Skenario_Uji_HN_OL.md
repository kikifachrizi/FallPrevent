# Skenario Uji : Set Kedua, Hard Negative (HN) dan Observation Limits (OL)

**Status:** Draf 13 Okt 2026, belum diuji. Semua kode, jumlah, dan durasi di bawah adalah **usulan**; keputusan ada di peneliti (lihat Bagian 8).

**Hubungan dengan set baseline:** set ini memakai setup, skrip, aturan nama, dan prosedur per klip yang sama dengan `Skenario_Uji_Pengambilan_Data_ToF_36_Klip.md` (Bagian 1, 2.4, 3). Yang berbeda hanya daftar klip dan kriteria valid tambahan.

**Yang dibuktikan set ini** (dua pertanyaan di `PLAN_OVERVIEW.md` Bagian 0):

| Set | Pertanyaan | Dibandingkan pada | Hasil yang diharapkan bila klaim benar |
|---|---|---|---|
| HN | Apakah sistem bisa membedakan jatuh dari gerakan turun yang disengaja? | Alarm palsu Sistem A, B, C pada klip HN (semua `no_fall`) | C tidak menambah alarm palsu dibanding A; idealnya kasus yang ambigu menjadi "ragu", bukan "jatuh" |
| OL | Apakah sistem menunda keputusan saat observasi buruk, bukan memutus dengan yakin? | Keputusan yakin yang salah dan laju "bukti kurang" pada OL vs N | C lebih sering "bukti kurang" pada OL daripada pada N, dan lebih sedikit keputusan yakin yang salah daripada A dan B |

**Prinsip desain:**
1. **Setiap kondisi OL direkam dalam dua versi, jatuh (`F`) dan tidak jatuh (`N`).** Bila semua klip OL adalah jatuh, `Q(x)` rendah akan identik dengan label jatuh dan model bisa "curang" memakai kualitas sebagai bukti jatuh.
2. **Setiap OL menyasar satu komponen `Q(x)`** (`edge_touch`, `valid_ratio`, `continuity`), supaya kegagalan bisa dilacak ke komponennya.
3. **Kondisi OL dibuat dengan setup fisik yang terukur** (posisi lakban, letak tirai, pakaian), bukan dipilih dari nilai `Q`. Nilai `qc_clip.py` hanya dicatat, tidak dipakai untuk meloloskan klip (menghindari sirkularitas, sama seperti Bagian 3 protokol baseline).

---

## 1. Prasyarat

| Item | Ketentuan |
|---|---|
| Geometri kamera | **Sama dengan sesi baseline** (12 Okt: ±2,48 m, pitch ±69°). Cek dengan `python3 calib_live.py` sebelum mulai; bila rata-rata bergeser > 3 cm atau > 1°, rekam REF baru |
| Area valid | Hasil `calib_live.py` 12 Okt: lantai valid maju 0,16–2,05 m dari titik di bawah kamera, lebar ±0,9 m; pusat gambar di 0,96 m. Tandai batas ini dengan lakban sebelum sesi (dipakai OL1) |
| REF | `<SESI>_REF` seperti biasa, ditambah **REF khusus untuk setiap properti OL yang diam** (Bagian 3) |
| Properti | Matras, kursi (HN5), benda kecil di lantai (HN4), tirai/kain pada rangka berdiri (OL2, OL4), pakaian gelap (OL3) |
| Urutan terhadap baseline | Disarankan **sesi terpisah** dari N1–N8b, supaya jumlah jatuh per hari tidak berlebihan (Bagian 4) |

---

## 2. Set HN (Hard Negative), semua label `no_fall`

Gerakan yang tingginya turun seperti jatuh, tetapi terkendali. Pilot dan sesi 12 Okt sudah menunjukkan **N3 (duduk) mirip jatuh pelan** di kurva tinggi tubuh.

| Kode | Aksi | Arg aksi (dtk) | Durasi bag | Mirip jatuh pada fitur | Instruksi ke partisipan |
|---|---|---|---|---|---|
| HN1 | Jongkok, tahan | 3 | 13 dtk | Tinggi turun ±0,6–0,8 m | Turun ke jongkok dengan kecepatan biasa, tahan sampai bag selesai |
| HN2 | Duduk di lantai/matras dengan sengaja | 4 | 14 dtk | Tinggi akhir rendah, mirip jatuh pelan | Tekuk lutut, tangan menyentuh lantai, duduk; tahan |
| HN3 | Berbaring sengaja di matras | 6 | 16 dtk | **Posisi akhir sama dengan jatuh** | Duduk dulu, lalu rebah perlahan; tahan berbaring |
| HN4 | Membungkuk mengambil benda dari lantai, lalu berdiri | 3 | 13 dtk | Penurunan cepat bagian atas tubuh, lalu naik | Benda kecil diletakkan ±0,5 m di depan posisi awal |
| HN5 | Menjatuhkan diri ke kursi (duduk cepat) | 1 | 11 dtk | **Kecepatan turun** mirip jatuh cepat, berhenti di tinggi kursi | Duduk keras ke kursi dalam ≤ 1 dtk; tahan duduk |

Catatan:
- Posisi awal dan kursi sama dengan N3; arah gerakan menjauhi atau menyamping dari kamera seperti klip N.
- **HN3 secara label bisa diperdebatkan**: orang yang berbaring di lantai kamar mandi mungkin tetap perlu dicek. Bila dianggap ambigu, ganti dengan **berlutut** (mis. membersihkan lantai) dan catat keputusannya.
- HN1 dan HN4 tidak membutuhkan matras, tetapi matras tetap di tempatnya supaya latar sama dengan REF.

---

## 3. Set OL (Observation Limits), tiap kondisi × {jatuh `F`, tidak jatuh `N`}

Untuk semua OL: **`F` = jatuh cepat** (≤ 1 dtk, arah sesuai tabel), **`N` = duduk di lantai** seperti HN2. Keduanya berakhir rendah, sehingga kualitas observasi yang menentukan seberapa yakin sistem boleh memutus.

| Kode | Kondisi | Komponen `Q` yang disasar | Cara membuat | Arah `F` | REF tambahan |
|---|---|---|---|---|---|
| OL1 | **Tubuh terpotong tepi** area valid | `edge_touch` | Posisi awal di dekat batas samping area valid (±0,6 m dari garis tengah, ditandai lakban). Setelah aksi, ±1/3–1/2 tubuh berada di luar elips valid. Matras ikut digeser ke sana | Samping, keluar area | Tidak (latar sama) |
| OL2 | **Tertutup sebagian, diam** (tirai) | `valid_ratio` tubuh | Tirai/kain kedap pada rangka berdiri, menggantung dari ±2 m sampai ±0,3 m di atas lantai, di antara kamera dan area mendarat, menutupi ±separuh area mendarat. Mirip tirai shower | Depan, menjauhi kamera, mendarat di belakang tirai | **Ya**: `<SESI>_REF_OL2` dengan tirai terpasang (di pemakaian nyata tirai adalah bagian latar) |
| OL3 | **Piksel tubuh tanpa depth** (pakaian/penutup kepala gelap) | `valid_ratio` tubuh | Jaket/kaos hitam berbahan menyerap IR + penutup kepala hitam. **Butuh uji kelayakan dulu** (lihat bawah) | Depan, menjauhi kamera | Tidak |
| OL4 | **Tertutup sementara** saat aksi | `continuity` | Tirai yang sama, mulai terbuka; operator menarik tirai melintasi area **tepat setelah GO** (±1 dtk menutup, lalu dibuka lagi). Operator tetap di luar frame, menarik dari ujung rangka | Depan, menjauhi kamera | **Ya**: `<SESI>_REF_OL4` dengan tirai di posisi terbuka (beda dari OL2) |

**Uji kelayakan OL3 (sebelum merekam OL3):** dengan geometri dan REF median, piksel tubuh tanpa depth di sesi 12 Okt hanya ±2–7% (kepala yang paling sering kosong). Belum diketahui apakah pakaian hitam menaikkannya. Rekam satu klip berdiri diam (`<SESI>_OL3TEST_terang` dan `_gelap`, 5 dtk), jalankan `qc_clip.py`, bandingkan baris `Invalid`. Bila selisihnya kecil (< ±10 poin persen), OL3 tidak menghasilkan kondisi yang berbeda; ganti dengan kondisi lain atau gugurkan dan catat di keterbatasan.

**Kriteria valid tambahan OL** (cek visual + setup, bukan dari `Q`):
- OL1: setelah aksi, sebagian tubuh di luar lakban batas area valid (lihat langsung atau di Foxglove).
- OL2: tubuh mendarat di belakang tirai; tirai tidak tersenggol saat jatuh.
- OL3: pakaian sesuai daftar; dicatat di `clothing`.
- OL4: tirai benar-benar melintasi tubuh dalam jendela GO sampai ±2 dtk setelah GO; catat waktu tarik di `notes` bila bisa.

---

## 4. Jumlah klip dan jadwal

| Set | Hitungan | Klip | Klip jatuh |
|---|---|---|---|
| HN | 5 kode × 2 partisipan × 2 rep | 20 | 0 |
| OL | 4 kondisi × 2 versi × 2 partisipan × 2 rep | 32 | 16 |
| **Total** | | **52** | **16** |

Per partisipan: 26 klip, 8 di antaranya jatuh. Ditambah 12 jatuh dari baseline, setiap partisipan jatuh ±20 kali, jadi **pisahkan dari sesi baseline** dan beri istirahat ≥ 30–60 dtk setelah klip jatuh.

**Urutan dalam satu rep (usulan):** HN1 → HN5, lalu OL1N, OL1F, OL3N, OL3F (tanpa properti tambahan), lalu pasang tirai: REF_OL2, OL2N, OL2F, REF_OL4, OL4N, OL4F. Versi `N` sebelum `F` supaya partisipan tidak lelah saat jatuh. Perkiraan ±40–50 menit per partisipan per rep termasuk pasang properti *(kasar)*.

**Keterbatasan jumlah:** 16 klip OL-jatuh dan 36 klip tidak jatuh (20 HN + 16 OL-N) memberi interval kepercayaan lebar. Hasil set ini bersifat **pembuktian arah efek** (C vs A/B pada klip yang sama, uji McNemar), bukan estimasi performa.

---

## 5. Penamaan dan pencatatan

- Nama klip: `P1_R1_HN3`, `P1_R1_OL2F`, `P1_R1_OL2N`. Klip gagal: `_x1`, `_x2`, ... sama seperti baseline.
- REF properti: `<SESI>_REF_OL2`, `<SESI>_REF_OL4`. REF biasa tetap `<SESI>_REF`.
- `clips.csv`: `group` = `HN` atau `OL`; `label` = `no_fall` untuk HN dan `OL*N`, `fall` untuk `OL*F`; kolom `notes` untuk properti, posisi tirai, dan waktu tarik OL4.
- `sessions.csv`: satu baris per sesi set kedua, `ref_clip_id` = REF biasa; REF properti dicatat di `notes`.

---

## 6. Perintah

```bash
cd ~/FallPrevent/tof_tools
python3 calib_live.py --target-h 2.48 --target-pitch 69   # cek geometri sama dengan baseline
./rec_clip.sh S20261015_REF 0                              # REF biasa

./run_rep.sh P1 1 fwd HN                                   # HN1..HN5
./run_rep.sh P1 1 fwd OL                                   # OL1N, OL1F, OL3N, OL3F, OL2N, OL2F, OL4N, OL4F
# run_rep berhenti sebelum OL2N dan OL4N untuk mengingatkan REF properti:
./rec_clip.sh S20261015_REF_OL2 0
./rec_clip.sh S20261015_REF_OL4 0
```

`qc_clip.py` mengenali kode HN dan OL. Untuk OL, baris `Tepi` dan `Invalid` memang diharapkan buruk dan tidak dijadikan saran gagal.

---

## 7. Keselamatan

- Semua klip `F` mendarat di matras, termasuk OL1 (matras digeser ke tepi) dan OL2/OL4 (matras di belakang tirai).
- Rangka tirai ringan dan tidak berada di jalur jatuh; tirai dari kain, bukan papan.
- Pada OL4, operator menarik tirai dari ujung rangka, tidak masuk ke area jatuh.
- HN5: kursi stabil dan tidak beroda; spotter di samping.

---

## 8. Keputusan terbuka (milik peneliti)

| # | Keputusan | Usulan draf ini |
|---|---|---|
| 1 | HN3 berbaring sengaja tetap `no_fall`, atau diganti berlutut | Tetap, dengan catatan ambiguitas |
| 2 | Versi `N` pada OL: duduk di lantai, atau gerakan lain (berdiri, jalan) | Duduk di lantai, karena berakhir rendah seperti jatuh |
| 3 | Satu jenis jatuh untuk OL `F`, atau variasi depan/samping/belakang | Satu jenis per kondisi (Bagian 3), supaya jumlah klip tetap kecil |
| 4 | OL3 dipertahankan atau diganti | Tergantung uji kelayakan |
| 5 | Material tirai OL2/OL4 | Kain gelap tidak tembus pandang; cek di Foxglove bahwa tubuh di belakangnya benar-benar hilang |
| 6 | Set kedua di sesi terpisah atau digabung | Terpisah |
