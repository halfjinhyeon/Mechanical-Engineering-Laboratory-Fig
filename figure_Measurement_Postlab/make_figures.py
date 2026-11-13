"""계측 Module#1 post-lab 그림.

  lab1_spectra.png     Lab 1: 샘플링 주파수 4가지로 측정한 신호의 FFT 진폭 스펙트럼
  lab1_waveforms.png   Lab 1: 20 kHz와 1 kHz로 측정한 시간 파형
  bode.png             Lab 2 RC 필터의 Bode plot (설계값)
  gain_phase.png       Lab 2: 측정한 gain과 위상, 설계 모델과 비교
  superposition.png    측정한 gain과 위상으로 합성한 noisy signal의 필터 입출력
  antialiasing.png     fs = 1 kHz에서 필터 사용 전후의 예상 스펙트럼

Lab 1은 data/Lab1_*.csv (myDAQ 측정값)를 읽는다. Lab 2 측정값은 LabVIEW 화면에서 읽은 값을 아래에 적었다.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import labfig as lf

OUT = HERE / "figures"
DATA = HERE / "data"
lf.use()

F_SIG, F_NOISE = 300.0, 6100.0                      # 신호와 잡음의 주파수 (Hz)
R, C = 4.7e3, 100e-9                                # Lab 2 필터 부품
FC = 1 / (2 * np.pi * R * C)                        # 설계 cutoff frequency, 338.6 Hz
FC_FIT = 637.0                                      # 측정 gain에 맞춘 1차 모델의 cutoff frequency (Hz)

# Lab 2 측정값: 입력 주파수 (Hz), CH0 = 필터 입력 rms (mV), CH1 = 필터 출력 rms (mV)
F_LAB = np.array([30, 300, 340, 3400, 6100, 10000.0])
CH0 = np.array([353.20, 353.41, 353.40, 353.10, 352.58, 348.43])
CH1 = np.array([351.93, 313.88, 305.75, 65.02, 36.35, 22.48])
GAIN = CH1 / CH0
GAIN_DB = 20 * np.log10(GAIN)
# 위상은 파형에 정현파를 최소제곱 적합해 구한 값 (deg)과 그 표준편차. 30, 300, 340 Hz만 구했다
PHASE_F = F_LAB[:3]
PHASE = np.array([-3.9, -29.5, -32.6])
PHASE_SD = np.array([0.7, 1.3, 1.3])


def gain_db(f, fc):
    return -10 * np.log10(1 + (np.asarray(f) / fc) ** 2)


def phase_deg(f, fc):
    return -np.degrees(np.arctan(np.asarray(f) / fc))


def db(v, digits=2):
    return f"{v:.{digits}f}".replace("-", "−")


def load_lab1(name):
    """Lab 1 CSV. (샘플링 주파수, 시간, 전압)"""
    t, v = np.genfromtxt(DATA / name, delimiter=",", skip_header=4, encoding="utf-8-sig").T
    return 1 / (t[1] - t[0]), t, v


def spectrum_rms(v, fs):
    """단측 진폭 스펙트럼, rms 기준. (주파수, 크기)"""
    n = len(v)
    p = np.abs(np.fft.fft(v))[: n // 2 + 1] / n
    p[1:-1] *= np.sqrt(2)
    return fs * np.arange(n // 2 + 1) / n, p


def alias(f, fs):
    return abs(f - fs * round(f / fs))


def peak(f, p, f0):
    i = int(np.argmin(np.abs(f - f0)))
    return f[i], p[i]


LAB1 = {name: load_lab1(f"Lab1_{name}.csv") for name in ("20kHz", "10kHz", "5kHz", "1kHz")}


# ---------------------------------------------------------------- lab1_spectra
def lab1_spectra():
    fig, axes = lf.figure("full", 3.9, nrows=2, ncols=2, sharey=True)
    for k, (ax, (fs, t, v)) in enumerate(zip(axes.ravel(), LAB1.values())):
        f, p = spectrum_rms(v, fs)
        lf.trace(ax, f[1:], p[1:], lw=0.9)           # 0 Hz의 직류 성분 (0.48 ~ 0.68 V)은 그리지 않는다
        fa = alias(F_NOISE, fs)
        fp, pp = peak(f, p, fa)
        right = fa < 0.6 * fs / 2
        gap = 0.025 * fs / 2
        lf.note(ax, f"{fp:.0f} Hz" + (" (noise)" if fa == F_NOISE else " (noise alias)") + f"\n{pp:.3f} V",
                (fp + (gap if right else -gap), pp), ha="left" if right else "right", va="top")
        for f0 in (60.0, F_SIG):
            fq, pq = peak(f, p, f0)
            if 0 < fa - f0 < 0.2 * fs / 2:           # 바로 오른쪽에 잡음 피크가 있으면 이름을 피크 위에 쓴다
                lf.note(ax, f"{f0:.0f} Hz", (fq + 2 * gap, pq + 0.03), fontsize=7.5, ha="right")
            else:
                lf.note(ax, f"{f0:.0f} Hz", (fq + gap, pq + 0.035), fontsize=7.5)
        ax.set_xlim(0, fs / 2)
        ax.set_ylim(0, 0.4)
        lf.panel(ax, f"({'abcd'[k]}) $f_s$ = {fs / 1e3:.0f} kHz ($f_N$ = {fs / 2e3:g} kHz)")
    for ax in axes[1]:
        ax.set_xlabel(r"Frequency $f$ (Hz)")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"Magnitude (V$_{rms}$)")
    lf.save(fig, OUT / "lab1_spectra.png")


# ---------------------------------------------------------------- lab1_waveforms
def lab1_waveforms():
    fig, (axa, axb) = lf.figure("full", 1.9, ncols=2, sharey=True)
    fs, t, v = LAB1["20kHz"]
    lf.trace(axa, t * 1e3, v, lw=0.5)
    axa.annotate("", xy=(12.4, 0.27), xytext=(12.4 + 1e3 / 60, 0.27),
                 arrowprops=dict(arrowstyle="<->", lw=0.8, color=lf.INK, shrinkA=0, shrinkB=0))
    lf.note(axa, "16.7 ms (60 Hz)", (12.4 + 500 / 60, 0.36), ha="center", va="bottom")
    lf.panel(axa, "(a) $f_s$ = 20 kHz")

    fs, t, v = LAB1["1kHz"]
    lf.trace(axb, t * 1e3, v, lw=1.0, marker="o", ms=2.4)
    lf.panel(axb, "(b) $f_s$ = 1 kHz")
    for ax in (axa, axb):
        ax.set_xlim(0, 50)
        ax.set_ylim(-1.5, 0.75)
        ax.set_xlabel(r"Time $t$ (ms)")
    axa.set_ylabel("Voltage (V)")
    lf.save(fig, OUT / "lab1_waveforms.png")


# ---------------------------------------------------------------- bode
def bode():
    f = np.logspace(0, 5, 1000)
    fig, (axm, axp) = lf.figure("wide", 3.7, nrows=2, sharex=True)

    lf.trace(axm, f, gain_db(f, FC), series=0, label=r"$|G(j\omega)|$")
    lf.model(axm, f, np.minimum(0, -20 * np.log10(f / FC)), label="Asymptotes")
    lf.points(axm, F_LAB, gain_db(F_LAB, FC), series=1, label="Lab 2 input frequencies")
    lf.mark(axm, FC, gain_db(FC, FC), series=1, marker="*", ms=10, mfc=lf.color(1), mew=0.6)
    lf.vref(axm, FC)
    lf.href(axm, gain_db(FC, FC), "−3.01 dB", x=0.98)
    lf.note(axm, rf"$f_c$ = {FC:.1f} Hz", (FC, gain_db(FC, FC)), (25, -17))
    lf.note(axm, "−20 dB/decade", (1.6e4, -24), ha="left")
    axm.set_ylim(-50, 5)
    axm.set_ylabel("Magnitude (dB)")
    lf.legend(axm, loc="lower left")

    lf.trace(axp, f, phase_deg(f, FC), series=0)
    lf.points(axp, F_LAB, phase_deg(F_LAB, FC), series=1)
    lf.mark(axp, FC, -45, series=1, marker="*", ms=10, mfc=lf.color(1), mew=0.6)
    lf.vref(axp, FC)
    lf.href(axp, -45, "−45°")
    axp.set_xscale("log")
    axp.set_xlim(1, 1e5)
    axp.set_ylim(-95, 5)
    axp.set_yticks(np.arange(-90, 1, 30))
    axp.set_xlabel(r"Frequency $f$ (Hz)")
    axp.set_ylabel("Phase (deg)")
    lf.save(fig, OUT / "bode.png")


# ---------------------------------------------------------------- gain_phase
def gain_phase():
    f = np.logspace(1, np.log10(2e4), 600)
    fig, (axg, axp) = lf.figure("wide", 3.7, nrows=2, sharex=True)
    for ax in (axg, axp):                            # 통과대역, cutoff 부근, 저지대역
        lf.region(ax, 10, 200, "Pass band" if ax is axg else None, alpha=0.05)
        lf.region(ax, 200, 2000, "Around cutoff" if ax is axg else None, alpha=0.14)
        lf.region(ax, 2000, 2e4, "Stop band" if ax is axg else None, alpha=0.24)

    lf.model(axg, f, gain_db(f, FC), label=rf"Design model ($f_c$ = {FC:.1f} Hz)")
    # 저지대역 측정점 3개를 지나는 -20 dB/decade 기준선
    c0 = np.mean(GAIN_DB[3:] + 20 * np.log10(F_LAB[3:]))
    fr = np.array([700.0, 2e4])
    lf.model(axg, fr, c0 - 20 * np.log10(fr), series=1, ls=lf.REF_DASH, label="−20 dB/decade reference")
    lf.points(axg, F_LAB, GAIN_DB, series=0, label="Measured, CH1/CH0 (rms)")
    lf.href(axg, -3, "−3 dB", below=True)
    # 측정값은 점 바로 옆에 쓴다 (지시선 없이, 점에서 떨어진 거리는 pt 단위)
    value = dict(textcoords="offset points", arrowprops=None, fontsize=7.5, va="bottom")
    place = [((0, 5), "center"), ((-3, 5), "right"), ((3, 5), "left"), ((6, 2), "left"), ((6, 2), "left"), ((6, 2), "left")]
    for fi, gi, (off, ha) in zip(F_LAB, GAIN_DB, place):
        lf.note(axg, db(gi), (fi, gi), off, ha=ha, **value)
    axg.set_ylim(-34, 9)
    axg.set_yticks([-30, -20, -10, 0])
    axg.set_ylabel("Gain (dB)")
    lf.legend(axg, loc="lower left", fontsize=7.5)

    lf.model(axp, f, phase_deg(f, FC), label="Design model")
    lf.points(axp, PHASE_F, PHASE, yerr=PHASE_SD, series=0, label="Measured (waveform fit, ±1σ)")
    lf.href(axp, -45, "−45°", x=0.98)
    for fi, pi, (off, ha) in zip(PHASE_F, PHASE, [((5, 4), "left"), ((-2, 9), "right"), ((6, 3), "left")]):
        lf.note(axp, db(pi, 1) + "°", (fi, pi), off, ha=ha, **value)
    axp.set_xscale("log")
    axp.set_xlim(10, 2e4)
    axp.set_ylim(-95, 5)
    axp.set_yticks(np.arange(-90, 1, 30))
    axp.set_xlabel(r"Frequency $f$ (Hz)")
    axp.set_ylabel("Phase (deg)")
    lf.legend(axp, loc="lower left", fontsize=7.5)
    lf.save(fig, OUT / "gain_phase.png")


# ---------------------------------------------------------------- superposition
def superposition():
    t = np.linspace(0, 10e-3, 4000)
    g_sig, g_noise = GAIN[1], GAIN[4]                # 300 Hz, 6100 Hz의 측정 gain
    ph_sig = np.radians(PHASE[1])                    # 300 Hz의 측정 위상
    ph_noise = np.radians(phase_deg(F_NOISE, FC_FIT))    # 6100 Hz는 적합 모델의 위상 (약 -84 deg)
    x = 0.5 * np.sin(2 * np.pi * F_SIG * t) + 0.5 * np.sin(2 * np.pi * F_NOISE * t)
    y = (0.5 * g_sig * np.sin(2 * np.pi * F_SIG * t + ph_sig)
         + 0.5 * g_noise * np.sin(2 * np.pi * F_NOISE * t + ph_noise))

    fig, ax = lf.figure("wide", 2.1)
    lf.trace(ax, t * 1e3, x, color=lf.GRAY, lw=0.7, label="Input: 300 Hz + 6100 Hz (1 V$_{pp}$ each)")
    lf.trace(ax, t * 1e3, y, series=0, label=f"Filter output (measured gains {g_sig:.3f}, {g_noise:.3f})")
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.15, 1.75)
    ax.set_yticks([-1, -0.5, 0, 0.5, 1])
    ax.set_xlabel(r"Time $t$ (ms)")
    ax.set_ylabel("Voltage (V)")
    lf.legend(ax, loc="upper left", fontsize=7.5)
    lf.save(fig, OUT / "superposition.png")
    print(f"  phase used at 6100 Hz: {np.degrees(ph_noise):.1f} deg")


# ---------------------------------------------------------------- antialiasing
def antialiasing():
    fs, t, v = LAB1["1kHz"]
    fn = fs / 2
    fig, (axa, axb) = lf.figure("full", 2.7, ncols=2)

    # (a) 필터 gain과 fs = 1 kHz의 Nyquist 주파수
    f = np.logspace(1, np.log10(2e4), 600)
    lf.region(axa, fn, 2e4, "aliased into\n0 to 500 Hz", fontsize=7.5)
    lf.model(axa, f, gain_db(f, FC), color=lf.GRAY, ls=lf.REF_DASH, lw=1.1,
             label=rf"Design model ($f_c$ = {FC:.1f} Hz)")
    lf.model(axa, f, gain_db(f, FC_FIT), series=0, label=rf"Fitted model ($f_{{c,eff}}$ = {FC_FIT:.0f} Hz)")
    lf.points(axa, F_LAB, GAIN_DB, series=0, label="Measured (Lab 2, rms)")
    lf.vref(axa, fn, rf"$f_N$ = {fn:.0f} Hz", y=0.42)
    lf.vref(axa, F_SIG, "300 Hz (signal)", y=0.42)
    lf.vref(axa, F_NOISE, "6100 Hz (noise)")
    axa.set_xscale("log")
    axa.set_xlim(10, 2e4)
    axa.set_ylim(-42, 3)
    axa.set_xlabel(r"Frequency $f$ (Hz)")
    axa.set_ylabel("Gain (dB)")
    lf.panel(axa, rf"(a) Filter gain and $f_N$ at $f_s$ = {fs / 1e3:.0f} kHz")
    lf.legend(axa, loc="lower left", fontsize=7.5)

    # (b) 필터가 없을 때 (Lab 1 측정)와 있을 때 (예상)의 스펙트럼
    fsp, p = spectrum_rms(v, fs)
    names = ["60 Hz\n(hum)", f"{alias(F_NOISE, fs):.0f} Hz\n(noise alias)", "180 Hz\n(hum)", "300 Hz\n(signal)"]
    seen = [60.0, alias(F_NOISE, fs), 180.0, F_SIG]            # fs = 1 kHz에서 보이는 주파수
    origin = [60.0, F_NOISE, 180.0, F_SIG]                     # 필터를 지날 때의 실제 주파수
    without = np.array([peak(fsp, p, f0)[1] for f0 in seen])
    # 300, 6100 Hz는 측정 gain, 측정하지 않은 60, 180 Hz는 적합 모델의 gain을 쓴다
    g = np.array([GAIN[list(F_LAB).index(f0)] if f0 in F_LAB else 10 ** (gain_db(f0, FC_FIT) / 20) for f0 in origin])
    lf.bars(axb, names, [without, without * g], fmt="{:.3f}", rotation=90,
            labels=["Without filter (Lab 1, measured)", "With filter (expected)"])
    axb.tick_params(axis="x", labelsize=7.5)
    axb.set_ylim(0, 0.54)
    axb.set_ylabel(r"Magnitude (V$_{rms}$)")
    lf.panel(axb, rf"(b) Expected spectrum at $f_s$ = {fs / 1e3:.0f} kHz")
    lf.legend(axb, loc="upper right", fontsize=7.5)
    lf.save(fig, OUT / "antialiasing.png")
    print("  without:", np.round(without, 3), " with:", np.round(without * g, 3))


for make in (lab1_spectra, lab1_waveforms, bode, gain_phase, superposition, antialiasing):
    make()
