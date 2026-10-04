#!/usr/bin/env python3
"""Ekstraksi bag per-klip (MCAP ROS 2) -> dataset npy. Tidak perlu ROS aktif (jalan di PC maupun Pi).

Install : pip install mcap mcap-ros2-support numpy
Pakai   : python3 extract_clips.py --bags ~/tof_data/bags --out ~/dataset_tof_fall \
              --depth-topic /TOPIK_DEPTH [--cloud-topic /TOPIK_CLOUD --cloud-first 30]

Keluaran:
  <out>/clips/<nama>/depth.npy   (T,H,W) uint16, mm, 0 = invalid
  <out>/clips/<nama>/t.npy       (T,) int64, log time bag (ns)
  <out>/clips/<nama>/meta.json
  <out>/ref/<nama>_floor_ref.npy (H,W) uint16, median per-piksel (hanya untuk klip bernama *REF*)
  <out>/clips_index.csv          ringkasan: n_frames, durasi, fps_est (untuk mengisi clips.csv)
  (opsional) <out>/clips/<nama>/cloud_xyz_firstN.npy  (N,H,W,3) float32, hanya bila cloud terorganisir

Bag dengan akhiran _x1, _x2, ... (klip gagal) dilewati.
Asumsi unit: 16UC1 = mm, 32FC1 = meter (REP-118). VERIFIKASI dengan check_topics.sh.
"""
import argparse
import csv
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

PF_DTYPE = {1: "i1", 2: "u1", 3: "i2", 4: "u2", 5: "i4", 6: "u4", 7: "f4", 8: "f8"}


def iter_msgs(mcap_files, topic):
    for mf in mcap_files:
        with open(mf, "rb") as f:
            reader = make_reader(f, decoder_factories=[DecoderFactory()])
            for _, _, message, ros_msg in reader.iter_decoded_messages(topics=[topic]):
                yield message.log_time, ros_msg


def image_to_mm(msg):
    h, w, enc = int(msg.height), int(msg.width), msg.encoding
    buf = bytes(msg.data)
    end = ">" if msg.is_bigendian else "<"
    if enc == "16UC1":
        a = np.frombuffer(buf, dtype=end + "u2").reshape(h, int(msg.step) // 2)[:, :w]
        return a.astype(np.uint16)
    if enc == "32FC1":
        a = np.frombuffer(buf, dtype=end + "f4").reshape(h, int(msg.step) // 4)[:, :w]
        a = np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0) * 1000.0
        return np.clip(a, 0, 65535).astype(np.uint16)
    raise ValueError(f"encoding tidak didukung: {enc}")


def cloud_to_xyz(msg):
    h, w = int(msg.height), int(msg.width)
    if h <= 1:
        return None  # tidak terorganisir
    if int(msg.row_step) != w * int(msg.point_step):
        raise ValueError("row_step != width*point_step (ada padding); belum didukung")
    end = ">" if msg.is_bigendian else "<"
    names, formats, offsets = [], [], []
    for fld in msg.fields:
        if fld.name in ("x", "y", "z"):
            names.append(fld.name)
            formats.append(end + PF_DTYPE[int(fld.datatype)])
            offsets.append(int(fld.offset))
    if sorted(names) != ["x", "y", "z"]:
        raise ValueError(f"field x,y,z tidak lengkap: {names}")
    dt = np.dtype({"names": names, "formats": formats, "offsets": offsets,
                   "itemsize": int(msg.point_step)})
    arr = np.frombuffer(bytes(msg.data), dtype=dt, count=h * w).reshape(h, w)
    return np.stack([arr["x"], arr["y"], arr["z"]], axis=-1).astype(np.float32)


def process_bag(bag_dir, out, depth_topic, cloud_topic, cloud_first, index_rows):
    name = bag_dir.name
    mcaps = sorted(bag_dir.glob("*.mcap"))
    if not mcaps:
        print(f"[LEWATI] {name}: tidak ada .mcap")
        return
    ts, frames = [], []
    for t, msg in iter_msgs(mcaps, depth_topic):
        ts.append(t)
        frames.append(image_to_mm(msg))
        enc = msg.encoding
    if not frames:
        print(f"[PERINGATAN] {name}: tidak ada pesan di {depth_topic}")
        return
    depth = np.stack(frames)
    t = np.array(ts, dtype=np.int64)
    dur = (t[-1] - t[0]) / 1e9
    fps = (len(t) - 1) / dur if dur > 0 else float("nan")

    cdir = out / "clips" / name
    cdir.mkdir(parents=True, exist_ok=True)
    np.save(cdir / "depth.npy", depth)
    np.save(cdir / "t.npy", t)

    if cloud_topic and cloud_first > 0:
        xyz = []
        for _, msg in iter_msgs(mcaps, cloud_topic):
            c = cloud_to_xyz(msg)
            if c is None:
                print(f"[PERINGATAN] {name}: cloud tidak terorganisir (height=1), dilewati")
                break
            xyz.append(c)
            if len(xyz) >= cloud_first:
                break
        if xyz:
            np.save(cdir / f"cloud_xyz_first{len(xyz)}.npy", np.stack(xyz))

    if "REF" in name:
        d = depth.astype(np.float32)
        d[d == 0] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            ref = np.nan_to_num(np.nanmedian(d, axis=0), nan=0.0).astype(np.uint16)
        (out / "ref").mkdir(parents=True, exist_ok=True)
        np.save(out / "ref" / f"{name}_floor_ref.npy", ref)

    meta = {"clip_id": name, "n_frames": int(len(t)), "duration_s": round(dur, 3),
            "fps_est": round(fps, 2), "encoding": enc, "shape": list(depth.shape),
            "depth_topic": depth_topic, "cloud_topic": cloud_topic}
    (cdir / "meta.json").write_text(json.dumps(meta, indent=2))
    index_rows.append([name, len(t), round(dur, 3), round(fps, 2), enc, depth.shape[1], depth.shape[2]])
    print(f"[OK] {name}: {len(t)} frame, {dur:.2f}s, ~{fps:.1f} fps, {enc}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bags", required=True, help="folder berisi bag per-klip (DATA_DIR/bags)")
    ap.add_argument("--out", required=True, help="folder dataset keluaran")
    ap.add_argument("--depth-topic", required=True)
    ap.add_argument("--cloud-topic", default=None)
    ap.add_argument("--cloud-first", type=int, default=0, help="simpan N frame cloud pertama per klip (0 = tidak)")
    ap.add_argument("--only", nargs="*", help="proses hanya nama klip ini")
    a = ap.parse_args()

    bags, out = Path(a.bags).expanduser(), Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in sorted(p for p in bags.iterdir() if p.is_dir()):
        if re.search(r"_x\d+$", d.name):
            continue
        if a.only and d.name not in a.only:
            continue
        try:
            process_bag(d, out, a.depth_topic, a.cloud_topic, a.cloud_first, rows)
        except Exception as e:  # satu klip bermasalah tidak menghentikan yang lain
            print(f"[ERROR] {d.name}: {e}", file=sys.stderr)

    idx = out / "clips_index.csv"
    new = not idx.exists()
    with open(idx, "a", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["clip_id", "n_frames", "duration_s", "fps_est", "encoding", "height", "width"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
