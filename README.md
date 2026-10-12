# Fall Prevention ToF

Proyek ini berisi rancangan pengambilan data dan perangkat pendukung untuk sistem deteksi jatuh berbasis kamera Time-of-Flight (ToF).

## Dokumentasi

- [Panduan penggunaan tools](tof_tools/README_PENGGUNAAN.md)
- [Skenario uji pengambilan data ToF 36 klip](tof_tools/Skenario_Uji_Pengambilan_Data_ToF_36_Klip.md)
- [Overview rencana dan arsitektur sistem](tof_tools/PLAN_OVERVIEW.md)

Skrip, konfigurasi, template, dan dokumentasi teknis tersedia di folder [`tof_tools`](tof_tools/).

## Catatan folder lama

`src/venvRos/` dan `archive/` adalah jalur lama (selisih frame → CNN) yang sudah ditinggalkan, dan hanya disimpan sebagai referensi. `src/venvRos/X.npy` berisi nol semua karena bug satuan (clip 100–4000 mengasumsikan mm, padahal data dalam meter). Pipeline yang dipakai sekarang ada di `tof_tools/`.
