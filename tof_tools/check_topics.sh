#!/usr/bin/env bash
# Cek topik driver. Jalankan SETELAH driver hidup (di terminal lain).
# Pakai: ./check_topics.sh
source /opt/ros/jazzy/setup.bash 2>/dev/null || true

echo "=== Semua topik ==="
ros2 topic list -t

IMG=$(ros2 topic list -t | awk '$2 ~ /sensor_msgs\/msg\/Image/ {print $1}')
PCL=$(ros2 topic list -t | awk '$2 ~ /sensor_msgs\/msg\/PointCloud2/ {print $1}')
echo
echo "=== Kandidat ==="
echo "Image      : ${IMG:-<tidak ada>}"
echo "PointCloud2: ${PCL:-<tidak ada>}"

for t in $IMG; do
  echo; echo "##### IMAGE $t"
  ros2 topic info -v "$t" | grep -E "Publisher count|Reliability|Durability"
  for f in header.frame_id encoding height width step; do
    printf '%s: ' "$f"; ros2 topic echo --once "$t" --field "$f" 2>/dev/null | head -1
  done
  echo "-- hz (8 dtk)"; timeout 8 ros2 topic hz "$t" 2>&1 | tail -3
  echo "-- bw (8 dtk)"; timeout 8 ros2 topic bw "$t" 2>&1 | tail -2
done

for t in $PCL; do
  echo; echo "##### POINTCLOUD2 $t"
  ros2 topic info -v "$t" | grep -E "Publisher count|Reliability|Durability"
  for f in header.frame_id height width point_step row_step is_dense; do
    printf '%s: ' "$f"; ros2 topic echo --once "$t" --field "$f" 2>/dev/null | head -1
  done
  echo "fields:"; ros2 topic echo --once "$t" --field fields 2>/dev/null | grep -E "name|datatype|offset"
  echo "-- hz (8 dtk)"; timeout 8 ros2 topic hz "$t" 2>&1 | tail -3
  echo "-- bw (8 dtk)"; timeout 8 ros2 topic bw "$t" 2>&1 | tail -2
done

echo
echo "Catatan:"
echo " - Image: encoding 16UC1 = mm, 32FC1 = meter (REP-118). height/width harus 180/240."
echo " - PointCloud2 'terorganisir' bila height=180 dan width=240 (height=1 = tidak terorganisir)."
echo " - Isi TOPIC_DEPTH, TOPIC_CLOUD, FPS_NOMINAL di config.sh."
