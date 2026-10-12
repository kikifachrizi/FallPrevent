#!/usr/bin/env bash
# Cek cepat 1 bag setelah direkam. Pakai: ./validate_clip.sh <nama_klip> <detik_aksi>
# Yang dicek otomatis: bag terbaca, file MCAP tertutup (magic byte di akhir), durasi ~ rencana (+-1.5 dtk),
# jumlah pesan >= 90% (FPS_NOMINAL x durasi), lalu QC isi klip dengan qc_clip.py (diam sebelum GO, kecepatan jatuh, dst.).
# Ambang = USULAN awal. Cek visual (tubuh utuh, aksi benar) tetap manual di Foxglove.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/config.sh"
set +u; source /opt/ros/jazzy/setup.bash 2>/dev/null || true; set -u   # setup.bash ROS tidak aman untuk set -u

NAME="${1:?nama klip}"; ACT="${2:?detik aksi}"
BAG="$DATA_DIR/bags/$NAME"
EXP=$((PRE+ACT+POST))   # durasi dihitung sejak recorder siap (rec_clip.sh versi baru)

INFO=$(ros2 bag info "$BAG" 2>&1) || { echo "GAGAL: bag tidak terbaca ($BAG)"; exit 1; }
DUR=$(echo "$INFO" | awk '/Duration:/ {gsub("s","",$2); print $2; exit}')
[ -z "$DUR" ] && { echo "GAGAL: durasi tidak terbaca. Output ros2 bag info:"; echo "$INFO"; exit 1; }

STATUS=PASS
DD=$(awk -v d="$DUR" -v e="$EXP" 'BEGIN{x=d-e; if(x<0)x=-x; print x}')
OKD=$(awk -v x="$DD" 'BEGIN{print (x<=1.5)?1:0}')
echo "Durasi  : ${DUR}s (rencana ${EXP}s) -> $([ "$OKD" = 1 ] && echo OK || echo CEK)"
[ "$OKD" = 1 ] || STATUS=CHECK

while read -r line; do
  tp=$(echo "$line" | sed -E 's/.*Topic: ([^ ]+).*/\1/')
  cnt=$(echo "$line" | sed -E 's/.*Count: ([0-9]+).*/\1/')
  need=$(awk -v f="$FPS_NOMINAL" -v d="$DUR" 'BEGIN{printf "%d", f*d*0.9}')
  ok=$([ "$cnt" -ge "$need" ] && echo OK || echo CEK)
  echo "Pesan   : $tp = $cnt (min $need) -> $ok"
  [ "$ok" = OK ] || STATUS=CHECK
done < <(echo "$INFO" | grep -E "Topic: .*Count:")

for f in "$BAG"/*.mcap; do
  tail_hex=$(tail -c 8 "$f" | xxd -p)
  if [ "$tail_hex" = "894d434150300d0a" ]; then echo "MCAP    : $(basename "$f") tertutup -> OK"
  else echo "MCAP    : $(basename "$f") TIDAK diakhiri magic MCAP -> CEK (file terpotong?)"; STATUS=CHECK; fi
done
echo "UKURAN  : $(du -sh "$BAG" | cut -f1)"

if [ "${QC:-1}" = "1" ] && command -v python3 >/dev/null; then
  echo "--- QC isi klip (qc_clip.py) ---"
  DATA_DIR="$DATA_DIR" PRE="$PRE" python3 "$HERE/qc_clip.py" "$NAME" || echo "qc_clip.py gagal (cek scipy/numpy terpasang)"
fi
echo "HASIL   : $STATUS"
[ "$STATUS" = PASS ]
