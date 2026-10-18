#!/usr/bin/env python3
"""QC isi 1 klip langsung setelah rekam (jalan di Pi; butuh ROS 2 Jazzy ter-source untuk rosbag2_py).

Pakai : python3 qc_clip.py <nama_klip> [--data-dir ~/tof_data] [--ref P1S1_REF] [--go 5.0]

Yang dicek (kriteria Skenario Bagian 3.1, ambang usulan):
  - fps dan jeda antar-frame terbesar
  - partisipan diam >= 3 dtk sebelum GO
  - aksi mulai <= 3 dtk setelah GO
  - durasi turun (10%->90% penurunan tinggi): cepat <= 1 dtk, pelan 1,5-3,5 dtk
  - piksel tubuh yang depth-nya invalid (indikasi IR terserap / observasi buruk)
  - tubuh menyentuh batas area valid (edge touch)

Latar diambil dari klip REF (median per-piksel, disimpan di <data-dir>/ref_cache/). Tanpa REF dipakai
persentil-85 klip itu sendiri, yang kurang akurat bila partisipan lama diam di satu tempat.
GO dibaca dari cue_log.csv (go_epoch - awal bag). Bila tidak ada, pakai --go atau PRE dari config.sh.
Hasil hanya saran: keputusan valid/tidak tetap dari pemeriksaan operator.
"""
import argparse
import csv
import os
import re
import sys
from pathlib import Path

import warnings

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

H, W = 180, 240
FX, FY, CX, CY = 190.92, 191.25, 120.0, 90.0
CODES = {  # kode: (detik aksi, kelas kecepatan atau None)
    "N1": (5, None), "N2": (5, None), "N3": (3, None), "N4": (1, "cepat"), "N5": (3, "pelan"),
    "N6": (1, "cepat"), "N7": (3, "pelan"), "N8a": (1, "cepat"), "N8b": (3, "pelan"),
    # set kedua (Skenario_Uji_HN_OL.md): HN tidak jatuh; OL*F jatuh cepat, OL*N duduk di lantai
    "HN1": (3, None), "HN2": (4, None), "HN3": (6, None), "HN4": (3, None), "HN5": (1, None),
    **{f"OL{i}F": (1, "cepat") for i in range(1, 5)}, **{f"OL{i}N": (4, None) for i in range(1, 5)},
}


def read_depth(bag, topic="/depth_frame"):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from std_msgs.msg import Float32MultiArray
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=str(bag), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
    r.set_filter(rosbag2_py.StorageFilter(topics=[topic]))
    ts, frames = [], []
    while r.has_next():
        _, data, t = r.read_next()
        ts.append(t)
        frames.append(np.asarray(deserialize_message(data, Float32MultiArray).data, np.float32).reshape(H, W))
    d = np.stack(frames)
    d[d <= 0] = np.nan
    return np.array(ts, np.int64), d


def floor_plane(bg, ok):
    vv, uu = np.mgrid[0:H, 0:W]
    z = np.nan_to_num(bg)
    P = np.stack([(uu - CX) * z / FX, (vv - CY) * z / FY, z], -1)[ok & np.isfinite(bg)]
    rng = np.random.default_rng(0)
    best = None
    for _ in range(1500):
        a, b, c = P[rng.choice(len(P), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-9:
            continue
        n /= np.linalg.norm(n)
        inl = np.abs(P @ n - n @ a) < 0.06
        if best is None or inl.sum() > best[1].sum():
            best = (n, inl)
    Q = P[best[1]]
    cen = Q.mean(0)
    n = np.linalg.svd(Q - cen, full_matrices=False)[2][2]
    d = n @ cen
    if d < 0:
        n, d = -n, -d
    return n, d


def go_from_cue(data_dir, name, t0_ns):
    f = Path(data_dir) / "cue_log.csv"
    if not f.exists():
        return None
    go = None
    for row in csv.reader(open(f)):
        if row and row[0] == name and len(row) >= 2:
            try:
                go = float(row[1]) - t0_ns / 1e9
            except ValueError:
                pass
    return go


def med(x, k=5):
    return np.array([np.nanmedian(x[max(0, i - k // 2):i + k // 2 + 1]) for i in range(len(x))])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--data-dir", default=os.environ.get("DATA_DIR", "~/tof_data"))
    ap.add_argument("--bags", help="folder bag (default <data-dir>/bags)")
    ap.add_argument("--ref", help="nama klip REF untuk latar (default: *REF* terbaru di folder bag)")
    ap.add_argument("--go", type=float, help="waktu GO (dtk dari awal bag), menimpa cue_log")
    ap.add_argument("--pre", type=float, default=float(os.environ.get("PRE", 5)))
    a = ap.parse_args()

    from scipy import ndimage as ndi

    data_dir = Path(a.data_dir).expanduser()
    bags = Path(a.bags).expanduser() if a.bags else data_dir / "bags"
    code = a.name.split("_")[-1]
    code = re.sub(r"_?(x\d+|RETRY\d+)$", "", code)
    m = re.search(r"_(N\d+[ab]?|HN\d|OL\d[FN])(?:_|$)", a.name)
    code = m.group(1) if m else code
    act, speed = CODES.get(code, (None, None))

    T, D = read_depth(bags / a.name)
    t = (T - T[0]) / 1e9
    dt = np.diff(t)
    print(f"Klip    : {a.name} ({code}) · {len(t)} frame · {t[-1]:.2f} dtk · {(len(t) - 1) / t[-1]:.1f} fps · jeda maks {dt.max() * 1000:.0f} ms")

    # latar
    refname = a.ref
    if not refname:
        refs = sorted((p for p in bags.iterdir() if p.is_dir() and "REF" in p.name), key=lambda p: p.stat().st_mtime)
        refname = refs[-1].name if refs else None
    if refname and refname != a.name:
        cache = data_dir / "ref_cache" / f"{Path(refname).name}_v4.npz"
        if cache.exists():
            z = np.load(cache)
            bg, vrate, bstd, nref = z["bg"], z["vrate"], z["bstd"], int(z["nref"])
        else:
            _, R = read_depth(bags / refname)
            bg, vrate, bstd, nref = np.nanmedian(R, 0), np.isfinite(R).mean(0), np.nanstd(R, 0), len(R)
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(cache, bg=bg, vrate=vrate, bstd=bstd, nref=nref)
        # Latar = median REF. Persentil yang lebih tinggi menggeser bidang lantai menjauh (~14 cm untuk noise
        # ±11 cm) sehingga semua tinggi ikut terbaca lebih tinggi. Mode tanpa REF di bawah punya bias itu.
        thr = 0.15
        print(f"Latar   : REF {refname} ({nref} frame, noise median {np.nanmedian(bstd[vrate > 0.3]) * 100:.0f} cm)")
        if nref < 150:
            print(f"          PERINGATAN REF hanya {nref} frame (< 5 dtk @30 Hz), latar dan noise kurang stabil")
    else:
        bg, vrate = np.nanpercentile(D, 85, 0), np.isfinite(D).mean(0)
        thr = 0.15
        print("Latar   : PERINGATAN tanpa REF, dipakai persentil-85 klip ini (kurang akurat)")
    ok = vrate > 0.3
    n, d = floor_plane(bg, ok)
    print(f"Kamera  : tinggi {d:.2f} m · pitch {np.degrees(np.arcsin(abs(n[2]))):.0f}° (fit bidang lantai)")

    vv, uu = np.mgrid[0:H, 0:W]
    edge_zone = ndi.binary_dilation(~ok | (uu < 2) | (uu > W - 3) | (vv < 2) | (vv > H - 3), iterations=2)
    top, cx, cy, dark, edge, npx = [], [], [], [], [], []
    for i in range(len(t)):
        z = D[i]
        near = ((bg - z) > thr) & ok
        inval = np.isnan(z) & (vrate > 0.8)
        f = ndi.binary_opening(near | inval, np.ones((3, 3)))
        lab, k = ndi.label(f)
        if k == 0:
            top.append(np.nan); cx.append(np.nan); cy.append(np.nan); dark.append(np.nan); edge.append(0); npx.append(0)
            continue
        sz = ndi.sum(f, lab, range(1, k + 1))
        mk = lab == (np.argmax(sz) + 1)
        npx.append(int(mk.sum()))
        valid = mk & np.isfinite(z)
        if mk.sum() < 150 or valid.sum() < 50:
            top.append(np.nan); cx.append(np.nan); cy.append(np.nan); dark.append(np.nan); edge.append(0)
            continue
        zz = z[valid]
        P = np.stack([(uu[valid] - CX) * zz / FX, (vv[valid] - CY) * zz / FY, zz], -1)
        h = d - P @ n
        top.append(np.percentile(h, 97))
        cx.append(P[:, 0].mean()); cy.append(P[:, 1].mean())
        dark.append((mk & inval).sum() / mk.sum())
        per = mk & ~ndi.binary_erosion(mk)
        edge.append((per & edge_zone).sum() / max(per.sum(), 1))
    top, cx, cy, dark, edge, npx = map(np.array, (med(np.array(top)), med(np.array(cx)), med(np.array(cy)), dark, edge, npx))
    w = 6
    v = np.full(len(t), np.nan)
    v[w:] = (top[w:] - top[:-w]) / (t[w:] - t[:-w])
    sp = np.full(len(t), np.nan)
    sp[w:] = np.hypot(cx[w:] - cx[:-w], cy[w:] - cy[:-w]) / (t[w:] - t[:-w])
    present = npx >= 150

    go = a.go if a.go is not None else go_from_cue(data_dir, a.name, T[0])
    src = "--go" if a.go is not None else ("cue_log" if go is not None else "PRE config")
    if go is None:
        go = a.pre
    flags = []
    print(f"GO      : {go:.2f} dtk ({src})")

    moving = (sp > 0.25) | (np.abs(v) > 0.3) | ~present
    pre_mv = np.where((t < go) & moving)[0]
    still = go - (t[pre_mv[-1]] if len(pre_mv) else 0.0)
    print(f"Diam    : {still:.1f} dtk sebelum GO -> {'OK' if still >= 3 else 'CEK (minimal 3 dtk)'}")
    if still < 3:
        flags.append("diam")

    win = (t > go - 1.5) & (t <= go) & present
    hs = np.nanmedian(top[win]) if win.sum() > 5 else np.nanmedian(top[(t < go) & present])
    hl = np.nanmedian(top[t > t[-1] - 1.5])
    if not np.isnan(hs):
        print(f"Tinggi  : {hs:.2f} m sebelum GO -> {hl:.2f} m di akhir")
    # Partisipan bisa bangun/keluar sebelum bag selesai (mis. P2_R1_N5_x1): tinggi akhir lalu tinggi lagi dan
    # jatuhnya tidak terhitung. Pakai posisi terendah setelah GO sebagai acuan bila jauh di bawah tinggi akhir.
    after = (t > go) & present
    lo = np.nanpercentile(top[after], 10) if after.sum() > 5 else np.nan
    rose = bool(speed) and not np.isnan(lo) and (np.isnan(hl) or hl - lo > 0.3)
    if rose:
        print(f"          posisi terendah {lo:.2f} m, lalu naik lagi ke {hl:.2f} m (bangun/keluar sebelum klip selesai)")
        hl = lo
        flags.append("bangun")
    drop = hs - hl
    if drop > 0.4:
        te = next((i for i in np.where((t > go - 0.5) & (top <= hl + 0.1 * drop))[0]
                   if np.all(top[i:i + 9] <= hl + 0.2 * drop)), None)
        if te is not None:
            before = np.where((t < t[te]) & (top >= hs - 0.1 * drop))[0]
            to = before[-1] if len(before) else 0
            desc, react = t[te] - t[to], t[to] - go
            print(f"Turun   : onset {t[to]:.2f} -> end {t[te]:.2f} dtk · durasi {desc:.2f} dtk · kec. maks {-np.nanmin(v[to:te + 7]):.2f} m/s")
            print(f"Reaksi  : aksi mulai {react:.1f} dtk setelah GO -> {'OK' if 0 <= react <= 3 else 'CEK (0-3 dtk)'}")
            if not 0 <= react <= 3:
                flags.append("reaksi")
            if speed == "cepat":
                good = desc <= 1.0
                print(f"Kecepatan: cepat (<= 1 dtk) -> {'OK' if good else 'CEK, terlalu lambat'}")
            elif speed == "pelan":
                good = 1.5 <= desc <= 3.5
                print(f"Kecepatan: pelan (1,5-3,5 dtk) -> {'OK' if good else ('CEK, terlalu cepat' if desc < 1.5 else 'CEK, terlalu lambat')}")
            else:
                good = True
            if not good:
                flags.append("kecepatan")
            up = np.where((t > t[te]) & (top > hl + 0.5 * drop))[0]
            post = (t[up[0]] if rose and len(up) else t[-1]) - t[te]
            print(f"Tahan   : {post:.1f} dtk di posisi akhir -> {'OK' if post >= 3 else 'CEK (minimal 3 dtk)'}")
            if post < 3:
                flags.append("tahan")
    elif speed:
        print("Turun   : CEK, tidak terdeteksi penurunan > 0,4 m padahal kode ini jatuh")
        flags.append("tidak_jatuh")

    act_win = (t >= go - 1) & present
    et = np.nanmax(edge[act_win]) if act_win.any() else 0
    dk = np.nanmedian(dark[present]) if present.any() else np.nan
    print(f"Tepi    : edge touch maks {et:.2f} -> {'OK' if et < 0.15 else 'CEK, tubuh menyentuh batas area valid'}")
    if np.isnan(dk):
        print("Invalid : tidak ada orang terdeteksi di klip ini -> CEK")
        flags.append("tanpa_orang")
    else:
        print(f"Invalid : {dk * 100:.0f}% piksel tubuh tanpa depth (median) -> {'OK' if dk < 0.2 else 'CATAT (IR terserap / pakaian gelap?)'}")
    if code.startswith("OL"):
        print("          (OL: tepi dan piksel invalid memang dibuat buruk, tidak dijadikan saran gagal)")
    elif et >= 0.15:
        flags.append("tepi")
    print(f"SARAN   : {'PASS' if not flags else 'CEK -> ' + ', '.join(flags)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
