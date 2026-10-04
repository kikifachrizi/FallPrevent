#!/usr/bin/env bash
# Rekam 9 klip (N1..N8b) untuk 1 partisipan, 1 rep.
# Pakai: ./run_rep.sh <partisipan> <rep>
# Contoh: ./run_rep.sh P1 1      -> P1_R1_N1 ... P1_R1_N8b (urutan tetap N1 -> N8b)
# Urutan lain: lewati klip dengan `s`, atau rekam klip tertentu langsung dengan rec_clip.sh.
# Tiap klip: Enter = mulai, s = lewati, q = keluar. Setelah rekam ada validasi otomatis
# + pertanyaan "valid?" (cek visual/aksi). Jika n: bag diganti nama _x1, _x2, ... dan slot diulang (maks 3x).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/config.sh"

P="${1:?partisipan, mis. P1}"; R="${2:?rep, mis. 1}"

# format: "<kode> <detik_aksi>"
CLIPS=("N1 5" "N2 5" "N3 3" "N4 1" "N5 3" "N6 1" "N7 3" "N8a 1" "N8b 3")

mkdir -p "$DATA_DIR"
for entry in "${CLIPS[@]}"; do
  read -r code act <<< "$entry"
  name="${P}_R${R}_${code}"
  tries=0
  while :; do
    read -r -p ">> Siap ${name} (aksi ${act} dtk). Enter=mulai, s=lewati, q=keluar: " ans
    [ "$ans" = "q" ] && exit 0
    [ "$ans" = "s" ] && break
    "$HERE/rec_clip.sh" "$name" "$act" || { echo "rec_clip gagal; periksa pesan di atas."; continue; }
    "$HERE/validate_clip.sh" "$name" "$act"
    read -r -p ">> Aksi sesuai kode & partisipan ikut aba-aba? valid [y/n]: " ok
    echo "${name},${ok},try$((tries+1)),$(date +%s)" >> "$DATA_DIR/clip_log.csv"
    [ "$ok" = "y" ] && break
    tries=$((tries+1))
    mv "$DATA_DIR/bags/$name" "$DATA_DIR/bags/${name}_x${tries}"
    if [ "$tries" -ge 3 ]; then
      echo "3x gagal untuk ${name}. Berhenti: cari penyebabnya dulu."; exit 1
    fi
  done
done
echo "Selesai rep ${R} untuk ${P}."
