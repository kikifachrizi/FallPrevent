#!/usr/bin/env python3
"""Kalibrasi kamera real-time dari /depth_frame: tinggi, pitch, roll, dan cakupan lantai.

Jalankan DI PI (bukan lewat Wi-Fi) saat driver hidup dan ruangan kosong:
  python3 calib_live.py                          # tampil tiap ~1 dtk
  python3 calib_live.py --target-h 2.5 --target-pitch 70
  python3 calib_live.py --bag ~/tof_data/bags/S20261012_REF    # sekali hitung dari bag (cek offline)

Cara kerja: median per piksel dari N frame terakhir (meredam noise ±11 cm), fit bidang lantai (RANSAC + SVD,
sama dengan qc_clip.py), lalu:
  tinggi = jarak kamera ke bidang lantai
  pitch  = sudut sumbu optik di bawah horizontal (90° = lurus ke bawah), definisi sama dengan sessions.csv
  roll   = kemiringan ke samping (0° = datar); tidak stabil bila pitch > ~80°
  tengah = titik lantai yang dilihat pusat gambar, diukur dari titik lantai tepat di bawah kamera
  cakupan = rentang lantai yang valid (persentil 5-95), maju x lebar
Subscriber memakai QoS best effort supaya tidak memperlambat publisher.

Angka per pembacaan bergoyang walau kamera diam: noise depth ±11 cm dan piksel pinggir elips yang kadang valid
kadang tidak membuat bidang lantai sedikit berbeda tiap kali (uji di bag 12 Okt: tinggi ±2 cm, pitch ±1°,
roll ±4°). Karena itu yang dipakai untuk menyetel adalah baris "Rata-rata", bukan satu pembacaan.
"""
import argparse
import sys
import time
from collections import deque

import numpy as np

H, W = 180, 240
FX, FY, CX, CY = 190.92, 191.25, 120.0, 90.0
VV, UU = np.mgrid[0:H, 0:W]


def fit_floor(P, iters=400, tol=0.06, seed=0):
    rng = np.random.default_rng(seed)
    best_n, best_inl = None, None
    for _ in range(iters):
        a, b, c = P[rng.choice(len(P), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-9:
            continue
        n /= np.linalg.norm(n)
        inl = np.abs(P @ n - n @ a) < tol
        if best_inl is None or inl.sum() > best_inl.sum():
            best_n, best_inl = n, inl
    Q = P[best_inl]
    cen = Q.mean(0)
    n = np.linalg.svd(Q - cen, full_matrices=False)[2][2]
    d = n @ cen
    if d < 0:
        n, d = -n, -d
    return n, d, best_inl


def measure(frames):
    D = np.stack(frames).astype(np.float32)
    D[D <= 0] = np.nan
    vrate = np.isfinite(D).mean(0)
    bg = np.nanmedian(D, 0) if len(D) > 1 else D[0]
    ok = (vrate > 0.3) & np.isfinite(bg)
    if ok.sum() < 500:
        return None
    z = bg[ok]
    P = np.stack([(UU[ok] - CX) * z / FX, (VV[ok] - CY) * z / FY, z], -1)
    n, d, inl = fit_floor(P)
    pitch = np.degrees(np.arcsin(min(abs(n[2]), 1.0)))
    roll = np.degrees(np.arctan2(n[0], n[1]))  # n = arah "bawah dunia" di frame kamera (x kanan, y bawah, z maju)
    # sumbu lantai: maju = sumbu optik diproyeksikan ke lantai, samping = tegak lurus
    fwd = np.array([0.0, 0.0, 1.0]) - n[2] * n
    fwd /= np.linalg.norm(fwd)
    side = np.cross(n, fwd)
    Q = P[inl] - d * n
    f, s = Q @ fwd, Q @ side
    center_fwd = d / np.tan(np.radians(pitch)) if pitch < 89.5 else 0.0
    vc = np.argwhere(vrate > 0.3).mean(0)  # pusat area valid (baris, kolom)
    return dict(
        n=len(D), h=d, pitch=pitch, roll=roll, inlier=inl.mean(), valid=np.isfinite(D[-1]).mean(),
        center_fwd=center_fwd, f5=np.percentile(f, 5), f95=np.percentile(f, 95),
        s5=np.percentile(s, 5), s95=np.percentile(s, 95),
        off_u=vc[1] - CX, off_v=vc[0] - CY, noise=np.nanmedian(np.nanstd(D, 0)[ok]) if len(D) > 1 else np.nan,
    )


def report(m, a, hist=None):
    if m is None:
        return "Piksel valid terlalu sedikit untuk fit lantai (ruangan kosong? sensor tertutup?)"
    L = []
    if hist and len(hist) > 1:
        h, p, r = (np.array([x[k] for x in hist]) for k in ("h", "pitch", "roll"))
        L.append(f"Rata-rata {len(hist)} pembacaan: tinggi {h.mean():.2f} ± {h.std() * 100:.1f} cm · "
                 f"pitch {p.mean():.1f} ± {p.std():.1f}° · roll {r.mean():+.1f} ± {r.std():.1f}°   <- pakai ini")
        L.append("Pembacaan terakhir:")
    if m["inlier"] < 0.35:
        L.append("PERINGATAN: inlier lantai < 35%, ada orang/benda besar di frame? Kosongkan area.")
    L += [
        f"Frame   : median {m['n']} frame · valid {m['valid'] * 100:.0f}% · inlier lantai {m['inlier'] * 100:.0f}%"
        + (f" · noise {m['noise'] * 100:.0f} cm" if np.isfinite(m["noise"]) else ""),
        f"Tinggi  : {m['h']:.2f} m" + (f"   (target {a.target_h:.2f}, selisih {m['h'] - a.target_h:+.2f})" if a.target_h else ""),
        f"Pitch   : {m['pitch']:.1f}°" + (f"  (target {a.target_pitch:.0f}°, selisih {m['pitch'] - a.target_pitch:+.1f}°)" if a.target_pitch else "")
        + "   90° = lurus ke bawah",
        f"Roll    : {m['roll']:+.1f}°" + ("   (kurang bermakna, pitch > 80°)" if m["pitch"] > 80 else "   0° = datar"),
        f"Tengah  : pusat gambar jatuh {m['center_fwd']:.2f} m di depan titik bawah kamera  -> taruh pusat matras di sini",
        f"Cakupan : lantai valid maju {m['f5']:.2f}–{m['f95']:.2f} m, lebar {m['s5']:+.2f}…{m['s95']:+.2f} m"
        f" ({m['f95'] - m['f5']:.1f} x {m['s95'] - m['s5']:.1f} m)",
        f"Elips   : pusat area valid bergeser {m['off_u']:+.0f} px kolom, {m['off_v']:+.0f} px baris dari pusat gambar",
    ]
    if a.target_pitch:
        dp = (np.mean([x["pitch"] for x in hist]) if hist and len(hist) > 1 else m["pitch"]) - a.target_pitch
        if abs(dp) > 2:
            L.append(f"SARAN   : {'kurangi' if dp > 0 else 'tambah'} kemiringan ke bawah ±{abs(dp):.0f}°")
        else:
            L.append("SARAN   : pitch sudah dalam ±2° dari target")
    return "\n".join(L)


def run_bag(a):
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from qc_clip import read_depth
    _, D = read_depth(a.bag, a.topic)
    frames = [np.nan_to_num(f) for f in D]
    print(report(measure(frames), a))


def run_live(a):
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from std_msgs.msg import Float32MultiArray

    buf = deque(maxlen=a.frames)
    hist = deque(maxlen=a.avg)
    rclpy.init()
    node = Node("calib_live")
    node.create_subscription(
        Float32MultiArray, a.topic,
        lambda msg: buf.append(np.asarray(msg.data, np.float32).reshape(H, W)), qos_profile_sensor_data)
    print(f"Menunggu {a.topic} ... (Ctrl+C untuk berhenti)")
    t_last, n_seen = time.time(), 0
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
            if time.time() - t_last < a.every or len(buf) < min(5, a.frames):
                continue
            dt = time.time() - t_last
            t_last = time.time()
            hz = (len(buf) - n_seen) / dt if len(buf) < a.frames else float("nan")
            n_seen = len(buf)
            print("\033[2J\033[H" if not a.no_clear else "", end="")
            print(time.strftime("%H:%M:%S"), f"· {a.topic}" + (f" · {hz:.0f} Hz" if np.isfinite(hz) else ""))
            m = measure(list(buf))
            if m is not None and len(buf) == a.frames:
                hist.append(m)
            print(report(m, a, hist), flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--topic", default="/depth_frame")
    ap.add_argument("--frames", type=int, default=60, help="jumlah frame untuk median (default 60 = 2 dtk @30 Hz)")
    ap.add_argument("--avg", type=int, default=10, help="jumlah pembacaan terakhir yang dirata-rata (default 10)")
    ap.add_argument("--every", type=float, default=1.0, help="interval tampil (dtk)")
    ap.add_argument("--target-h", type=float, default=None, help="tinggi target (m)")
    ap.add_argument("--target-pitch", type=float, default=None, help="pitch target (derajat)")
    ap.add_argument("--bag", default=None, help="hitung sekali dari bag, bukan live")
    ap.add_argument("--no-clear", action="store_true", help="jangan bersihkan layar tiap update")
    a = ap.parse_args()
    run_bag(a) if a.bag else run_live(a)
