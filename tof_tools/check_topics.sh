#!/usr/bin/env bash
# Cek topik driver. Jalankan SETELAH driver hidup (di terminal lain).
# Pakai: ./check_topics.sh
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
[ -n "${ROS_DOMAIN_ID:-}" ] && echo "ROS_DOMAIN_ID=$ROS_DOMAIN_ID" || echo "PERINGATAN: ROS_DOMAIN_ID belum diset (PC dan Pi memakai 42, lihat Setup Raspi)"

echo "=== Semua topik ==="
ros2 topic list -t

IMG=$(ros2 topic list -t | awk '$2 ~ /sensor_msgs\/msg\/Image/ {print $1}')
PCL=$(ros2 topic list -t | awk '$2 ~ /sensor_msgs\/msg\/PointCloud2/ {print $1}')
ARR=$(ros2 topic list -t | awk '$2 ~ /std_msgs\/msg\/Float32MultiArray/ {print $1}')   # driver Arducam: /depth_frame
echo
echo "=== Kandidat ==="
echo "Image      : ${IMG:-<tidak ada>}"
echo "Float32Arr : ${ARR:-<tidak ada>}   (depth driver Arducam)"
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

for t in $ARR; do
  echo; echo "##### FLOAT32MULTIARRAY $t"
  ros2 topic info -v "$t" | grep -E "Publisher count|Reliability|Durability"
  python3 - "$t" <<'PY'
import sys, rclpy, numpy as np
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
rclpy.init(); n = Node("check_depth"); got = []
n.create_subscription(Float32MultiArray, sys.argv[1], lambda m: got.append(np.asarray(m.data, np.float32)), 10)
while rclpy.ok() and len(got) < 30: rclpy.spin_once(n, timeout_sec=2.0)
a = np.stack(got); v = a[a > 0]
print(f"panjang data: {a.shape[1]} (harus 43200 = 180x240)")
print(f"piksel valid: {np.mean(a > 0) * 100:.0f}% · rentang {v.min():.2f}-{v.max():.2f} m · median {np.median(v):.2f} m")
u, c = np.unique(np.round(v, 4), return_counts=True)
print(f"level nilai unik (30 frame): {len(u)} · nilai tersering {u[c.argmax()]:.3f} m ({c.max() / c.sum() * 100:.0f}%)")
print("  -> bila level unik < 200 atau satu nilai > 15%: depth terkuantisasi, cek mode/filter driver")
PY
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
echo " - Float32MultiArray (driver Arducam): 43200 float = 180x240, meter, 0 = invalid. Ini yang dipakai sebagai TOPIC_DEPTH."
echo " - PointCloud2 driver Arducam = reproyeksi depth (intrinsik di config.sh), jadi REC_CLOUD=0 cukup."
echo " - Isi TOPIC_DEPTH, TOPIC_CLOUD, FPS_NOMINAL di config.sh."
