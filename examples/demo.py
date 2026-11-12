"""labfig 사용 예. 숫자는 모두 예시용으로 만든 값이고 실험 데이터가 아니다.

실행: python examples/demo.py   (결과는 examples/ 에 저장된다)
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import labfig as lf

OUT = Path(__file__).resolve().parent
rng = np.random.default_rng(2)
lf.use()

# ---------------------------------------------------------------- 예시 1: 이산 측정값, 오차 막대, 회귀
fig, (axa, axb) = lf.figure("full", 2.6, ncols=2)

x = np.linspace(2, 20, 10)                         # 변위 (mm)
y = 12.4 * x + 3 + rng.normal(0, 6, x.size)        # 하중 (N)
lf.points(axa, x, y, yerr=7.0, label="Measured")
fit = lf.linfit(axa, x, y, span=(0, 22), label="Linear fit")
lf.note(axa, rf"$k$ = {fit.slope:.1f} ± {fit.slope_se:.1f} N/mm" + "\n" + rf"($R^2$ = {fit.r2:.3f})",
        (1.2, 228))
axa.set_xlim(0, 22)
axa.set_ylim(0, 300)
axa.set_xlabel(r"변위 $\delta$ (mm)")
axa.set_ylabel(r"하중 $P$ (N)")
lf.panel(axa, "(a) 강성 보정")
lf.legend(axa, loc="lower right")

f = np.array([0.05, 0.10, 0.15, 0.20, 0.25])       # 이송 (mm/rev)
ff = np.linspace(0.04, 0.26, 50)
for i, r_eps in enumerate((0.2, 0.4, 0.8, 1.2)):   # 노즈 반경 (mm)
    ra_th = f ** 2 / (32 * r_eps) * 1e3            # 이론 표면 거칠기 (um)
    ra = ra_th * (1 + rng.normal(0.08, 0.06, f.size)) + 0.15
    lf.points(axb, f, ra, series=i, label=rf"$r_\varepsilon$ = {r_eps} mm")
    lf.model(axb, ff, ff ** 2 / (32 * r_eps) * 1e3, series=i)
lf.model(axb, [], [], label=r"Theory, $f^2/32r_\varepsilon$")      # 범례용 검정 점선
axb.set_xlim(0, 0.3)
axb.set_ylim(0, 12)
lf.plain_ticks(axb.xaxis, 2)
axb.set_xlabel(r"이송 $f$ (mm/rev)")
axb.set_ylabel(r"표면 거칠기 $R_a$ (μm)")
lf.panel(axb, "(b) 노즈 반경별 표면 거칠기")
lf.legend(axb, loc="upper left")
lf.save(fig, OUT / "demo1_points.png")

# ---------------------------------------------------------------- 예시 2: 촘촘한 측정 곡선, 모델, 구간
fig, ax = lf.figure("single", 2.7)
t = np.linspace(0, 120, 1200)                      # 시간 (s)
t0 = 20.0


def cooling(tau, drop):
    return 26.8 - np.where(t > t0, drop * (1 - np.exp(-(t - t0) / tau)), 0.0)


lf.trace(ax, t, cooling(14, 9.5) + rng.normal(0, 0.05, t.size), series=0, label="센서 1 (캔 표면)")
lf.trace(ax, t, cooling(22, 6.0) + rng.normal(0, 0.05, t.size), series=1, label="센서 2 (노즐)")
lf.model(ax, t, cooling(14, 9.5), label="1차 응답 모델")
lf.region(ax, t0, 60, "분사 구간")
lf.note(ax, r"$T_{min}$ = 17.3 °C", (118, 17.4), (80, 15.3))
ax.set_xlim(0, 120)
ax.set_ylim(14, 28)
ax.set_xlabel(r"시간 $t$ (s)")
ax.set_ylabel(r"온도 $T$ (°C)")
lf.legend(ax, loc="upper right")
lf.save(fig, OUT / "demo2_trace.png")

# ---------------------------------------------------------------- 회귀 계산 검증 (numpy와 비교)
p, cov = np.polyfit(x, y, 1, cov=True)
assert np.allclose([fit.slope, fit.intercept], p)
assert np.allclose([fit.slope_se, fit.intercept_se], np.sqrt(np.diag(cov)))
print(f"linfit check ok: slope {fit.slope:.3f} ± {fit.slope_se:.3f}, intercept {fit.intercept:.2f} ± {fit.intercept_se:.2f}")

# ---------------------------------------------------------------- 흑백 인쇄 확인용
from PIL import Image

for name in ("demo1_points", "demo2_trace"):
    Image.open(OUT / f"{name}.png").convert("L").save(OUT / f"{name}_gray.png", dpi=(600, 600))
    print("saved", OUT / f"{name}_gray.png")
