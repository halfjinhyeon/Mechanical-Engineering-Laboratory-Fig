"""3번 수치: 공칭값과 진값 비교, 파단 시 저장 에너지.

`python q3.py` 로 표 3-1과 본문 수치를 출력한다. 그림 3-1, 3-2도 이 모듈의 값을 쓴다.
"""
import numpy as np

import tensile as T

RHO_BRASS = 8470.0      # kg/m^3, Yellow Brass (강의자료 p. 8, Beer Appendix B)


def compute():
    d = T.load()
    E = T.extensometer_modulus(d)
    r = T.analyze(d, E)
    F, t = d["F"], d["t"]
    Fs = T.smooth(F)
    ec = r["eps_c"]
    iy, iu, ifr = r["iy"], r["iu"], r["ifr"]
    idx = np.arange(len(F))

    # 균일 변형 구간(항복~인장강도)의 진응력-진변형률: 부피 일정 가정
    m = (idx >= r["ipl"]) & (idx <= iu)          # 비례한도부터 (그 아래는 E 직선)
    eT = np.log1p(ec[m])
    sT = Fs[m] / T.A0 * (1 + ec[m])

    # 파단점: 목의 최소 단면적 기준 진값
    Af = np.pi * T.DF**2 / 4
    Pf = F[ifr]

    # 비례한도: 소성 변형률이 0.01 %를 처음 넘는 응력
    ep = ec - Fs / T.A0 / E
    ipl = r["ipl"]

    # 인성계수: 보정한 공칭 곡선 아래 면적 (원점에서 시작)
    x = np.concatenate([[0.0], ec[r["i_start"]:ifr + 1]])
    y = np.concatenate([[0.0], r["sig"][r["i_start"]:ifr + 1]])
    ut = np.trapezoid(y, x)                                   # MJ/m^3

    k = r["k"]
    out = {
        "d": d, "r": r, "E": E, "eT": eT, "sT": sT,
        "sig_pl": Fs[ipl] / T.A0, "eps_pl": ec[ipl],
        # 항복
        "sigY": r["sigY"], "epsY": ec[iy],
        "sigY_T": r["sigY"] * (1 + ec[iy]), "epsY_T": np.log1p(ec[iy]),
        # 인장강도 (네킹 시작)
        "sigU": r["sigU"], "epsU": ec[iu],
        "sigU_T": r["sigU"] * (1 + ec[iu]), "epsU_T": np.log1p(ec[iu]),
        # 파단
        "sigF": r["sigF"], "epsF": ec[ifr], "EL": (T.LF - T.L0) / T.L0,
        "sigF_T": Pf / Af, "epsF_T": np.log(T.A0 / Af), "RA": 1 - Af / T.A0,
        "RA_uniform": 1 - 1 / (1 + ec[iu]),
        # 에너지
        "Pf": Pf, "k": k, "U_total": Pf**2 / (2 * k) / 1e3,          # J
        "U_gauge": Pf**2 * T.L0 / (2 * T.A0 * E) / 1e3,             # J, 식 (14-16)
        "delta_el": Pf / k,                                          # mm
        "u_T": ut, "W_plastic": ut * T.A0 * T.L0 / 1e3,              # J
        "t_test": t[ifr], "s_frac": d["s"][ifr],
        "drop": F[ifr:ifr + 8], "t_drop": t[ifr:ifr + 8] - t[ifr],
        "c_bar": np.sqrt(E * 1e6 / RHO_BRASS),
    }
    return out


if __name__ == "__main__":
    q = compute()
    print(f"E                    {q['E'] / 1e3:.1f} GPa")
    print(f"proportional limit   {q['sig_pl']:.0f} MPa (ep 0.01 %)")
    print(f"yield     eng {q['sigY']:.1f} MPa, {q['epsY']:.4f} | true {q['sigY_T']:.1f} MPa, {q['epsY_T']:.4f}"
          f" | diff {100 * (q['sigY_T'] / q['sigY'] - 1):.1f} %")
    print(f"ultimate  eng {q['sigU']:.1f} MPa, {q['epsU']:.4f} | true {q['sigU_T']:.1f} MPa, {q['epsU_T']:.4f}"
          f" | diff {100 * (q['sigU_T'] / q['sigU'] - 1):.1f} %")
    print(f"fracture  eng {q['sigF']:.1f} MPa, {q['epsF']:.4f} (EL {q['EL']:.4f}) | true {q['sigF_T']:.1f} MPa,"
          f" {q['epsF_T']:.4f} | diff {100 * (q['sigF_T'] / q['sigF'] - 1):.1f} %")
    print(f"sigY/sigU {q['sigY'] / q['sigU']:.3f}, sigU/sigY eng {q['sigU'] / q['sigY']:.3f},"
          f" true {q['sigU_T'] / q['sigY_T']:.3f}, sigF/sigU {q['sigF'] / q['sigU']:.3f}")
    print(f"true stress U->F {100 * (q['sigF_T'] / q['sigU_T'] - 1):.1f} %, eng {100 * (q['sigF'] / q['sigU'] - 1):.1f} %")
    print(f"RA {q['RA']:.3f}, RA if uniform to U {q['RA_uniform']:.3f}, post-U elongation {q['EL'] - q['epsU']:.3f}")
    print(f"U_total {q['U_total']:.1f} J, U_gauge {q['U_gauge']:.2f} J, delta_el {q['delta_el']:.2f} mm,"
          f" crosshead {q['s_frac']:.2f} mm")
    print(f"toughness {q['u_T']:.1f} MJ/m3, plastic work {q['W_plastic']:.0f} J over {q['t_test']:.0f} s"
          f" = {q['W_plastic'] / q['t_test']:.2f} W; elastic release >= {q['U_total'] / 0.01:.0f} W")
    print("drop", np.round(q["drop"]).astype(int), np.round(q["t_drop"], 2))
    print(f"bar wave speed {q['c_bar']:.0f} m/s, 50 mm in {0.05 / q['c_bar'] * 1e6:.0f} us")

    # 소리 크기 추정 (수업 범위 밖, 표 3-2): 방출 에너지 U 중 비율 eta가 소리가 되어
    # 반사 없이 구면으로 퍼진다고 보고, r = 1 m에서 세기 레벨 기준 I0 = 1 pW/m^2로 계산
    I0, r, T = 1e-12, 1.0, 0.03
    for eta, src in ((1e-8, "[5] low"), (1.4e-4, "[6] sphere"), (1e-3, "[5] high")):
        for U in (4.0, 32.0):
            e = eta * U / (4 * np.pi * r**2)                    # J/m^2
            LE = 10 * np.log10(e / (I0 * 1.0))                  # SEL
            print(f"eta {eta:.1e} {src:10s} U {U:4.0f} J  Es {eta * U * 1e3:.3g} mJ"
                  f"  SEL {LE:5.1f} dB  L(30 ms) {LE + 10 * np.log10(1 / T):5.1f} dB")
