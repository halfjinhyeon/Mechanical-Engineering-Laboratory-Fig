"""고체 Module#1 post-lab 그림 (황동 시편 인장시험).

  stress_strain.png        측정 곡선 (크로스헤드 기준)과 보정한 공칭 응력-변형률 곡선
  modulus_yield.png        신율계 선형 회귀로 구한 탄성계수와 0.2 % offset 항복응력
  caliper_photos.png       파단 후 캘리퍼 측정 사진
  true_stress_strain.png   공칭 응력-변형률과 진응력-진변형률
  fracture.png             파단 시편 사진과 파단 전후 하중 기록

데이터는 data/tensile_brass.csv, 계산은 tensile.py와 q3.py가 맡는다.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import labfig as lf
import q3
import tensile as T

OUT = HERE / "figures"
PHOTO = HERE / "data"
lf.use()

d = T.load()
r = T.analyze(d, T.extensometer_modulus(d))
q = q3.compute()
F = d["F"]
sig, er, ec = r["sig"], r["eps_raw"], r["eps_c"]
ipl, iy, iu, ifr = r["ipl"], r["iy"], r["iu"], r["ifr"]
# 보정한 공칭 곡선: 비례한도까지는 원점에서 E 기울기 직선, 그 위는 측정값
xc = np.concatenate([[0.0], ec[ipl:ifr + 1]])
yc = np.concatenate([[0.0], sig[ipl:ifr + 1]])
SIGMA = r"$\sigma = P/A_0$ (MPa)"


# ---------------------------------------------------------------- stress_strain
def stress_strain():
    fig, (axa, axb) = lf.figure("wide", 2.5, ncols=2)

    # (a) 측정 곡선: 크로스헤드 변위 / L0
    lf.trace(axa, er[:ifr + 1], sig[:ifr + 1], color=lf.INK, lw=1.2)
    lf.mark(axa, er[iu], r["sigU"])
    lf.mark(axa, er[ifr], r["sigF"], cross=True)
    E_app = r["k"] * T.L0 / T.A0
    ys = np.array([0.0, 380.0])
    lf.model(axa, (r["s0"] + ys * T.A0 / r["k"]) / T.L0, ys, color=lf.GRAY)
    lf.note(axa, "Grip seating\n" + rf"$\delta_0$ = {r['s0']:.2f} mm", (r["s0"] / T.L0, 0), (0.085, 62))
    lf.note(axa, f"Apparent slope\n= {E_app / 1e3:.1f} GPa", (0.092, 245))
    lf.note(axa, rf"$\sigma_U$ = {r['sigU']:.0f} MPa", (er[iu] - 0.01, 512), ha="center")
    lf.note(axa, rf"$\sigma_f$ = {r['sigF']:.0f} MPa" + "\n" + rf"$\varepsilon_f$ = {er[ifr]:.3f}",
            (er[ifr], r["sigF"]), (er[ifr] - 0.035, 330), ha="right")
    axa.set_xlabel(r"$\varepsilon = \delta/L_0$ (mm/mm)")
    lf.panel(axa, "(a) Measured (crosshead)")

    # (b) 공칭 곡선: toe와 장비 컴플라이언스 보정
    lf.trace(axb, xc, yc, series=0)
    lf.mark(axb, ec[iy], r["sigY"], series=0)
    lf.mark(axb, ec[iu], r["sigU"], series=0)
    lf.mark(axb, ec[ifr], r["sigF"], series=0, cross=True)
    lf.note(axb, rf"$\sigma_U$ = {r['sigU']:.0f} MPa", (ec[iu], 512), ha="center")
    lf.note(axb, rf"$\sigma_f$ = {r['sigF']:.0f} MPa, $\varepsilon_f$ = {ec[ifr]:.3f}",
            (ec[ifr], r["sigF"]), (0.305, 352), ha="right")

    # 항복 부근 확대: 전체 축에서는 탄성과 항복이 변형률 0.006 안에 몰려 보이지 않는다
    axi = axb.inset_axes([0.34, 0.20, 0.60, 0.33])
    lf.region(axi, ec[ipl], ec[iy])
    lf.trace(axi, xc, yc, series=0, lw=1.2)
    xo = np.array([0.002, 0.002 + 430 / r["E"]])
    lf.model(axi, xo, r["E"] * (xo - 0.002), color=lf.GRAY, lw=0.8)
    lf.mark(axi, ec[iy], r["sigY"], series=0, ms=4.2)
    lf.note(axi, rf"$\sigma_Y$ = {r['sigY']:.0f} MPa" + "\n(0.2% offset)", (ec[iy], r["sigY"]),
            (0.0082, 235), fontsize=7.5)
    lf.note(axi, rf"$E$ = {r['E'] / 1e3:.0f} GPa", (110 / r["E"], 110), (0.0082, 55), fontsize=7.5)
    axi.set_xlim(0, 0.015)
    axi.set_ylim(0, 450)
    axi.set_xticks([0, 0.005, 0.01, 0.015])
    axi.set_yticks([0, 200, 400])
    lf.plain_ticks(axi.xaxis, 3)
    axi.tick_params(labelsize=7, length=2.5)
    axi.set_title(r"Zoom: $\varepsilon \leq$ 0.015", fontsize=7.5, loc="left", pad=2)

    elf = (T.LF - T.L0) / T.L0                         # 실측 연신율: x축 위 삼각형
    axb.plot(elf, 0, "^", ms=5.5, color=lf.INK, clip_on=False, zorder=5)
    lf.note(axb, r"Measured $(L_f-L_0)/L_0$" + f" = {elf:.3f}", (0.305, 34), ha="right", fontsize=7.5)
    axb.set_xlabel(r"$\varepsilon$ (mm/mm)")
    lf.panel(axb, "(b) Engineering (corrected)")

    for ax in (axa, axb):
        ax.set_xlim(0, 0.32)
        ax.set_ylim(0, 540)
        ax.set_xticks(np.arange(0, 0.31, 0.1))
        lf.plain_ticks(ax.xaxis, 1)
        ax.set_ylabel(SIGMA)
    lf.save(fig, OUT / "stress_strain.png")


# ---------------------------------------------------------------- modulus_yield
def modulus_yield():
    n = int(np.sum(~np.isnan(d["ext"])))
    ipk = int(np.argmax(F[:n]))
    ee = d["ext"][:n] / T.L0 * 1e4                     # x축: 10^-4 단위
    ss = F[:n] / T.A0
    use = np.zeros(n, bool)
    use[:ipk] = (ss[:ipk] > 5) & (ss[:ipk] < 25)

    fig, (axa, axb) = lf.figure("wide", 2.4, ncols=2)

    # (a) 신율계 회귀
    lf.points(axa, ee[~use], ss[~use], label="Measured", mec=lf.GRAY, mfc=lf.GRAY, ms=1.8, mew=0)
    lf.points(axa, ee[use], ss[use], series=0, label="Fitting range", ms=1.8, mew=0, filled=True)
    fit = lf.linfit(axa, ee[use], ss[use], span=(0, 2.5), label="Linear fit")
    E = fit.slope * 1e4
    lf.note(axa, rf"$E$ = {E / 1e3:.1f} GPa" + "\n" + rf"($R^2$ = {fit.r2:.3f})", (0.12, 25.5))
    axa.set_xlim(0, 2.6)
    axa.set_ylim(0, 30)
    lf.plain_ticks(axa.xaxis, 1)
    axa.set_xlabel(r"$\varepsilon$ (extensometer, $10^{-4}$ mm/mm)")
    axa.set_ylabel(SIGMA)
    lf.panel(axa, "(a) Elastic modulus (5–25 MPa fit)")
    lf.legend(axa, loc="lower right", handlelength=1.6)

    # (b) 보정 곡선의 0.2 % offset
    Er = r["E"]
    sp = (T.smooth(F) / T.A0)[ipl]
    lf.region(axb, ec[ipl], ec[iy], "Yielding", y=0.04, va="bottom", rotation=90)
    lf.trace(axb, xc, yc, series=0)
    xo = np.array([0.002, 0.002 + 450 / Er])
    lf.model(axb, xo, Er * (xo - 0.002), color=lf.GRAY, lw=0.8)
    lf.note(axb, "0.2% offset", (0.0064, 40), color=lf.GRAY)
    lf.mark(axb, ec[ipl], sp, mfc=lf.GRAY, mec=lf.GRAY, ms=4)
    lf.mark(axb, ec[iy], r["sigY"], series=0)
    # 두 지시선이 서로나 글자와 겹치지 않게 항복점 주석을 위, 비례한도 주석을 아래에 둔다
    lf.note(axb, rf"$\sigma_Y$ = {r['sigY']:.0f} MPa" + "\n" + rf"($\varepsilon$ = {ec[iy]:.3f})",
            (ec[iy], r["sigY"]), (0.0092, 300))
    lf.note(axb, rf"$\sigma_{{pl}}$ ≈ {sp:.0f} MPa", (ec[ipl], sp), (0.0084, 165))
    lf.note(axb, rf"$E$ = {Er / 1e3:.0f} GPa", (250 / Er, 250), (0.0002, 455),
            arrowprops=dict(lf.LEAD, relpos=(0.3, 0.0)))
    axb.set_xlim(0, 0.015)
    axb.set_ylim(0, 500)
    axb.set_xticks([0, 0.005, 0.01, 0.015])
    lf.plain_ticks(axb.xaxis, 3)
    axb.set_xlabel(r"$\varepsilon$ (corrected, mm/mm)")
    axb.set_ylabel(SIGMA)
    lf.panel(axb, "(b) 0.2% offset yield strength")
    lf.save(fig, OUT / "modulus_yield.png")
    print(f"  E {E:.0f} MPa, R2 {fit.r2:.4f}, sig_pl {sp:.1f}, sigY {r['sigY']:.1f}")


# ---------------------------------------------------------------- caliper_photos
def caliper_photos():
    fig = lf.photos(
        [PHOTO / "caliper_diameter.jpg", PHOTO / "caliper_gauge_length.jpg"],
        [rf"(a) Diameter, $d_f$ = {T.DF} mm", rf"(b) Gauge length, $L_f$ = {T.LF} mm"],
        width=4.6, height=1.7, crops=[(0.0, 0.29, 1.0, 0.77), None])
    lf.save(fig, OUT / "caliper_photos.png", dpi=300)


# ---------------------------------------------------------------- true_stress_strain
def true_stress_strain():
    eY, eU, eF = q["epsY"], q["epsU"], q["epsF"]
    fig, ax = lf.figure("single", 2.4)
    lf.region(ax, eY, eU, "Strain hardening", alpha=0.10)
    lf.region(ax, eU, eF, "Necking", alpha=0.26, rotation=90)

    lf.trace(ax, xc, yc, series=0, label="Engineering")
    lf.trace(ax, np.concatenate([[0.0], q["eT"]]), np.concatenate([[0.0], q["sT"]]), series=1, label="True")
    lf.model(ax, [q["epsU_T"], q["epsF_T"]], [q["sigU_T"], q["sigF_T"]], series=1, ls=(0, (1.2, 1.6)),
             label="True (necking: U, F only)")
    lf.mark(ax, eU, q["sigU"], series=0)
    lf.mark(ax, eF, q["sigF"], series=0, cross=True)
    lf.mark(ax, q["epsU_T"], q["sigU_T"], series=1)
    lf.mark(ax, q["epsF_T"], q["sigF_T"], series=1, cross=True)

    lf.note(ax, rf"$\sigma_U$ = {q['sigU']:.0f}", (eU, q["sigU"]), (0.150, 385), ha="center")
    lf.note(ax, rf"$\sigma_f$ = {q['sigF']:.0f}" + "\n" + rf"$\varepsilon_f$ = {eF:.3f}",
            (eF, q["sigF"]), (0.265, 350), ha="left")
    lf.note(ax, rf"$\sigma_{{T,U}}$ = {q['sigU_T']:.0f}", (q["epsU_T"], q["sigU_T"]), (0.075, 640), ha="center")
    lf.note(ax, rf"$\sigma_{{T,f}}$ = {q['sigF_T']:.0f} MPa" + "\n"
            + rf"$\varepsilon_{{T,f}}$ = ln($A_0/A_f$) = {q['epsF_T']:.2f}",
            (q["epsF_T"], q["sigF_T"]), (0.535, 590), ha="right")
    ax.set_xlim(0, 0.55)
    ax.set_ylim(0, 780)
    ax.set_xticks(np.arange(0, 0.551, 0.1))
    lf.plain_ticks(ax.xaxis, 1)
    ax.set_xlabel(r"$\varepsilon$, $\varepsilon_T$ (mm/mm)")
    ax.set_ylabel(r"$\sigma$, $\sigma_T$ (MPa)")
    lf.legend(ax, loc="lower right")
    lf.save(fig, OUT / "true_stress_strain.png")


# ---------------------------------------------------------------- fracture
def fracture():
    def crop(name, box_thumb, thumb_w):
        """썸네일(가로 thumb_w px) 좌표로 정한 상자를 사진 해상도에 맞춰 잘라 낸다."""
        im = lf.load_photo(PHOTO / name)
        sc = im.size[0] / thumb_w
        return im.crop(tuple(int(v * sc) for v in box_thumb))

    img_a = crop("fracture_surface.jpg", (178, 412, 392, 640), 562)
    img_b = crop("caliper_gauge_length.jpg", (430, 112, 615, 222), 1000).rotate(90, expand=True)
    t = d["t"]

    fig, (axa, axb, axc) = lf.figure(4.6, 1.7, ncols=3, width_ratios=[
        img_a.size[0] / img_a.size[1], img_b.size[0] / img_b.size[1], 1.25])
    lf.photo(axa, img_a, "(a) Fracture surface")
    lf.photo(axb, img_b, "(b) Neck")
    wa, ha = img_a.size
    lf.note(axa, "Dull, fibrous\nsurface", (0.36 * wa, 0.13 * ha), (0.47 * wa, 0.10 * ha), fontsize=7)

    m = (t >= t[ifr] - 0.10) & (t <= t[ifr] + 0.10)
    lf.trace(axc, (t[m] - t[ifr]) * 1e3, F[m] / 1e3, series=0, lw=1.1, marker="o", ms=2.4)
    for k, dy in enumerate((0.6, 0.0, 2.6)):
        i = ifr + 1 + k
        x, y = (t[i] - t[ifr]) * 1e3, F[i] / 1e3
        lf.note(axc, f"{y:.1f} kN", (x, y), (x + 9, y + dy), ha="left", fontsize=8)
    lf.note(axc, rf"$P_f$ = {F[ifr] / 1e3:.1f} kN", (-94, 17.0), fontsize=8)
    lf.note(axc, "100 Hz sampling\n(10 ms per point)", (-94, 10.5), fontsize=7.5)
    axc.set_xlim(-100, 100)
    axc.set_ylim(0, 25)
    axc.set_xlabel(r"$t - t_f$ (ms)")
    axc.set_ylabel(r"Load $P$ (kN)")
    lf.panel(axc, "(c) Load at fracture")
    lf.save(fig, OUT / "fracture.png", dpi=300)


for make in (stress_strain, modulus_yield, caliper_photos, true_stress_strain, fracture):
    make()
