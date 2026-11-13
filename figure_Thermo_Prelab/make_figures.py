"""열역학 Module#1 pre-lab 개념도 (단열 팽창 실험).

  system_boundary.png   분사 전후의 계 경계 (주황 점선: 계, 파란 점선: 분사될 기체)
  apparatus.png         실험 장치 구성

그래프가 아닌 도형 그림이라 labfig에서는 글꼴, 색, 정확한 저장 폭만 가져다 쓴다.
"""
import random
import sys
from pathlib import Path

from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import labfig as lf

OUT = HERE / "figures"
lf.use()

LIQUID = "#8DBBDD"                    # 액체 채움
SYSTEM = lf.SERIES[1]                 # 계 경계
GAS = lf.SERIES[0]                    # 분사될 기체 경계
DASH = (0, (3, 2))
OUTLINE = dict(fc="none", ec=lf.INK, lw=1.1)


def can(ax, x0, y0=0.0, w=1.0, h=1.9, liq=0.8):
    """캔 몸통, 어깨, 노즐을 그린다. 액체 높이는 liq."""
    ax.add_patch(Rectangle((x0, y0), w, liq, fc=LIQUID, ec="none"))
    ax.add_patch(Rectangle((x0, y0), w, h, **OUTLINE))
    ax.add_patch(Polygon([(x0, y0 + h), (x0 + 0.12 * w, y0 + h + 0.22), (x0 + 0.88 * w, y0 + h + 0.22), (x0 + w, y0 + h)],
                         closed=False, **OUTLINE))
    ax.add_patch(Rectangle((x0 + 0.38 * w, y0 + h + 0.22), 0.24 * w, 0.1, fc="white", ec=lf.INK, lw=1.1))


def bubbles(ax, x0, w, y0, y1, rows, seed):
    """기체 분자를 나타내는 작은 원."""
    rnd = random.Random(seed)
    for i in range(rows):
        y = y0 + (i + 0.5) * (y1 - y0) / rows
        for j in range(4):
            x = x0 + (j + 0.5) * w / 4 + rnd.uniform(-0.05, 0.05) * w
            ax.add_patch(Circle((x, y + rnd.uniform(-0.03, 0.03)), 0.045 * w, fc="white", ec=GAS, lw=0.8))


def boundary(ax, x, y, w, h, color):
    ax.add_patch(Rectangle((x, y), w, h, fc="none", ec=color, lw=1.5, ls=DASH))


def lead(color=lf.INK):
    return dict(arrowstyle="-", lw=0.8, color=color)


# ---------------------------------------------------------------- system_boundary
def system_boundary():
    fig, ax = lf.canvas(3.9, (-0.2, 6.2), (-0.55, 2.3))
    w, liq, h = 1.0, 0.8, 1.9

    xa = 1.5                                                    # (a) 분사 전
    can(ax, xa)
    ax.text(xa + w / 2, liq / 2, "R-134a\n액체", ha="center", va="center", fontsize=8)
    mid = liq + 0.55 * (h - liq)
    bubbles(ax, xa, w, liq, mid, 3, seed=1)
    bubbles(ax, xa, w, mid, h, 2, seed=2)
    boundary(ax, xa + 0.03, liq + 0.02, w - 0.06, mid - liq - 0.03, SYSTEM)
    boundary(ax, xa + 0.03, mid + 0.02, w - 0.06, h - mid - 0.05, GAS)
    lf.note(ax, "분사될 기체", (xa - 0.02, (mid + h) / 2), (xa - 0.28, (mid + h) / 2), ha="right", arrowprops=lead(GAS))
    lf.note(ax, "계\n(캔에 남는 기체)", (xa - 0.02, (liq + mid) / 2), (xa - 0.28, (liq + mid) / 2), ha="right",
            arrowprops=lead(SYSTEM))
    ax.text(xa + w / 2, -0.12, "(a) 분사 전", ha="center", va="top")

    ax.add_patch(FancyArrowPatch((2.78, 1.45), (3.5, 1.45), arrowstyle="-|>", mutation_scale=11, lw=1.1, color=lf.INK))
    ax.text(3.14, 1.58, "분사", ha="center", va="bottom", fontsize=lf.SMALL)

    xb = 3.78                                                   # (b) 분사 후
    can(ax, xb)
    ax.text(xb + w / 2, liq / 2, "R-134a\n액체", ha="center", va="center", fontsize=8)
    bubbles(ax, xb, w, liq, h, 3, seed=3)
    boundary(ax, xb + 0.03, liq + 0.02, w - 0.06, h - liq - 0.05, SYSTEM)
    lf.note(ax, "계가 팽창해\n기체 부피\n$V_g$를 채움", (xb + w + 0.02, (liq + h) / 2), (xb + w + 0.25, (liq + h) / 2),
            arrowprops=lead(SYSTEM))
    ax.text(xb + w / 2, -0.12, "(b) 분사 후", ha="center", va="top")
    lf.save(fig, OUT / "system_boundary.png")


# ---------------------------------------------------------------- apparatus
def apparatus():
    fig, ax = lf.canvas(2.9, (-1.15, 4.5), (-0.5, 2.95))
    # 전자저울
    ax.add_patch(FancyBboxPatch((0.2, 0.0), 1.9, 0.28, boxstyle="round,pad=0.02", fc="#F2F2F2", ec=lf.INK, lw=1.0))
    ax.add_patch(Rectangle((0.95, 0.06), 0.55, 0.15, fc="#E3E9E0", ec=lf.INK, lw=0.6))
    ax.text(1.225, 0.135, "g", ha="center", va="center", fontsize=6.5)
    # 캔
    x0, base, w, h, liq = 0.6, 0.3, 1.0, 2.0, 0.85
    can(ax, x0, base, w, h, liq)
    ax.text(x0 + w / 2, base + liq / 2, "액체", ha="center", va="center", fontsize=8)
    ax.text(x0 + w / 2, base + liq + 0.45, "기체", ha="center", va="center", fontsize=8)
    # RTD (검정)와 캡톤 테이프 (노랑), 캔 오른쪽 위
    ry = base + h - 0.32
    ax.add_patch(Rectangle((x0 + w - 0.02, ry - 0.2), 0.07, 0.4, fc="#E8B400", ec="none"))
    ax.add_patch(Rectangle((x0 + w + 0.02, ry - 0.08), 0.06, 0.16, fc=lf.INK, ec="none"))
    # 전선 두 가닥
    ax.plot([x0 + w + 0.08, 2.2, 3.3], [ry + 0.04, ry + 0.04, 1.30], color=SYSTEM, lw=1.0)
    ax.plot([x0 + w + 0.08, 2.2, 3.3], [ry - 0.04, ry - 0.04, 1.18], color=lf.INK, lw=1.0)
    # 멀티미터
    ax.add_patch(FancyBboxPatch((3.3, 0.55), 0.95, 1.35, boxstyle="round,pad=0.03", fc="#F4C27A", ec=lf.INK, lw=1.0))
    ax.add_patch(Rectangle((3.42, 1.4), 0.71, 0.35, fc="#E3E9E0", ec=lf.INK, lw=0.7))
    ax.text(3.775, 1.575, "Ω", ha="center", va="center")
    ax.add_patch(Circle((3.775, 0.95), 0.2, fc="#4A4A4A", ec=lf.INK, lw=0.7))
    # 이름
    lf.note(ax, "PT100 RTD\n(캡톤 테이프로 부착)", (x0 + w + 0.05, ry + 0.2), (1.85, 2.68), arrowprops=lead())
    lf.note(ax, "먼지제거제\n(R-134a)", (x0, base + 1.2), (-1.1, base + 1.5), arrowprops=lead())
    ax.text(3.775, 0.4, "멀티미터\n(저항 모드)", ha="center", va="top", fontsize=lf.SMALL)
    ax.text(1.15, -0.1, "전자저울", ha="center", va="top", fontsize=lf.SMALL)
    lf.save(fig, OUT / "apparatus.png")


system_boundary()
apparatus()
