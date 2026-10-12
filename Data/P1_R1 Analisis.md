# P1_R1 — Analisis dan Status

Sesi P1 Rep 1, direkam 2026-10-09 (±12:58–13:15 WIB). Bag ada di `P1_R1_Nanas/`, dan salinannya ada di Google Drive (ukuran byte cocok). Alur kerja: [[Alur Pasca Pengambilan Data]]. Kode skenario: [[Skenario Uji Baseline 36 Klip]].

> [!warning] Analisis ulang 2026-10-12 (menggantikan penilaian di bawah)
> Dengan fit bidang lantai, intrinsik kamera, dan kriteria protokol 3.1: **tidak ada klip yang lolos semua kriteria**. P1_R1 diperlakukan sebagai **sesi pilot**. Rekam ulang seluruh P1_R1 setelah perbaikan skrip dan driver.
> - Geometri terukur: kamera 2,84 m, pitch 76° (rencana 2,5 m / 60°), perlu dicek dengan meteran. Tinggi berdiri 1,73–1,75 m. Koreksi ×0,87 di bawah sudah tidak berlaku.
> - Diam ≥ 3 dtk sebelum GO hanya terpenuhi di N1 dan N6.
> - Klip "pelan" tidak ada yang masuk 1,5–3,5 dtk (N5 1,3; N8b 1,2; N7 0,7; N7_RETRY1 0,5). Klip cepat N4 dan N6 benar (0,7–0,8 dtk). N3 duduk 3,4 dtk.
> - 20–50% piksel tubuh invalid (IR terserap?). Depth terkuantisasi (±12 cm).
> - Detail dan diagram: `Data/peta_jalan_fallprevent.html` (dan artifact claude.ai "Peta Jalan FallPrevent").

## Status klip (penilaian awal, 2026-10-12)

| Klip | Skenario | Status | Jatuh (berdiri → lantai) | Turun maks* | Catatan |
|---|---|---|---|---|---|
| N1 | Berdiri diam | ✅ Valid | – | – | Masuk frame di ~0,5 dtk, bukan diam sejak awal |
| N2 | Jalan silang | ✅ Valid | – | – | Frame kosong 2,5 dtk, lalu menyeberang |
| N3 | Duduk (kursi) | ✅ Valid | – | ~1 m/s | Turun ±1,5 dtk ke ~0,6–0,8 m, **mirip jatuh pelan** |
| N4 | Depan, cepat | ✅ Valid | 9,0 → 9,3 dtk | ~1,4 m/s | |
| N5 | Depan, pelan | ✅ Valid | 8,8 → 9,6 dtk | ~1,0 m/s | |
| N6 | Belakang, cepat | ✅ Valid (durasi −2,7 dtk) | 7,0 → 7,3 dtk | ~2,4 m/s | Bag terlambat mulai, pre-buffer terpotong |
| N7 | Belakang, pelan | ⚠️ Ambil ulang | 5,6 → 6,2 dtk | ~2,3 m/s | Kecepatannya seperti jatuh cepat, durasi −3,4 dtk |
| N7_RETRY1 | Belakang, pelan | ⚠️ Ambil ulang | 5,7 → 6,1 dtk | ~2,1 m/s | Kecepatannya seperti jatuh cepat, durasi −4,7 dtk |
| N8a | Samping, cepat | ✅ Valid | 8,3 → 8,5 dtk | ~2,3 m/s | |
| N8b | Samping, pelan | ⚠️ Ambil ulang | 7,4 → 7,8 dtk | ~1,8 m/s | Hampir sama dengan N8a |

\* Kecepatan sudah dikoreksi pitch 60° (×0,87). Tinggi berdiri terbaca sekitar 1,6 m.

**Dihapus 2026-10-12:** N2_x1 dan N4_x1 (percobaan gagal), serta N6_RETRY1 (duplikat N6). Salinannya masih ada di Drive.

Penilaian awal: 7/9 layak (N1–N6, N8a), ambil ulang N7 dan N8b. **Sudah diganti oleh analisis ulang di atas.**

## Untuk pengambilan ulang

- Pastikan "pelan" benar-benar 1,5–3,5 dtk dari awal turun sampai di matras. Contoh yang sudah benar: N5 (0,85 dtk, ~1 m/s), dan itu pun masih di bawah 1,5 dtk.
- Partisipan sudah diam di posisi **sebelum** rekam dimulai. Pre-buffer yang terpotong disebabkan bug sinkronisasi GO di `rec_clip.sh` (lihat [[Penyelarasan Repo dan Pipeline]]), jadi skripnya yang perlu diperbaiki.
- Ikuti penamaan `_xN` untuk klip gagal, jangan `_RETRY1`.
- Rekam juga klip `REF` (tanpa orang), `cue_log.csv`, dan isi `sessions.csv` (tinggi kamera, pitch, tinggi badan, pakaian).

## Temuan teknis

- 30 Hz stabil. Satu-satunya celah besar adalah 314 ms di N3 (sekitar detik 0,4), dan ada beberapa timestamp duplikat.
- Adegan kosong berisi objek statis setinggi ±0,5 m, yang tingginya mirip orang berbaring. Jadi selain tinggi, perlu fitur luas atau bentuk area.
- Integritas: semua bag diakhiri magic MCAP. Sesi laptop sempat menyimpulkan file di Drive rusak, tapi itu kemungkinan karena unduhannya belum selesai.
