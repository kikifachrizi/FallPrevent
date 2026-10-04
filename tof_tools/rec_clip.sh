#!/usr/bin/env bash
# Rekam 1 klip = 1 bag. Pakai: ./rec_clip.sh <nama_klip> <detik_aksi>
# Contoh : ./rec_clip.sh P1_R1_N4 1        (jatuh depan cepat, aksi ~1 dtk)
#          ./rec_clip.sh P1S1_REF 0        (klip REF tanpa orang)
# Alur   : bag mulai -> INIT dtk -> PRE dtk diam -> "GO" -> aksi -> POST dtk diam -> bag selesai
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/config.sh"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true

NAME="${1:?nama klip, mis. P1_R1_N4}"
ACT="${2:?durasi aksi (detik)}"

case "$TOPIC_DEPTH" in *GANTI*) echo "Isi TOPIC_DEPTH di config.sh dulu."; exit 1;; esac
TOPICS="$TOPIC_DEPTH"
if [ "$REC_CLOUD" = "1" ]; then
  case "$TOPIC_CLOUD" in *GANTI*) echo "Isi TOPIC_CLOUD di config.sh (atau set REC_CLOUD=0)."; exit 1;; esac
  TOPICS="$TOPICS $TOPIC_CLOUD"
fi

mkdir -p "$DATA_DIR/bags"
BAG="$DATA_DIR/bags/$NAME"
[ -e "$BAG" ] && { echo "SUDAH ADA: $BAG (ganti nama atau pindahkan dulu)"; exit 1; }

TOTAL=$((INIT+PRE+ACT+POST))
timeout -s INT "$TOTAL" ros2 bag record -s mcap -o "$BAG" $TOPICS >"$DATA_DIR/last_rec.log" 2>&1 &
RECPID=$!

sleep $((INIT+PRE))
echo ">>> GO <<<"; printf '\a'
echo "$NAME,$(date +%s.%N)" >> "$DATA_DIR/cue_log.csv"

wait $RECPID    # exit code 124 dari `timeout` itu normal
echo "SELESAI $NAME (total ${TOTAL} dtk)"

if [ ! -f "$BAG/metadata.yaml" ]; then
  echo "PERINGATAN: metadata.yaml tidak ada -> bag tidak tertutup bersih. Lihat $DATA_DIR/last_rec.log"
  exit 2
fi
