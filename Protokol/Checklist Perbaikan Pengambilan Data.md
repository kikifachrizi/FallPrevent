# Checklist Perbaikan Pengambilan Data

Disusun 12 Okt 2026 dari hasil QC sesi pilot (9 Okt) dan sesi 12 Okt (P1_R1_1, P2_R1). Acuan protokol: `tof_tools/Skenario_Uji_Pengambilan_Data_ToF_36_Klip.md`.

## Persiapan (sebelum sesi)
- [ ] Pi memakai skrip terbaru (branch `fix/pilot-p1r1`, `git pull`). Sesi 12 Okt masih memakai skrip lama.
- [ ] Pasang `bc` dan `python3-scipy` di Pi, lalu jalankan `./check_topics.sh` dan pastikan depth 30 Hz.
- [ ] `ROS_DOMAIN_ID=42` di PC dan Pi.
- [ ] Saat merekam, **tutup semua subscriber di PC** (Foxglove, RViz, `ros2 topic hz`). Bila dibiarkan, laju rekaman di Pi ikut turun ke 4–6 Hz.
- [ ] Isi `sessions.csv`: tinggi badan, pakaian, tinggi dan pitch kamera (ukur dengan meteran).

## REF
- [ ] Rekam **REF lebih dulu**, sebelum klip pertama: `./rec_clip.sh <SESI>_REF 0`
- [ ] Saat REF: ruangan kosong, matras dan kursi di posisinya, operator di luar frame, ±10 dtk.
- [ ] Rekam REF baru setiap kali kamera atau matras bergeser.

## Per klip
- [ ] Partisipan **sudah diam di posisi sebelum Enter**, lalu tetap diam ±5 dtk sampai aba-aba GO. Ini paling sering gagal: hampir semua klip diamnya < 3 dtk.
- [ ] Aksi dimulai segera setelah GO (≤ 3 dtk).
- [ ] Posisi awal **lebih ke tengah** area, ditandai lakban. P2 sering terlalu ke pinggir.
- [ ] **Jatuh pelan harus 1,5–3,5 dtk.** Latih dulu dengan klip `_warmup` sebelum N5/N7/N8b. Baru 3 dari 8 klip pelan yang masuk rentang.
- [ ] Setelah tiap klip jalankan `./validate_clip.sh <nama> <aksi>`, lalu lihat baris **SARAN**.
- [ ] Klip gagal diberi akhiran `_x1`, `_x2`, dan seterusnya. Jangan pakai `_RETRY`.
- [ ] Rekaman dihentikan oleh skrip, jangan Ctrl+C manual (contoh: `P1_R1_1_N6` jadi 22,9 dtk).

## Setelah sesi
- [ ] Kirim semua bag, **REF, dan `cue_log.csv`** ke PC: `rsync -avP ~/tof_data/bags/ ~/tof_data/cue_log.csv aiserver-kiki@10.42.0.1:~/FallPrevent/`

## Rekam ulang dari sesi 12 Okt
- [ ] P1: **N7, N8b**. N6 dan N7: `_x` di P1_R1_1 adalah **rekaman ulang** (bukan klip gagal). Ganti nama: `N6` → `N6_x1`, `N6_x` → `N6`; begitu juga N7. N6 ulang sudah valid (0,33 dtk); N7 ulang masih terlalu cepat (1,1 dtk).
- [ ] P2: **N7**. N8b opsional (1,40 dtk, sedikit di bawah batas).
- [ ] REF ulang pada 30 Hz, bila setup kamera masih sama.

Terkait: [[Alur Pasca Pengambilan Data]] · [[Penyelarasan Repo dan Pipeline]]
