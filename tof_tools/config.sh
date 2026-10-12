# config.sh - EDIT SEKALI setelah menjalankan ./check_topics.sh
# File ini di-"source" oleh semua skrip lain. Jangan dijalankan langsung.

export DATA_DIR="$HOME/tof_data"          # folder kerja: bags/, cue_log.csv, clip_log.csv
export TOPIC_DEPTH="/depth_frame"         # std_msgs/msg/Float32MultiArray, 180x240, meter, 0 = invalid (dikonfirmasi pilot P1_R1)
export TOPIC_CLOUD="/point_cloud"         # sensor_msgs/msg/PointCloud2, tidak terorganisir (height=1), frame "map"
export REC_CLOUD=0                        # 0 = hanya depth (cloud = reproyeksi depth, galat 0 mm, lihat INTRINSIK)
export REC_CLOUD_REF=1                    # 1 = klip *REF* tetap merekam cloud (cek ulang intrinsik per sesi)
export FPS_NOMINAL=30                     # terukur 30,0 Hz di pilot P1_R1

export INIT_MAX=10                        # batas tunggu (detik) sampai recorder benar-benar merekam
export PRE=5                              # detik partisipan diam sebelum GO, dihitung SETELAH recorder siap
export POST=5                             # detik diam setelah aksi selesai

# Intrinsik pinhole hasil fit depth <-> cloud (pilot P1_R1, galat 0 mm):
#   x = (u - CX) * z / FX ,  y = (v - CY) * z / FY ,  z = depth (m)
export FX=190.92 FY=191.25 CX=120.0 CY=90.0
