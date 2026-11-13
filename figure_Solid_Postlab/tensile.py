"""고체 Module#1 post-lab 공통 분석: CSV 읽기, 신율계 E, toe와 장비 컴플라이언스 보정, 특성점.

1, 2, 3번 그림과 수치가 모두 이 모듈에서 나오도록 한다.
"""
from pathlib import Path

import numpy as np

CSV = Path(__file__).resolve().parent / "data" / "tensile_brass.csv"

D0 = 8.0                    # mm, 시험 전 지름 (실측)
L0 = 50.0                   # mm, 표점 거리 = 신율계 게이지 길이
A0 = np.pi * D0**2 / 4      # mm^2
LF = 60.6                   # mm, 파단 후 표점 거리 (사진 02 판독)
DF = 6.2                    # mm, 목 최소 지름 (사진 01 판독)


def load():
    """CSV를 읽어 열별 배열을 돌려준다. 신율계 '-.----'는 NaN."""
    rows = CSV.read_text(encoding="utf-8").splitlines()[3:]

    def num(x):
        try:
            return float(x.strip('"'))
        except ValueError:
            return np.nan

    a = np.array([[num(x) for x in r.split(",")] for r in rows])
    t, F, s, ext, sig, eps = a.T
    return {"t": t, "F": F, "s": s, "ext": ext, "sig_sw": sig, "eps_sw": eps}


def smooth(x, w=51):
    return np.convolve(x, np.ones(w) / w, mode="same")


def fracture_index(F, drop=500.0):
    """파단 직전 인덱스: 가장 큰 하중 급락 구간이 시작되기 바로 앞 점."""
    i = int(np.argmin(np.diff(F)))
    while F[i - 1] - F[i] > drop:
        i -= 1
    return i


def extensometer_modulus(d, lo=5.0, hi=25.0):
    """신율계 구간(하중 봉우리 전)의 lo~hi MPa 선형 회귀로 E(MPa)를 구한다."""
    n = int(np.sum(~np.isnan(d["ext"])))
    ipk = int(np.argmax(d["F"][:n]))
    sig = d["F"][:ipk] / A0
    m = (sig > lo) & (sig < hi)
    E, _ = np.polyfit(d["ext"][:ipk][m] / L0, sig[m], 1)
    return E


def analyze(d, E, fit_lo=200.0, fit_hi=330.0):
    """toe와 컴플라이언스를 보정한 변형률과 특성점을 계산한다.

    스트로크의 선형 구간(fit_lo~fit_hi MPa)을 연장한 절편 s0를 원점으로 옮기고,
    장비 컴플라이언스 Cm = 1/k - L0/(E A0)만큼의 변위를 뺀다.
    """
    F, s = d["F"], d["s"]
    sig = F / A0
    ifr = fracture_index(F)
    iu = int(np.argmax(smooth(F)[:ifr]))
    idx = np.arange(len(F))

    i_lo = int(np.argmax((idx > 800) & (sig >= fit_lo)))
    i_hi = int(np.argmax((idx > i_lo) & (sig >= fit_hi)))
    k, b = np.polyfit(s[i_lo:i_hi], F[i_lo:i_hi], 1)
    s0 = -b / k
    Cm = 1 / k - L0 / (E * A0)
    eps_c = (s - s0 - F * Cm) / L0

    # 0.2 % offset: 소성 변형률 eps_c - sig/E 가 0.002가 되는 첫 점
    ep = eps_c - smooth(F) / A0 / E
    iy = int(np.argmax((idx > i_hi) & (ep >= 0.002)))
    # 비례한도: 소성 변형률이 0.01 %를 처음 넘는 점. 그 아래 탄성 구간은 크로스헤드 보정의
    # 잔차(변형률 약 1e-4)가 보이므로 그림에서는 원점에서 E 기울기 직선으로 잇는다.
    ipl = int(np.argmax((idx > i_lo) & (ep >= 1e-4)))

    return {
        "sig": sig, "eps_raw": s / L0, "eps_c": eps_c,
        "k": k, "s0": s0, "Cm": Cm, "E": E,
        "i_start": i_lo, "ipl": ipl, "iy": iy, "iu": iu, "ifr": ifr,
        "sigY": smooth(F)[iy] / A0, "sigU": smooth(F)[iu] / A0,
        "sigF": F[ifr] / A0, "Fmax": smooth(F)[iu], "Ff": F[ifr],
    }


if __name__ == "__main__":
    d = load()
    E = extensometer_modulus(d)
    r = analyze(d, E)
    print(f"E (extensometer)   {E/1e3:.1f} GPa")
    print(f"k, s0, Cm          {r['k']:.0f} N/mm, {r['s0']:.3f} mm, {r['Cm']*1e3:.4f} mm/kN")
    print(f"sigY (0.2 %)       {r['sigY']:.1f} MPa")
    print(f"sigU               {r['sigU']:.1f} MPa (Pmax {r['Fmax']/1e3:.2f} kN)")
    print(f"sigF               {r['sigF']:.1f} MPa (Pf {r['Ff']/1e3:.2f} kN)")
    print(f"eps at U  raw/corr {r['eps_raw'][r['iu']]:.4f} / {r['eps_c'][r['iu']]:.4f}")
    print(f"eps at F  raw/corr {r['eps_raw'][r['ifr']]:.4f} / {r['eps_c'][r['ifr']]:.4f}")
    print(f"(Lf-L0)/L0         {(LF-L0)/L0:.4f}")
