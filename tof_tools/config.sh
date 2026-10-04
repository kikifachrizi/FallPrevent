# config.sh - EDIT SEKALI setelah menjalankan ./check_topics.sh
# File ini di-"source" oleh semua skrip lain. Jangan dijalankan langsung.

export DATA_DIR="$HOME/tof_data"          # folder kerja: bags/, cue_log.csv, clip_log.csv
export TOPIC_DEPTH="/GANTI_topik_depth"   # topik sensor_msgs/msg/Image (depth)
export TOPIC_CLOUD="/GANTI_topik_cloud"   # topik sensor_msgs/msg/PointCloud2
export REC_CLOUD=1                        # 1 = rekam cloud juga, 0 = hanya depth image
export FPS_NOMINAL=30                     # isi dari hasil `ros2 topic hz` (angka riil, bukan spek)

export INIT=2                             # detik tunggu rosbag2 siap
export PRE=5                              # detik partisipan diam sebelum GO
export POST=5                             # detik diam setelah aksi selesai
