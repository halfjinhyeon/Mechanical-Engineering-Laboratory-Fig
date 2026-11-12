"""labfig: 기계공학실험 보고서용 matplotlib Figure 스타일.

Word 보고서(본문 10 pt, Arial과 맑은 고딕)에 넣을 실험 그래프를 같은 규칙으로 그리기 위한 모듈.
필요한 것: Python 3.10 이상, matplotlib 3.6 이상, numpy. 사진 패널을 쓸 때만 Pillow.

사용법 (각 보고서의 그림 스크립트 맨 위. 폴더 구조가 다르면 labfig.py가 있는 곳을 sys.path에 넣는다):

    import sys
    from pathlib import Path
    ROOT = next(p for p in Path(__file__).resolve().parents if (p / "공통" / "labfig").exists())
    sys.path.insert(0, str(ROOT / "공통" / "labfig"))
    import labfig as lf

    lf.use()                                   # 스타일 적용 (한 번만)
    fig, ax = lf.figure("single")              # 폭 프리셋은 WIDTHS 참고
    lf.points(ax, x, y, yerr=u, label="Measured")          # 이산 측정값: 마커와 오차 막대
    fit = lf.linfit(ax, x, y, label="Linear fit")          # 회귀선을 그리고 기울기, 절편, R2를 돌려준다
    lf.legend(ax)                                          # 측정값, 곡선, 이론선 순서로 정리한 범례
    lf.save(fig, Path(__file__).parent / "fig1-1.png")     # 600 dpi PNG, 지정한 폭 그대로

규칙:
  1. 글꼴은 Arial, 한글은 맑은 고딕으로 자동 대체된다 (본문 규칙과 같다). 기본 9 pt.
  2. 그림은 Word에 넣을 폭으로 처음부터 그린다. 저장한 그림은 지정한 폭과 정확히 같으므로
     원래 크기로 넣으면 글자가 9 pt로 보인다. 넣은 뒤에 줄이거나 늘리지 않는다.
     build 스크립트에서는 add_picture(path, width=Inches(lf.WIDTHS["wide"]))처럼 같은 폭을 쓴다.
  3. 역할마다 그리는 방법을 고정한다.
       points  이산 측정값. 속이 빈 마커, 계열마다 모양이 다르다.
       trace   촘촘하게 샘플링한 측정 곡선. 실선에서 시작해 계열마다 선 모양이 다르다.
       model   이론값, 모델, 회귀선. 가는 점선. 기본은 검정, series를 주면 그 계열 색.
     색과 모양이 함께 바뀌므로 흑백 인쇄에서도 계열이 구분된다.
  4. 계열 색은 SERIES 순서대로만 쓴다 (최대 5개). 더 많으면 패널을 나눈다.
  5. 축 범위는 물리량 기준으로 정하고 (가능하면 0 포함), 축 이름에는 항상 단위를 적는다.
     y축을 두 개 쓰지 않는다. 단위가 다른 두 양은 패널을 나눈다.

색 검증: SERIES는 흰 배경 기준으로 색각 이상 시뮬레이션 색차, 일반 시야 색차, 3:1 대비를
확인한 값이다. 앞의 4색은 모든 쌍이 통과하고, 5번째 보라는 파랑과의 색각 이상 색차가
경고 구간이라 마커와 선 모양 구분에 의존한다. 색을 바꾸면 다시 검증해야 한다.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ------------------------------------------------------------------ 상수
# Word에 넣는 폭 (inch). A4, 좌우 여백 0.75 in, 문항 상자 안쪽 폭 약 6.4 in 기준.
#   full   상자를 꽉 채우는 폭. 패널 3개 이상
#   wide   패널 2개짜리 그림의 기본 폭
#   single 패널 1개짜리 그림의 기본 폭
#   half   두 그림을 나란히 놓을 때
WIDTHS = {"full": 6.3, "wide": 5.0, "single": 3.6, "half": 3.1}

INK = "#1A1A1A"        # 글자, 축, 이론선
GRAY = "#8C8C8C"       # 보조선, 구간 음영
SERIES = ("#0072B2", "#D55E00", "#009E73", "#902018", "#AA4499")   # 파랑, 주황, 초록, 진빨강, 보라
MARKERS = ("o", "s", "^", "D", "v")
_MS = {"o": 4.6, "s": 4.2, "^": 5.0, "D": 3.9, "v": 5.0}            # 모양별로 눈에 보이는 크기를 맞춘다
DASHES = ("-", (0, (5, 1.8)), (0, (5, 1.6, 1.2, 1.6)), (0, (1.2, 1.4)), (0, (8, 2, 1.2, 2, 1.2, 2)))
MODEL_DASH = (0, (3.5, 2))
LEAD = dict(arrowstyle="-", lw=0.6, color=INK, shrinkA=1, shrinkB=3)   # 주석 지시선
SMALL = 8.5            # 범례, 주석 글자 크기


def use(font_size: float = 9.0, latin: str = "Arial", korean: str = "Malgun Gothic",
        agg: bool = True) -> None:
    """공통 스타일을 적용한다. 스크립트마다 그림을 만들기 전에 한 번 부른다.

    latin과 korean은 글꼴 이름. Windows가 아니면 설치된 글꼴로 바꾼다
    (예: macOS는 latin="Helvetica", korean="Apple SD Gothic Neo").
    """
    if agg:
        matplotlib.use("Agg")
    plt.rcParams.update({
        # 글꼴: 영문 글꼴에 없는 글자(한글)는 한글 글꼴에서 가져온다
        "font.family": [latin, korean],
        "font.size": font_size,
        "axes.labelsize": font_size + 0.5,
        "axes.titlesize": font_size + 0.5,
        "xtick.labelsize": font_size,
        "ytick.labelsize": font_size,
        "legend.fontsize": SMALL,
        "mathtext.fontset": "custom",
        "mathtext.rm": latin,
        "mathtext.it": f"{latin}:italic",
        "mathtext.bf": f"{latin}:bold",
        "mathtext.fallback": "stixsans",
        # 색
        "text.color": INK,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.prop_cycle": plt.cycler(color=SERIES),
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        # 축과 눈금
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlelocation": "left",
        "axes.titlepad": 5,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        # 선과 마커
        "lines.linewidth": 1.4,
        "lines.markersize": 4.6,
        # 범례
        "legend.frameon": False,
        "legend.handlelength": 2.4,
        "legend.labelspacing": 0.3,
        "legend.borderaxespad": 0.3,
        # 저장
        "savefig.dpi": 600,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    _hangul_in_mathtext(korean)


_KOREAN_FONT_PATH = None      # 수식 렌더러가 한글을 가져올 글꼴 파일


def _hangul_in_mathtext(korean: str) -> None:
    """한글과 수식이 한 문자열에 섞여도 한글이 나오게 한다 (예: r"변위 $\\delta$ (mm)").

    matplotlib은 "$...$"가 들어간 문자열 전체를 수식 렌더러로 그리는데, 수식 렌더러는
    글꼴 대체를 하지 않아 영문 글꼴에 없는 한글이 깨진다. 한글 글자만 한글 글꼴에서 가져오도록
    글리프 조회를 보완한다. matplotlib 내부 구조에 기대는 부분이라 실패하면 경고만 낸다.
    """
    global _KOREAN_FONT_PATH
    try:
        from matplotlib import _mathtext, font_manager

        _KOREAN_FONT_PATH = font_manager.findfont(korean, fallback_to_default=False)
        cls = _mathtext.UnicodeFonts
        if getattr(cls, "_labfig_hangul", False):
            return
        original = cls._get_glyph

        def _get_glyph(self, fontname, font_class, sym):
            if len(sym) == 1:
                code = ord(sym)
                if 0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F:
                    font = self._get_font(_KOREAN_FONT_PATH)
                    if font is not None and font.get_char_index(code):
                        return font, code, False
            return original(self, fontname, font_class, sym)

        cls._get_glyph = _get_glyph
        cls._labfig_hangul = True
    except Exception as exc:                # 글꼴이 없거나 내부 구조가 바뀐 matplotlib 버전
        import warnings

        warnings.warn(f"labfig: 한글과 수식을 한 문자열에 섞으면 한글이 깨질 수 있다 ({exc}).")


def color(series: int) -> str:
    """계열 번호(0부터)의 색. 5개를 넘기면 색을 되풀이하지 않고 오류를 낸다."""
    if not 0 <= series < len(SERIES):
        raise ValueError(f"계열은 한 축에 {len(SERIES)}개까지만 쓴다 (series={series}). 패널을 나눠서 그린다.")
    return SERIES[series]


# ------------------------------------------------------------------ 그림 만들기와 저장
def figure(width: str | float = "full", height: float | None = None, nrows: int = 1, ncols: int = 1, **kw):
    """보고서 폭에 맞춘 그림을 만든다. (fig, ax) 또는 (fig, axes 배열)을 돌려준다.

    width는 프리셋 이름("full", "wide", "single", "half")이나 inch 값.
    height를 생략하면 패널 비율로 정한다.
    """
    w = WIDTHS[width] if isinstance(width, str) else float(width)
    if height is None:
        height = min(w / ncols * 0.8, 3.0) * nrows
    kw.setdefault("layout", "constrained")
    return plt.subplots(nrows, ncols, figsize=(w, height), **kw)


def save(fig, path, dpi: int = 600, tight: bool = False, close: bool = True) -> Path:
    """PNG(또는 확장자에 맞는 형식)로 저장한다.

    기본은 figure()에서 정한 크기 그대로 저장한다. tight=True는 여백을 잘라내므로
    축이 없는 개념도나 사진처럼 폭이 정확할 필요가 없는 그림에만 쓴다.
    사진이 들어간 그림은 dpi=300이면 충분하다.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    extra = dict(bbox_inches="tight", pad_inches=0.03) if tight else {}
    fig.savefig(path, dpi=dpi, **extra)
    w, h = fig.get_size_inches()
    if close:
        plt.close(fig)
    print(f"saved {path}  ({'tight' if tight else f'{w:.2f} x {h:.2f} in'}, {dpi} dpi)")
    return path


# ------------------------------------------------------------------ 역할별 그리기
def points(ax, x, y, yerr=None, xerr=None, label=None, series: int = 0, filled: bool = False, **kw):
    """이산 측정값. 마커만 찍고, yerr나 xerr를 주면 오차 막대를 함께 그린다."""
    c, m = color(series), MARKERS[series]
    style = dict(fmt=m, ms=_MS[m], mfc=c if filled else "white", mec=c, mew=1.1,
                 ecolor=c, elinewidth=0.8, capsize=2, capthick=0.8, label=label, zorder=3)
    style.update(kw)
    return ax.errorbar(x, y, yerr=yerr, xerr=xerr, **style)


def trace(ax, x, y, label=None, series: int = 0, **kw):
    """촘촘하게 샘플링한 측정 곡선 (DAQ 신호, 응력-변형률 곡선 등). 계열마다 선 모양이 다르다."""
    style = dict(color=color(series), lw=1.4, ls=DASHES[series], label=label, zorder=2.5)
    style.update(kw)
    (line,) = ax.plot(x, y, **style)
    return line


def model(ax, x, y, label=None, series: int | None = None, **kw):
    """이론값, 모델, 회귀선. 가는 점선. series를 주면 그 계열의 색으로 그린다."""
    style = dict(color=INK if series is None else color(series), lw=1.0, ls=MODEL_DASH,
                 label=label, zorder=2.8)                    # 측정 곡선 위, 마커 아래
    style.update(kw)
    (line,) = ax.plot(x, y, **style)
    line._labfig_role = "model"
    return line


def legend(ax, **kw):
    """범례를 측정값(마커), 측정 곡선, 이론선 순서로 정리해서 단다. 인자는 ax.legend와 같다."""
    handles, labels = ax.get_legend_handles_labels()

    def rank(h):
        if getattr(h, "_labfig_role", None) == "model":
            return 2
        return 0 if isinstance(h, matplotlib.container.ErrorbarContainer) else 1

    order = sorted(range(len(handles)), key=lambda i: rank(handles[i]))     # 같은 역할끼리는 그린 순서
    return ax.legend([handles[i] for i in order], [labels[i] for i in order], **kw)


class Fit(NamedTuple):
    slope: float
    intercept: float
    r2: float
    slope_se: float        # 기울기의 표준오차
    intercept_se: float    # 절편의 표준오차
    n: int


def linfit(ax, x, y, through_origin: bool = False, span=None, label=None,
           series: int | None = None, **kw) -> Fit:
    """최소제곱 직선 회귀를 하고 model() 모양으로 그린다. ax=None이면 계산만 한다.

    span=(x0, x1)은 직선을 그릴 범위 (기본은 데이터 범위).
    through_origin=True는 y = a x로 맞춘다. 이때 R2는 평균 기준 총제곱합으로 계산한다.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = x.size
    if through_origin:
        sxx = float(np.sum(x * x))
        slope, intercept, dof = float(np.sum(x * y) / sxx), 0.0, n - 1
    else:
        xm, ym = x.mean(), y.mean()
        sxx = float(np.sum((x - xm) ** 2))
        slope = float(np.sum((x - xm) * (y - ym)) / sxx)
        intercept, dof = float(ym - slope * xm), n - 2
    ss_res = float(np.sum((y - (slope * x + intercept)) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    s2 = ss_res / dof if dof > 0 else float("nan")
    slope_se = float(np.sqrt(s2 / sxx))
    intercept_se = 0.0 if through_origin else float(np.sqrt(s2 * (1 / n + x.mean() ** 2 / sxx)))
    fit = Fit(slope, intercept, 1 - ss_res / ss_tot, slope_se, intercept_se, n)
    if ax is not None:
        xs = np.array(span if span is not None else (x.min(), x.max()), float)
        model(ax, xs, slope * xs + intercept, label=label, series=series, **kw)
    return fit


# ------------------------------------------------------------------ 주석과 꾸밈
def note(ax, text, xy, xytext=None, **kw):
    """주석. xytext를 주면 xy에서 가는 지시선을 끌어 그 자리에 글자를 쓴다."""
    if xytext is None:
        style = dict(fontsize=SMALL, va="center")
        style.update(kw)
        return ax.text(xy[0], xy[1], text, **style)
    style = dict(fontsize=SMALL, va="center", arrowprops=dict(LEAD))
    style.update(kw)
    return ax.annotate(text, xy=xy, xytext=xytext, **style)


def mark(ax, x, y, series: int | None = None, cross: bool = False, **kw):
    """특성점 하나를 표시한다. 기본은 속이 빈 원 (항복점, 최대점), cross=True는 X (파단점)."""
    c = INK if series is None else color(series)
    if cross:
        style = dict(marker="x", ms=6, mew=1.3, color=c, ls="none", zorder=5)
    else:
        style = dict(marker="o", ms=5, mfc="white", mec=c, mew=1.1, ls="none", zorder=5)
    style.update(kw)
    (line,) = ax.plot([x], [y], **style)
    return line


def region(ax, x0, x1, text=None, alpha: float = 0.14, y: float = 0.97, **text_kw):
    """x0에서 x1까지를 옅게 칠하고 이름을 쓴다 (탄성 구간, 가열 구간 등).

    y는 글자의 세로 위치 (축 높이에 대한 비율, 기본은 위쪽). 나머지 인자는 글자 설정으로 넘어간다.
    """
    ax.axvspan(x0, x1, color=GRAY, alpha=alpha, lw=0, zorder=0)
    if text:
        style = dict(fontsize=SMALL, ha="center", va="top")
        style.update(text_kw)
        ax.text((x0 + x1) / 2, y, text, transform=ax.get_xaxis_transform(), **style)


def panel(ax, text: str) -> None:
    """패널 제목. "(a) ..." 형식으로 왼쪽 위에 쓴다."""
    ax.set_title(text, loc="left")


def plain_ticks(axis, decimals: int) -> None:
    """눈금을 고정 소수 자리로 쓰되 0은 "0"으로 쓴다. 예: lf.plain_ticks(ax.xaxis, 3)."""
    axis.set_major_formatter(mticker.FuncFormatter(lambda v, _: "0" if v == 0 else f"{v:.{decimals}f}"))


def photos(images, titles=None, width: str | float = "wide", height: float = 2.0, crops=None):
    """사진을 한 줄로 나란히 놓은 그림을 만든다. fig를 돌려준다.

    images는 파일 경로나 PIL 이미지의 목록. crops는 사진마다 (왼, 위, 오른, 아래) 비율 상자나 None.
    패널 폭은 사진의 가로세로비에 맞춘다. 저장할 때는 lf.save(fig, path, dpi=300)이면 충분하다.
    """
    ims = [load_photo(src, crops[i] if crops else None) for i, src in enumerate(images)]
    fig, axes = figure(width, height, ncols=len(ims), squeeze=False,
                       width_ratios=[im.size[0] / im.size[1] for im in ims])
    for i, im in enumerate(ims):
        photo(axes[0, i], im, titles[i] if titles else None)
    return fig


def load_photo(src, crop=None):
    """사진을 읽는다 (휴대폰 사진의 회전 정보 반영). crop은 (왼, 위, 오른, 아래) 비율 상자."""
    from PIL import Image, ImageOps

    im = src if isinstance(src, Image.Image) else ImageOps.exif_transpose(Image.open(src))
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    return im


def photo(ax, src, title=None, crop=None):
    """축 하나에 사진을 넣는다. 그래프 패널과 사진 패널을 한 그림에 섞을 때 쓴다."""
    im = load_photo(src, crop)
    ax.imshow(im)
    ax.set_axis_off()
    if title:
        panel(ax, title)
    return im
