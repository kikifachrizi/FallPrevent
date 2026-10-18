#!/usr/bin/env bash
# Rekam 1 set klip untuk 1 partisipan, 1 rep. Set N = N1..N8b (baseline), HN = HN1..HN5, OL = OL1N..OL4F
# (lihat Skenario_Uji_HN_OL.md).
# Pakai: ./run_rep.sh <partisipan> <rep> [fwd|rev] [N|HN|OL]
# Contoh: ./run_rep.sh P1 1 fwd  -> P1_R1_N1 ... P1_R1_N8b
#         ./run_rep.sh P1 2 rev  -> P1_R2_N8b ... P1_R2_N1 (opsional; Skenario: rep 2 tetap N1 -> N8b)
#         ./run_rep.sh P1 1 fwd HN -> P1_R1_HN1 ... P1_R1_HN5
# Urutan lain: lewati klip dengan `s`, atau rekam klip tertentu langsung dengan rec_clip.sh.
# Tiap klip: Enter = mulai, s = lewati, q = keluar. Setelah rekam ada validasi otomatis
# + pertanyaan "valid?" (cek visual/aksi). Jika n: bag diganti nama _x1, _x2, ... dan slot diulang (maks 3x).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/config.sh"

P="${1:?partisipan, mis. P1}"; R="${2:?rep, mis. 1}"; ORDER="${3:-fwd}"; SET="${4:-N}"

# format: "<kode> <detik_aksi>"
case "$SET" in
  N)  CLIPS=("N1 5" "N2 5" "N3 3" "N4 1" "N5 3" "N6 1" "N7 3" "N8a 1" "N8b 3") ;;
  HN) CLIPS=("HN1 3" "HN2 4" "HN3 6" "HN4 3" "HN5 1") ;;
  OL) CLIPS=("OL1N 4" "OL1F 1" "OL3N 4" "OL3F 1" "OL2N 4" "OL2F 1" "OL4N 4" "OL4F 1") ;;   # tanpa properti dulu, lalu tirai
  *) echo "Set harus N, HN, atau OL"; exit 1 ;;
esac
case "$ORDER" in
  fwd) ;;
  rev) for ((i=${#CLIPS[@]}-1; i>=0; i--)); do REVD+=("${CLIPS[$i]}"); done; CLIPS=("${REVD[@]}") ;;
  *) echo "Urutan harus fwd atau rev"; exit 1 ;;
esac
echo "Set ${SET}, rep ${R} ${P}, urutan ${ORDER}: $(for e in "${CLIPS[@]}"; do printf '%s ' "${e%% *}"; done)"

mkdir -p "$DATA_DIR"
for entry in "${CLIPS[@]}"; do
  read -r code act <<< "$entry"
  name="${P}_R${R}_${code}"
  tries=0
  case "$code" in
    OL2N|OL4N) echo "!! Sebelum ${code}: pasang tirai untuk ${code%N} lalu rekam REF properti, mis. ./rec_clip.sh <SESI>_REF_${code%N} 0" ;;
  esac
  while :; do
    read -r -p ">> Siap ${name} (aksi ${act} dtk). Partisipan SUDAH diam di posisi? Enter=mulai, s=lewati, q=keluar: " ans
    [ "$ans" = "q" ] && exit 0
    [ "$ans" = "s" ] && break
    "$HERE/rec_clip.sh" "$name" "$act" || { echo "rec_clip gagal; periksa pesan di atas."; continue; }
    "$HERE/validate_clip.sh" "$name" "$act"
    read -r -p ">> Aksi sesuai kode & partisipan ikut aba-aba? valid [y/n]: " ok
    echo "${name},${ok},try$((tries+1)),$(date +%s)" >> "$DATA_DIR/clip_log.csv"
    [ "$ok" = "y" ] && break
    tries=$((tries+1))
    # nomor _x lanjut dari yang sudah ada (mis. dari sesi lain); mv ke folder yang sudah ada akan memindahkan bag KE DALAMNYA
    x=1; while [ -e "$DATA_DIR/bags/${name}_x${x}" ]; do x=$((x+1)); done
    mv "$DATA_DIR/bags/$name" "$DATA_DIR/bags/${name}_x${x}" && echo "Disimpan sebagai ${name}_x${x}"
    if [ "$tries" -ge 3 ]; then
      echo "3x gagal untuk ${name}. Berhenti: cari penyebabnya dulu."; exit 1
    fi
  done
done
echo "Selesai rep ${R} untuk ${P}."
