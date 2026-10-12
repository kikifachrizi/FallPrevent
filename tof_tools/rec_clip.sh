#!/usr/bin/env bash
# Rekam 1 klip = 1 bag. Pakai: ./rec_clip.sh <nama_klip> <detik_aksi>
# Contoh : ./rec_clip.sh P1_R1_N4 1        (jatuh depan cepat, aksi ~1 dtk)
#          ./rec_clip.sh P1S1_REF 0        (klip REF tanpa orang)
# Alur   : recorder start -> TUNGGU sampai benar-benar merekam -> PRE dtk diam -> "GO" -> aksi -> POST dtk -> stop (SIGINT)
#
# Kenapa menunggu: di pilot P1_R1 recorder kadang butuh 0,6-4,7 dtk sebelum merekam. Versi lama menghitung
# PRE sejak recorder diluncurkan, jadi GO jatuh terlalu awal di timeline bag dan pre-buffer terpotong.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/config.sh"
set +u; source /opt/ros/jazzy/setup.bash 2>/dev/null || true; set -u   # setup.bash ROS tidak aman untuk set -u

NAME="${1:?nama klip, mis. P1_R1_N4}"
ACT="${2:?durasi aksi (detik)}"

case "$TOPIC_DEPTH" in *GANTI*) echo "Isi TOPIC_DEPTH di config.sh dulu."; exit 1;; esac
TOPICS="$TOPIC_DEPTH"
if [ "$REC_CLOUD" = "1" ] || { [ "${REC_CLOUD_REF:-0}" = "1" ] && [[ "$NAME" == *REF* ]]; }; then
  TOPICS="$TOPICS $TOPIC_CLOUD"
fi
NTOP=$(wc -w <<< "$TOPICS")

mkdir -p "$DATA_DIR/bags"
BAG="$DATA_DIR/bags/$NAME"
LOG="$DATA_DIR/last_rec.log"
[ -e "$BAG" ] && { echo "SUDAH ADA: $BAG (ganti nama atau pindahkan dulu)"; exit 1; }

t_launch=$(date +%s.%N)
# `timeout` dipakai sebagai pembungkus: proses background di skrip non-interaktif mengabaikan SIGINT,
# sedangkan `timeout` meneruskan SIGINT ke recorder. Batas waktunya hanya jaring pengaman.
SAFETY=$(echo "$INIT_MAX + $PRE + $ACT + $POST + 15" | bc | cut -d. -f1)
timeout -s INT "$SAFETY" ros2 bag record -s mcap -o "$BAG" --topics $TOPICS >"$LOG" 2>&1 &
RECPID=$!
trap 'kill -INT $RECPID 2>/dev/null' INT TERM

# Tunggu sampai semua topik ter-subscribe DAN file .mcap mulai berisi data.
ready=0
for _ in $(seq 1 $((INIT_MAX*10))); do
  kill -0 $RECPID 2>/dev/null || { echo "GAGAL: ros2 bag record berhenti. Lihat $LOG"; exit 2; }
  nsub=$(grep -c "Subscribed to topic" "$LOG" 2>/dev/null || true)
  sz=$(stat -c %s "$BAG"/*.mcap 2>/dev/null | head -1)
  if [ "${nsub:-0}" -ge "$NTOP" ] && [ "${sz:-0}" -gt 100000 ]; then ready=1; break; fi
  sleep 0.1
done
if [ "$ready" != 1 ]; then
  echo "GAGAL: recorder belum merekam setelah ${INIT_MAX} dtk (topik ter-subscribe: ${nsub:-0}/$NTOP). Lihat $LOG"
  kill -INT $RECPID 2>/dev/null; wait $RECPID; exit 2
fi
t_ready=$(date +%s.%N)
printf 'Recorder siap (%.1f dtk setelah start). Partisipan DIAM...\n' "$(echo "$t_ready - $t_launch" | bc)"

sleep "$PRE"
t_go=$(date +%s.%N)
echo ">>> GO <<<"; printf '\a'
# cue_log.csv: clip_id, go_epoch, ready_epoch, launch_epoch, act_s  (jam sistem Pi; bag memakai jam yang sama)
[ -f "$DATA_DIR/cue_log.csv" ] || echo "clip_id,go_epoch,ready_epoch,launch_epoch,act_s" > "$DATA_DIR/cue_log.csv"
echo "$NAME,$t_go,$t_ready,$t_launch,$ACT" >> "$DATA_DIR/cue_log.csv"

sleep "$(echo "$ACT + $POST" | bc)"
kill -INT $RECPID 2>/dev/null
wait $RECPID
echo "SELESAI $NAME (PRE ${PRE} + aksi ${ACT} + POST ${POST} dtk setelah recorder siap)"

if [ ! -f "$BAG/metadata.yaml" ]; then
  echo "PERINGATAN: metadata.yaml tidak ada -> bag tidak tertutup bersih. Lihat $LOG"
  exit 2
fi
