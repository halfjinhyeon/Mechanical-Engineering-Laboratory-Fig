"""고체 Module#1 pre-lab 그림.

  hypothetical_materials.png   Al 2024-T4와 가상 재료 A, B의 공칭 응력-변형률 곡선
  monel_work_history.png       가공 이력에 따른 Monel 400의 공칭 응력-변형률 곡선

곡선은 조에서 만든 인장시험 시뮬레이터의 금속 모델로 계산한다.
  균일 변형 구간: Ramberg-Osgood 진응력 곡선을 공칭값으로 변환. 지수 n은 최대 공칭응력이 인장강도와 같아지도록 맞춘다.
  네킹 구간: 인장강도에서 파단 연신율까지 포물선으로 내려가고, 파단 시 공칭응력은 인장강도의 0.8배로 가정한다.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import labfig as lf

OUT = HERE / "figures"
RF = 0.8                                           # 파단 공칭응력 / 인장강도 (가정)
lf.use()

# E (GPa), 항복강도와 인장강도 (MPa), 파단 연신율
MATERIALS = {
    "al": dict(name="Al 2024-T4", E=73, sy=325, su=470, ef=0.19),
    "hypA": dict(name="Hypothetical A", E=109.5, sy=422.5, su=470, ef=0.19),
    "hypB": dict(name="Hypothetical B", E=109.5, sy=422.5, su=611, ef=0.19),
    "monelC": dict(name="Monel 400 (cold-worked)", E=180, sy=585, su=675, ef=0.22),
    "monelA": dict(name="Monel 400 (annealed)", E=180, sy=220, su=550, ef=0.46),
}


def ro_points(m, n, e_end):
    """Ramberg-Osgood 진응력 곡선을 공칭 (변형률, 응력)으로 바꾼 점들. e_end에서 자른다."""
    E, sy = m["E"] * 1e3, m["sy"]
    st = 0.9 * sy * np.arange(81) / 80                              # 0.9 sy까지는 응력을 등간격으로
    ep = 0.002 * (st / sy) ** (1 / n)
    ep0, ep_max = 0.002 * 0.9 ** (1 / n), np.log1p(e_end) + 0.05
    if ep_max > ep0:                                                # 그 뒤는 소성 변형률을 로그 간격으로
        ep2 = ep0 * (ep_max / ep0) ** (np.arange(1, 501) / 500)
        st, ep = np.concatenate([st, sy * (ep2 / 0.002) ** n]), np.concatenate([ep, ep2])
    et = st / E + ep
    e, s = np.expm1(et), st * np.exp(-et)
    if e[-1] > e_end:
        k = int(np.argmax(e > e_end))
        s_end = np.interp(e_end, e[k - 1:k + 1], s[k - 1:k + 1])
        e, s = np.append(e[:k], e_end), np.append(s[:k], s_end)
    return e, s


def calibrate(m):
    """최대 공칭응력이 인장강도가 되는 n과 그때의 균일 연신율 eu."""
    peak = lambda n: ro_points(m, n, m["ef"])[1].max()
    lo, hi = 0.002, 0.8
    if peak(hi) < m["su"]:
        n = hi
    elif peak(lo) > m["su"]:
        n = lo
    else:
        for _ in range(50):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if peak(mid) < m["su"] else (lo, mid)
        n = (lo + hi) / 2
    e, s = ro_points(m, n, 3.0)
    return n, e[int(np.argmax(s))]


def curve(m):
    """공칭 응력-변형률 곡선과 특성값."""
    n, eu = calibrate(m)
    e, s = ro_points(m, n, eu)
    s_u = s[-1]
    ez = eu + (m["ef"] - eu) / np.sqrt(1 - RF)
    en = np.linspace(eu, m["ef"], 221)[1:]
    e = np.concatenate([e, en])
    s = np.concatenate([s, s_u * (1 - ((en - eu) / (ez - eu)) ** 2)])
    # 0.2 % offset 항복점: 곡선과 직선 E(e - 0.002)의 교점
    E = m["E"] * 1e3
    d = s - E * (e - 0.002)
    k = int(np.argmax(d < 0))
    t = d[k - 1] / (d[k - 1] - d[k])
    ey, sy = e[k - 1] + t * (e[k] - e[k - 1]), s[k - 1] + t * (s[k] - s[k - 1])
    return dict(e=e, s=s, n=n, eu=eu, su=s_u, ey=ey, sy=sy, ef=e[-1], sf=s[-1], E=E)


CURVES = {key: curve(m) for key, m in MATERIALS.items()}
for key, c in CURVES.items():
    print(f"  {MATERIALS[key]['name']:24s} n = {c['n']:.3f}, eu = {c['eu']:.3f}, sY(0.2 %) = {c['sy']:.0f} MPa, "
          f"sU = {c['su']:.0f} MPa, sf = {c['sf']:.0f} MPa")
SIGMA = r"$\sigma$ (MPa)"
EPS = r"$\varepsilon$ (mm/mm)"


# ---------------------------------------------------------------- hypothetical_materials
def hypothetical_materials():
    keys = ("al", "hypA", "hypB")
    fig, (axa, axb) = lf.figure("wide", 2.5, ncols=2)

    # (a) 전체 곡선
    for i, key in enumerate(keys):
        c, m = CURVES[key], MATERIALS[key]
        tag = "" if key == "al" else rf" ($\sigma_U$ = {m['su']:.0f} MPa)"
        lf.trace(axa, c["e"], c["s"], series=i, label=m["name"] + tag)
        lf.mark(axa, c["eu"], c["su"], series=i)
        lf.mark(axa, c["ef"], c["sf"], series=i, cross=True)
    lf.note(axa, rf"$\varepsilon_u$ = {CURVES['hypB']['eu']:.3f}", (CURVES["hypB"]["eu"], CURVES["hypB"]["su"] + 38), ha="center")
    lf.note(axa, rf"$\varepsilon_u$ = {CURVES['hypA']['eu']:.3f}", (CURVES["hypA"]["eu"], CURVES["hypA"]["su"]), (0.022, 245))
    lf.note(axa, rf"$\varepsilon_u$ = {CURVES['al']['eu']:.3f}", (CURVES["al"]["eu"], CURVES["al"]["su"]), (0.098, 315))
    axa.set_xlim(0, 0.2)
    axa.set_ylim(0, 720)
    lf.plain_ticks(axa.xaxis, 2)
    axa.set_xticks([0, 0.05, 0.1, 0.15, 0.2])
    axa.set_xlabel(EPS)
    axa.set_ylabel(SIGMA)
    lf.panel(axa, "(a) Engineering stress–strain")
    lf.legend(axa, loc="lower right", fontsize=7.5, handlelength=2.6)

    # (b) 탄성과 항복 구간 확대: A와 B는 E와 항복응력이 같아 이 구간에서 겹친다
    for i, key in enumerate(keys):
        c = CURVES[key]
        lf.trace(axb, c["e"], c["s"], series=i)
    for i, key in ((0, "al"), (1, "hypA")):
        c = CURVES[key]
        xo = np.array([0.002, 0.002 + 1.12 * c["sy"] / c["E"]])
        lf.model(axb, xo, c["E"] * (xo - 0.002), series=i, lw=0.8)
        lf.mark(axb, c["ey"], c["sy"], series=i)
    al, hy = CURVES["al"], CURVES["hypA"]
    lf.note(axb, rf"$\sigma_Y$ = {hy['sy']:.0f} MPa (A, B)", (hy["ey"], hy["sy"]), (0.0006, 515))
    lf.note(axb, rf"$\sigma_Y$ = {al['sy']:.0f} MPa", (al["ey"], al["sy"]), (0.0078, 255))
    lf.note(axb, rf"$E$ = {hy['E'] / 1e3:.1f} GPa", (200 / hy["E"], 200), (0.0003, 430), fontsize=7.5)
    lf.note(axb, rf"$E$ = {al['E'] / 1e3:.0f} GPa", (130 / al["E"], 130), (0.0042, 60), fontsize=7.5)
    lf.note(axb, "0.2% offset", (0.0032, 20), fontsize=7.5)
    axb.set_xlim(0, 0.012)
    axb.set_ylim(0, 560)
    axb.set_xticks([0, 0.004, 0.008, 0.012])
    lf.plain_ticks(axb.xaxis, 3)
    axb.set_xlabel(EPS)
    lf.panel(axb, "(b) Elastic and yield region")
    lf.save(fig, OUT / "hypothetical_materials.png")


# ---------------------------------------------------------------- monel_work_history
def monel_work_history():
    cw, an = CURVES["monelC"], CURVES["monelA"]
    fig, ax = lf.figure("single", 2.6)
    # 구간은 풀림 재료 기준
    lf.region(ax, an["ey"], an["eu"], "Strain hardening", alpha=0.10)
    lf.region(ax, an["eu"], an["ef"], "Necking", alpha=0.26)

    for i, (c, key) in enumerate(((cw, "monelC"), (an, "monelA"))):
        lf.trace(ax, c["e"], c["s"], series=i, label=MATERIALS[key]["name"] + (", shaded regions" if key == "monelA" else ""))
        lf.mark(ax, c["eu"], c["su"], series=i)
        lf.mark(ax, c["ef"], c["sf"], series=i, cross=True)
    lf.note(ax, rf"$\sigma_Y$ = {cw['sy']:.0f} MPa" + "\n" + rf"$\varepsilon_f$ = {cw['ef']:.2f}", (cw["ef"], cw["sf"]), (0.255, 705))
    lf.note(ax, rf"$\sigma_Y$ = {an['sy']:.0f} MPa" + "\n" + rf"$\varepsilon_f$ = {an['ef']:.2f}", (an["ef"], an["sf"]), (0.39, 300), ha="center")
    ax.set_xlim(0, 0.5)
    ax.set_ylim(0, 900)
    lf.plain_ticks(ax.xaxis, 1)
    ax.set_xlabel(EPS)
    ax.set_ylabel(SIGMA)
    lf.legend(ax, loc="lower center", fontsize=7.5)
    lf.save(fig, OUT / "monel_work_history.png")


hypothetical_materials()
monel_work_history()
