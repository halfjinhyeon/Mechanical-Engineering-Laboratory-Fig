"""계측 Module#1 pre-lab 그림.

  noisy_signal.png   주어진 noisy signal의 파형과 단측 진폭 스펙트럼
  downsampling.png   10, 5, 1 kHz로 다시 샘플링했을 때의 파형과 스펙트럼 (aliasing)
  lpf_design.png     anti-aliasing RC 저역 통과 필터 설계: 후보 필터의 gain과 부품 조합 비교

noisy_signal.png과 downsampling.png은 수업에서 받은 data/noisy_signal.wav가 있어야 그려진다.
"""
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import labfig as lf

OUT = HERE / "figures"
WAV = HERE / "data" / "noisy_signal.wav"
F_SIG, F_NOISE = 300.0, 6100.0          # 신호와 잡음의 주파수 (Hz)
lf.use()


def spectrum(y, fs):
    """단측 진폭 스펙트럼. (주파수, 진폭)"""
    n = len(y)
    p = np.abs(np.fft.fft(y))[: n // 2 + 1] / n
    p[1:-1] *= 2
    return fs * np.arange(n // 2 + 1) / n, p


def alias(f, fs):
    """주파수 f의 성분이 샘플링 주파수 fs에서 관찰되는 위치."""
    return abs(f - fs * round(f / fs))


def peak(f, p, f0):
    i = int(np.argmin(np.abs(f - f0)))
    return f[i], p[i]


def load_wav():
    with wave.open(str(WAV)) as w:
        fs = w.getframerate()
        y = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768.0
    return y, fs


# ---------------------------------------------------------------- noisy_signal
def noisy_signal(y, fs):
    t = np.arange(len(y)) / fs
    f, p = spectrum(y, fs)
    fig, ax = lf.mosaic([["a", "b"], ["c", "c"]], "full", 3.4)

    lf.trace(ax["a"], t, y, lw=0.3)
    ax["a"].set_xlim(0, 0.5)
    ax["a"].set_xlabel(r"Time $t$ (s)")
    lf.panel(ax["a"], "(a) Full waveform")

    lf.trace(ax["b"], t * 1e3, y, lw=0.9)
    ax["b"].set_xlim(0, 10)
    ax["b"].set_xlabel(r"Time $t$ (ms)")
    lf.panel(ax["b"], "(b) Zoom, 0 to 10 ms")
    for k in ("a", "b"):
        ax[k].set_ylim(-1.1, 1.1)
        ax[k].set_ylabel(r"$x(t)$ (normalized)")

    lf.trace(ax["c"], f, p, lw=0.9)
    for f0, name in ((F_SIG, "signal"), (F_NOISE, "noise")):
        fp, pp = peak(f, p, f0)
        lf.note(ax["c"], f"{fp:.0f} Hz ({name})\namplitude {pp:.3f}", (fp + 130, pp - 0.07))
    ax["c"].set_xlim(0, fs / 2)
    ax["c"].set_ylim(0, 0.8)
    ax["c"].set_xlabel(r"Frequency $f$ (Hz)")
    ax["c"].set_ylabel("Amplitude (normalized)")
    lf.panel(ax["c"], "(c) Single-sided amplitude spectrum")
    lf.save(fig, OUT / "noisy_signal.png")


# ---------------------------------------------------------------- downsampling
def downsampling(y, fs):
    fig, axes = lf.figure("full", 3.5, nrows=2, ncols=3, sharey="row")
    for k, fs_d in enumerate((10e3, 5e3, 1e3)):
        step = int(round(fs / fs_d))
        yd = y[::step]                               # 새 샘플 시각이 원래 샘플 시각과 겹치므로 보간이 필요 없다
        td = np.arange(len(yd)) / fs_d
        f, p = spectrum(yd, fs_d)
        top, bot = axes[0, k], axes[1, k]

        lf.trace(top, td * 1e3, yd, lw=0.7, marker="o", ms={10e3: 1.5, 5e3: 2.0, 1e3: 2.8}[fs_d])
        top.set_xlim(0, 10)
        top.set_xticks([0, 5, 10])
        top.set_ylim(-1.1, 1.1)
        top.set_xlabel(r"Time $t$ (ms)")
        lf.panel(top, f"({'abc'[k]}) $f_s$ = {fs_d / 1e3:.0f} kHz")

        lf.trace(bot, f, p, lw=0.9)
        fa = alias(F_NOISE, fs_d)
        gap = 0.03 * fs_d / 2
        # 신호 피크 이름은 피크 옆 가운데 높이에, 접힌 잡음 피크 이름은 위쪽에 둔다
        lf.note(bot, f"{F_SIG:.0f} Hz", (F_SIG + gap, 0.42), fontsize=7.5)
        right = fa < 0.55 * fs_d / 2
        lf.note(bot, f"{fa:.0f} Hz\n(6100 Hz alias)", (fa + (gap if right else -gap), 0.88),
                ha="left" if right else "right", va="top", fontsize=7.5)
        bot.set_xlim(0, fs_d / 2)
        bot.set_ylim(0, 0.9)
        bot.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
        bot.set_xlabel(r"Frequency $f$ (Hz)")
    axes[0, 0].set_ylabel(r"$x(t)$ (normalized)")
    axes[1, 0].set_ylabel("Amplitude (normalized)")
    lf.save(fig, OUT / "downsampling.png")


# ---------------------------------------------------------------- lpf_design
def gain_db(f, tau):
    """1차 RC 저역 통과 필터의 gain (dB)."""
    return -10 * np.log10(1 + (2 * np.pi * np.asarray(f) * tau) ** 2)


def db(v, digits=2):
    return f"{v:.{digits}f}".replace("-", "−")


def lpf_design():
    fn = 10e3                                        # fs = 20 kHz의 Nyquist 주파수
    # 매뉴얼 부품표: 저항 14종 (ohm), 세라믹 커패시터 30종 (pF)
    R = np.array([10, 100, 150, 220, 330, 470, 510, 1e3, 2e3, 4.7e3, 10e3, 100e3, 1e6, 10e6])
    C = np.array([2, 3, 5, 10, 15, 22, 30, 33, 47, 68, 75, 82, 100, 150, 220, 330, 470, 680, 1e3, 1.5e3,
                  2.2e3, 3.3e3, 4.7e3, 6.8e3, 1e4, 1.5e4, 2.2e4, 4.7e4, 6.8e4, 1e5]) * 1e-12
    tau = np.unique(np.round(np.outer(R, C).ravel(), 15))
    gs, gn = gain_db(F_SIG, tau), gain_db(F_NOISE, tau)
    ok = gs >= -3                                    # 조건: 신호 gain이 -3 dB 이상
    best = tau[ok][np.argmin(gn[ok])]                # 조건을 만족하면서 잡음 gain이 최소인 RC
    print(f"  {tau.size} RC values, {ok.sum()} feasible, best RC = {best:.2e} s, fc = {1 / (2 * np.pi * best):.1f} Hz, "
          f"G(300) = {gain_db(F_SIG, best):.2f} dB, G(6100) = {gain_db(F_NOISE, best):.2f} dB")

    fig, (axa, axb) = lf.figure("full", 2.8, ncols=2)

    # (a) 후보 필터의 gain 곡선. 선택한 조합을 굵게
    f = np.logspace(1, 5, 800)
    cands = [(4.7e3, 100e-9, ", selected"), (4.7e3, 68e-9, ""), (10e3, 68e-9, "")]
    for i, (r, c, tag) in enumerate(cands):
        fc = 1 / (2 * np.pi * r * c)
        name = rf"{r / 1e3:g} kΩ, {c * 1e9:.0f} nF ($f_c$ = {fc:.0f} Hz)" + tag
        lf.trace(axa, f, gain_db(f, r * c), series=i, lw=1.9 if i == 0 else 1.2, label=name)
    lf.href(axa, -3, "−3 dB", x=0.98)
    lf.vref(axa, F_SIG, "300 Hz (signal)", y=0.30)
    lf.vref(axa, F_NOISE, "6100 Hz (noise)", y=0.93)
    lf.vref(axa, fn, r"$f_N$ = 10 kHz", y=0.93, side="right")
    for f0 in (F_SIG, F_NOISE):
        lf.mark(axa, f0, gain_db(f0, best), series=0)
    lf.note(axa, db(gain_db(F_SIG, best)) + " dB", (F_SIG, gain_db(F_SIG, best)), (25, -11))
    lf.note(axa, db(gain_db(F_NOISE, best)) + " dB", (F_NOISE, gain_db(F_NOISE, best)), (2.1e4, -16))
    axa.set_xscale("log")
    axa.set_xlim(10, 1e5)
    axa.set_ylim(-58, 4)                             # 아래쪽에 범례 자리를 둔다
    axa.set_yticks(np.arange(-50, 1, 10))
    axa.set_xlabel(r"Frequency $f$ (Hz)")
    axa.set_ylabel("Gain (dB)")
    lf.panel(axa, "(a) Gain of candidate RC filters")
    lf.legend(axa, loc="lower left", fontsize=7.5)

    # (b) 부품표의 모든 RC 값: 신호 gain 대 잡음 gain
    lf.points(axb, gs[~ok], gn[~ok], mec=lf.GRAY, ms=3.4, label="Infeasible")
    lf.points(axb, gs[ok], gn[ok], series=0, filled=True, ms=3.4, label="Feasible (≥ −3 dB)")
    lf.mark(axb, gain_db(F_SIG, best), gain_db(F_NOISE, best), series=1, marker="*", ms=11, mfc=lf.color(1),
            mew=0.6, label="Selected")
    lf.vref(axb, -3, "−3 dB")
    lf.note(axb, rf"RC = {best * 1e4:.1f} × 10$^{{-4}}$ s" + f"\n({db(gain_db(F_SIG, best))} dB, {db(gain_db(F_NOISE, best))} dB)",
            (gain_db(F_SIG, best), gain_db(F_NOISE, best)), (-5.6, -19.5))
    axb.set_xlim(-7, 0.15)
    axb.set_ylim(-35, -5)
    axb.set_xlabel("Signal gain at 300 Hz (dB)")
    axb.set_ylabel("Noise gain at 6100 Hz (dB)")
    lf.panel(axb, "(b) All R and C combinations")
    lf.legend(axb, loc="upper left")
    lf.save(fig, OUT / "lpf_design.png")


if WAV.exists():
    y, fs = load_wav()
    noisy_signal(y, fs)
    downsampling(y, fs)
else:
    print(f"skip noisy_signal, downsampling: {WAV} not found")
lpf_design()
