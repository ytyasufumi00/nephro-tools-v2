import math
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager


def _setup_japanese_font():
    """回路図(matplotlib)で日本語ラベルが文字化けしないよう、利用可能なCJKフォントを探して設定する。
    見つからない場合は何もしない(デフォルトフォントのまま、文字が欠落表示される可能性がある)。"""
    candidates = [
        "Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic", "Meiryo",
        "MS Gothic", "Hiragino Sans", "IPAexGothic", "TakaoGothic",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            matplotlib.rcParams["font.family"] = name
            return


_setup_japanese_font()

# ==========================================
# 0. 物質プリセット (教育用の簡略化された代表値)
# ==========================================
# free_frac: 遊離型分率 (1 - 蛋白結合率)
# v1_per_kg / v2_per_kg: 2-コンパートメントモデルの中心室(V1)・末梢室(V2) (L/kg)
# qic: 組織間移行クリアランス (L/min) ※既存ツール(VCM TDM Sim / Overdose Sim)の慣例にあわせ、
#      体重に比例させず絶対値として扱う簡略化モデル
SUBSTANCES = {
    "尿素窒素 (BUN)": {
        "mw": 60, "free_frac": 1.00,
        "v1_per_kg": 0.50, "v2_per_kg": 0.10, "qic": 0.30,
        "note": "分子量が小さく蛋白結合もないため、膜はほぼ自由に通過する。組織間移行も速く、"
                "ほぼ1コンパートメントのように振る舞う代表例。",
    },
    "カリウム (K+)": {
        "mw": 39, "free_frac": 1.00,
        "v1_per_kg": 0.07, "v2_per_kg": 0.43, "qic": 0.012,
        "note": "イオンなので膜は自由に通過する（ふるい係数は尿素と同等）。しかし体内カリウムの"
                "大半は細胞内(V2)にあり、Na/K-ATPaseを介した細胞膜輸送でしか移動できないため、"
                "組織間移行(再分布)が尿素よりかなり遅い。膜の通しやすさは同じでも、24時間除去率は"
                "尿素より明確に低くなる(リバウンドが起きやすい)よう設定している。",
    },
    "バンコマイシン (VCM)": {
        "mw": 1485, "free_frac": 0.50,
        "v1_per_kg": 0.25, "v2_per_kg": 0.65, "qic": 0.15,
        "note": "中分子量・蛋白結合約50%。本アプリ内「VCM TDM Simulator」と同一のPKパラメータ"
                "(V1=0.25, V2=0.65 L/kg, Q=0.15 L/min)を採用し、ツール間で一貫させている。",
    },
    "クレアチンキナーゼ (CK)": {
        "mw": 86000, "free_frac": 1.00,
        "v1_per_kg": 0.07, "v2_per_kg": 0.03, "qic": 0.02,
        "note": "分子量が大きく、標準的な血液濾過膜のカットオフ(約3万Da)を大きく超えるため、"
                "ふるい係数はほぼ0。横紋筋融解症の管理でCHDFそのものによるCK低下は期待せず、"
                "輸液・原疾患治療を優先する。",
    },
    "アシクロビル (ACV)": {
        "mw": 225, "free_frac": 0.85,
        "v1_per_kg": 0.15, "v2_per_kg": 0.55, "qic": 0.20,
        "note": "水溶性の小分子で蛋白結合率は低い。本アプリ内「Overdose Simulation」の腎不全時"
                "PKパラメータ(V1=0.15, V2=0.55 L/kg, Q=0.2 L/min)と一貫させている。",
    },
}

MW_REF = 60.0  # 尿素を基準分子量とする
MEMBRANE_CUTOFF = 30000.0  # 標準的な高flux膜のカットオフ目安 (Da)


# ==========================================
# 1. 計算ロジック
# ==========================================
def pore_factor(mw, cutoff=MEMBRANE_CUTOFF, n=4):
    """膜のサイズ排除（カットオフ）による通過率 (0~1)。カットオフ付近で急峻に低下する。"""
    return 1.0 / (1.0 + (mw / cutoff) ** n)


def calc_sieving(mw, free_frac):
    """
    拡散ふるい係数 Sd と 濾過(対流)ふるい係数 Sc を分子量・蛋白結合から推定する簡略モデル。
    - 拡散: 分子の拡散速度は分子量が大きいほど低下する(目安として MW^-0.5 に比例)。
    - 対流: 溶媒(血漿水)に乗って膜を通過するため、カットオフに近づくまでMW依存性は小さい。
    """
    pf = pore_factor(mw)
    sd = free_frac * min(1.0, math.sqrt(MW_REF / mw)) * pf
    sc = free_frac * pf
    return sd, sc


def calc_clearance(qb_ml_min, qd_ml_h, qf_ml_h, qs_ml_h, ht_pct, sd, sc, dilution_mode):
    """CHDFの拡散・濾過(対流)クリアランスを effluent-rate 近似(CL = Q × S)で計算し、
    QB(血漿流量)で上限をキャップする。前希釈の場合は補充液による希釈効果を反映する。"""
    qb_l = qb_ml_min / 1000.0
    qd_l = qd_ml_h / 1000.0 / 60.0
    qf_l = qf_ml_h / 1000.0 / 60.0
    qs_l = qs_ml_h / 1000.0 / 60.0

    qb_plasma = qb_l * (1.0 - ht_pct / 100.0)

    if dilution_mode == "前希釈 (Pre-dilution)":
        dilution_factor = qb_plasma / (qb_plasma + qs_l) if (qb_plasma + qs_l) > 0 else 1.0
    else:
        dilution_factor = 1.0

    cl_d = qd_l * sd
    cl_c = qf_l * sc * dilution_factor
    cl_raw = cl_d + cl_c
    cl_total = min(cl_raw, qb_plasma) if qb_plasma > 0 else 0.0
    capped = cl_raw > qb_plasma + 1e-9

    return {
        "qb_plasma": qb_plasma,
        "dilution_factor": dilution_factor,
        "cl_d": cl_d,
        "cl_c": cl_c,
        "cl_raw": cl_raw,
        "cl_total": cl_total,
        "capped": capped,
    }


def simulate_removal_pct(weight, v1_per_kg, v2_per_kg, qic, cl_total_l_min, hours=24.0, dt=1.0):
    """
    2-コンパートメントモデルで CL_total を24時間持続適用した場合の、体内総量に対する除去率(%)を計算する。
    t=0において V1, V2 は同一濃度(平衡状態)にあると仮定し、産生・摂取は考慮しない
    (「今ある量のうち何%が24時間で抜けるか」を見るための単純化)。
    """
    v1 = v1_per_kg * weight
    v2 = v2_per_kg * weight
    k12 = qic / v1
    k21 = qic / v2

    a1 = v1  # 濃度=1.0 とおいた初期量
    a2 = v2
    total0 = a1 + a2

    steps = int(hours * 60.0 / dt)
    for _ in range(steps):
        trans = (k12 * a1 - k21 * a2) * dt
        removal = (cl_total_l_min * (a1 / v1)) * dt
        a1 = a1 - trans - removal
        a2 = a2 + trans
        if a1 < 0:
            a1 = 0.0
        if a2 < 0:
            a2 = 0.0

    total_t = a1 + a2
    pct = (total0 - total_t) / total0 * 100.0
    return pct, v1, v2, k12, k21


def draw_chdf_circuit(qb, qd, qf, qs, dilution_mode):
    """CHDF回路の概念図(matplotlibによる簡易スキーマ)。研修医が血液・透析液・濾液・補充液の
    流れを一目で把握できるよう、現在の流量値をそのまま描き込む。"""
    fig, ax = plt.subplots(figsize=(8, 7.0))
    ax.set_xlim(0, 11)
    ax.set_ylim(-2.6, 9.0)
    ax.axis("off")

    # 患者
    ax.add_patch(patches.FancyBboxPatch((0.3, 3.2), 1.8, 2.2, boxstyle="round,pad=0.05",
                                         fc="#bcd6f0", ec="#2266aa", lw=2))
    ax.text(1.2, 4.3, "患者", ha="center", va="center", fontsize=14, fontweight="bold")

    # 血液ポンプ
    pump_xy = (3.6, 5.3)
    ax.add_patch(patches.Circle(pump_xy, 0.35, fc="#f3c623", ec="#a67c00", lw=2))
    ax.text(*pump_xy, "P", ha="center", va="center", fontsize=12, fontweight="bold")

    # ヘモフィルター
    ax.add_patch(patches.FancyBboxPatch((6.0, 1.6), 1.2, 4.6, boxstyle="round,pad=0.03",
                                         fc="#e4ebf2", ec="#555555", lw=2))
    ax.text(6.6, 3.9, "ヘモ\nフィルター", ha="center", va="center", fontsize=9)

    # 排液バッグ
    ax.add_patch(patches.FancyBboxPatch((8.6, 5.0), 2.0, 1.4, boxstyle="round,pad=0.05",
                                         fc="#e6e6e6", ec="#777777", lw=2))
    ax.text(9.6, 5.7, "排液バッグ", ha="center", va="center", fontsize=9, fontweight="bold")

    blood = dict(arrowstyle="-|>", color="#c1121f", lw=2.4)
    # 患者 -> ポンプ -> フィルター上部(流入)
    ax.annotate("", xy=pump_xy, xytext=(2.1, 5.0), arrowprops=blood)
    ax.annotate("", xy=(6.0, 6.0), xytext=(3.95, 5.45), arrowprops=blood)
    ax.text(4.6, 4.5, f"QB\n{qb:.0f} mL/min", color="#c1121f", fontsize=8.5, ha="center", fontweight="bold")

    # フィルター下部(流出) -> 患者(返血)
    ax.annotate("", xy=(2.1, 3.6), xytext=(6.0, 2.0), arrowprops=blood)

    # 補充液 (前希釈 / 後希釈)
    repl_arrow = dict(arrowstyle="-|>", color="#2d6a4f", lw=2.2, linestyle="--")
    if dilution_mode == "前希釈 (Pre-dilution)":
        repl_box_xy, join_xy, label_xy = (4.6, 7.3), (4.9, 5.68), (5.3, 8.3)
    else:
        repl_box_xy, join_xy, label_xy = (4.6, -1.6), (4.9, 2.45), (5.3, -2.1)

    ax.add_patch(patches.FancyBboxPatch((repl_box_xy[0], repl_box_xy[1]), 1.4, 0.8, boxstyle="round,pad=0.05",
                                         fc="#d8f3dc", ec="#2d6a4f", lw=2))
    ax.text(repl_box_xy[0] + 0.7, repl_box_xy[1] + 0.4, "補充液", ha="center", va="center",
            fontsize=9, fontweight="bold")
    box_edge_y = repl_box_xy[1] if dilution_mode == "前希釈 (Pre-dilution)" else repl_box_xy[1] + 0.8
    ax.annotate("", xy=join_xy, xytext=(4.9, box_edge_y), arrowprops=repl_arrow)
    ax.text(*label_xy, f"補充液 QS\n{qs:.0f} mL/h", color="#2d6a4f", fontsize=8.5, ha="center", fontweight="bold")

    # 透析液 (向流)
    dia_arrow = dict(arrowstyle="-|>", color="#1d4e89", lw=2.2)
    ax.annotate("", xy=(7.0, 2.1), xytext=(8.3, 0.7), arrowprops=dia_arrow)
    ax.text(8.5, 0.3, f"透析液 QD\n{qd:.0f} mL/h", color="#1d4e89", fontsize=8.5, ha="center", fontweight="bold")

    # 濾液 -> 排液バッグ
    filtrate_arrow = dict(arrowstyle="-|>", color="#6c757d", lw=2.2)
    ax.annotate("", xy=(8.55, 5.6), xytext=(7.25, 5.6), arrowprops=filtrate_arrow)
    ax.text(7.9, 6.1, f"濾液 QF\n{qf:.0f} mL/h", color="#6c757d", fontsize=8.5, ha="center", fontweight="bold")

    fig.tight_layout()
    return fig


# ==========================================
# 2. ページ設定
# ==========================================
st.set_page_config(page_title="CHDF Simulator 信州上田医療センター腎臓内科", layout="wide")

st.markdown("""
    <style>
    @media (max-width: 600px) {
        h1 { font-size: 1.6rem !important; padding-bottom: 0.5rem !important; }
        h2 { font-size: 1.4rem !important; padding-top: 0.5rem !important; }
        h3 { font-size: 1.2rem !important; }
        p, .stMarkdown { font-size: 0.95rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🩸 CHDF シミュレーター (研修医教育用)\n💡流量設定と除去物質％の関係を体感する")

# ==========================================
# 3. サイドバー：入力
# ==========================================
with st.sidebar:
    st.header("1. 患者情報")
    weight = st.number_input("体重 (kg)", 20.0, 150.0, 60.0, 0.5)

    st.header("2. 目標除去物質")
    substance_name = st.selectbox("対象物質", list(SUBSTANCES.keys()))
    sub = SUBSTANCES[substance_name]
    st.caption(f"MW {sub['mw']:,} Da ／ 遊離型分率 {sub['free_frac']*100:.0f}%")
    st.caption(sub["note"])

    st.header("3. 流量設定 (CHDF条件)")
    with st.expander("⚙️ 血液浄化条件", expanded=True):
        qb = st.number_input("血流量 QB (mL/min)", 50.0, 300.0, 100.0, 10.0)
        qd = st.number_input("透析液流量 QD (mL/h)", 0.0, 2000.0, 600.0, 50.0)
        qf = st.number_input("濾液流量 QF (mL/h)", 0.0, 2500.0, 800.0, 50.0)
        qs = st.number_input("補充液流量 QS (mL/h)", 0.0, 2000.0, 200.0, 50.0)
        if qs > qf:
            st.warning("⚠️ 補充液(QS)が濾液(QF)を上回っています。通常は QS ≤ QF で設定します。")

    with st.expander("🔧 詳細設定 (上級者向け)", expanded=False):
        ht_pct = st.slider("ヘマトクリット Ht (%)", 10.0, 60.0, 30.0, 1.0,
                            help="血漿流量(QB×(1-Ht))の算出に使用。CHDFのクリアランスはこの血漿流量で上限が決まる。")
        dilution_mode = st.radio("補充液の希釈方式", ["前希釈 (Pre-dilution)", "後希釈 (Post-dilution)"], index=0,
                                  help="前希釈はフィルター手前で血液を希釈し凝固を防ぐが、希釈分だけ濾過効率が下がる。"
                                       "後希釈は効率が良いが濾過率(filtration fraction)が高くなり凝固リスクが上がる。")
        st.markdown("---")
        st.caption("2-コンパートメントPKパラメータ（物質ごとにプリセット。必要に応じ上書き可）")
        v1_pk = st.number_input("V1 中心室 (L/kg)", 0.01, 2.0, sub["v1_per_kg"], 0.01, key=f"v1_{substance_name}")
        v2_pk = st.number_input("V2 末梢室 (L/kg)", 0.01, 2.0, sub["v2_per_kg"], 0.01, key=f"v2_{substance_name}")
        qic_pk = st.number_input("組織間移行クリアランス Q (L/min)", 0.001, 1.0, sub["qic"], 0.01, key=f"qic_{substance_name}")
        free_frac_pk = st.slider("遊離型分率 (1-蛋白結合率)", 0.0, 1.0, sub["free_frac"], 0.01, key=f"free_{substance_name}")

# ==========================================
# 4. 計算
# ==========================================
sd, sc = calc_sieving(sub["mw"], free_frac_pk)
cl = calc_clearance(qb, qd, qf, qs, ht_pct, sd, sc, dilution_mode)
pct_removed, v1, v2, k12, k21 = simulate_removal_pct(weight, v1_pk, v2_pk, qic_pk, cl["cl_total"])

# ==========================================
# 5. メインエリア：結果表示
# ==========================================
st.header("2. シミュレーション結果")

m1, m2, m3, m4 = st.columns(4)
m1.metric("🔴 血流量 QB", f"{qb:.0f} mL/min")
m2.metric("🔵 透析液流量 QD", f"{qd:.0f} mL/h")
m3.metric("⚪ 濾液流量 QF", f"{qf:.0f} mL/h")
m4.metric("🟢 補充液流量 QS", f"{qs:.0f} mL/h")

st.markdown("---")
col_res1, col_res2 = st.columns([1, 1])
with col_res1:
    st.metric(f"🎯 {substance_name} の24時間除去率", f"{pct_removed:.1f} %",
              help="体内に今ある総量のうち、24時間このCHDF条件を維持した場合に除去される割合(産生・摂取は考慮しない)。")
    if cl["capped"]:
        st.warning("⚠️ 拡散・濾過の合計クリアランスが血漿流量(QB×(1-Ht))の上限に達しています。"
                   "これ以上 QD・QF を増やしても除去率は伸びません。QBを増やす必要があります。")
with col_res2:
    st.caption("内訳 (クリアランス, mL/min)")
    st.code(
        f"拡散クリアランス  (QD×Sd)        : {cl['cl_d']*1000:6.2f}\n"
        f"濾過クリアランス  (QF×Sc×希釈率) : {cl['cl_c']*1000:6.2f}\n"
        f"合計(上限適用前)                  : {cl['cl_raw']*1000:6.2f}\n"
        f"血漿流量上限 QB×(1-Ht)            : {cl['qb_plasma']*1000:6.2f}\n"
        f"--------------------------------------------\n"
        f"実効クリアランス CL_total         : {cl['cl_total']*1000:6.2f}\n"
        f"Sd={sd:.3f} / Sc={sc:.3f} / 希釈率={cl['dilution_factor']:.3f}",
        language="text",
    )

# ==========================================
# 6. 回路図
# ==========================================
st.markdown("---")
st.subheader("🖼️ CHDF回路図と設定流量")
col_img, col_metrics = st.columns([1.2, 1])
with col_img:
    fig_circuit = draw_chdf_circuit(qb, qd, qf, qs, dilution_mode)
    st.pyplot(fig_circuit, use_container_width=True)
with col_metrics:
    st.markdown("#### ⚙️ 現在の設定")
    st.markdown(f"""
    <div style="background-color:#f0f2f6; padding:12px; border-radius:8px; font-size:0.95em;">
    <b>対象物質:</b> {substance_name}<br>
    <b>希釈方式:</b> {dilution_mode}<br>
    <b>Ht:</b> {ht_pct:.0f}%<br>
    <b>体重:</b> {weight:.0f} kg<br>
    <hr>
    <b>QB:</b> {qb:.0f} mL/min<br>
    <b>QD:</b> {qd:.0f} mL/h<br>
    <b>QF:</b> {qf:.0f} mL/h<br>
    <b>QS:</b> {qs:.0f} mL/h<br>
    <hr>
    <b>24時間除去率:</b> <span style="font-size:1.3em; color:#c1121f;"><b>{pct_removed:.1f}%</b></span>
    </div>
    """, unsafe_allow_html=True)
    eff_dose = (qd + qf) / weight if weight > 0 else 0
    st.caption(f"💡 排液量(QD+QF) ÷ 体重 = {eff_dose:.1f} mL/kg/h "
               f"(KDIGO等で目安とされる20~25 mL/kg/hと比較する習慣をつけると良い)")

# ==========================================
# 7. 流量感度チャート
# ==========================================
st.markdown("---")
st.subheader("📊 流量を変えると除去率はどう変わるか")

n_pts = 21
qd_range = np.linspace(0, 1500, n_pts)
qf_range = np.linspace(0, 2000, n_pts)

pct_vs_qd = []
for q in qd_range:
    cl_tmp = calc_clearance(qb, q, qf, qs, ht_pct, sd, sc, dilution_mode)
    p, *_ = simulate_removal_pct(weight, v1_pk, v2_pk, qic_pk, cl_tmp["cl_total"], dt=2.0)
    pct_vs_qd.append(p)

pct_vs_qf = []
for q in qf_range:
    cl_tmp = calc_clearance(qb, qd, q, qs, ht_pct, sd, sc, dilution_mode)
    p, *_ = simulate_removal_pct(weight, v1_pk, v2_pk, qic_pk, cl_tmp["cl_total"], dt=2.0)
    pct_vs_qf.append(p)

# QDとQFのグラフで縦軸(除去率%)のスケールを揃える。
# 物質によっては拡散(QD)と濾過(QF)で効き方が何倍も違うため、軸を独立に自動調整すると
# 「どちらも同じくらい効いている」ように見えてしまい誤解を招く。同じレンジで描くことで、
# 拡散と濾過のどちらがどれだけ効くかを正しく比較できるようにする。
y_all = pct_vs_qd + pct_vs_qf + [pct_removed]
y_min, y_max = min(y_all), max(y_all)
y_pad = (y_max - y_min) * 0.1 if y_max > y_min else 1.0
shared_y_range = [max(0.0, y_min - y_pad), y_max + y_pad]

col_c1, col_c2 = st.columns(2)
with col_c1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=qd_range, y=pct_vs_qd, mode="lines", line=dict(color="#1d4e89", width=3)))
    fig1.add_trace(go.Scatter(x=[qd], y=[pct_removed], mode="markers",
                               marker=dict(color="#c1121f", size=12, symbol="x"), name="現在の設定"))
    fig1.update_layout(title="QD (透析液流量) を変化させた場合",
                        xaxis_title="QD (mL/h)", yaxis_title="24時間除去率 (%)",
                        yaxis=dict(range=shared_y_range),
                        height=380, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)
with col_c2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=qf_range, y=pct_vs_qf, mode="lines", line=dict(color="#6c757d", width=3)))
    fig2.add_trace(go.Scatter(x=[qf], y=[pct_removed], mode="markers",
                               marker=dict(color="#c1121f", size=12, symbol="x"), name="現在の設定"))
    fig2.update_layout(title="QF (濾液流量) を変化させた場合",
                        xaxis_title="QF (mL/h)", yaxis_title="24時間除去率 (%)",
                        yaxis=dict(range=shared_y_range),
                        height=380, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)
st.caption("💡 左右のグラフは縦軸(除去率%)のスケールを揃えている。線の傾きそのものを比較すれば、"
           "その物質において拡散(QD)と濾過(QF)のどちらがどれだけ効果的かが分かる。")

# ==========================================
# 8. 物質ごとの比較表
# ==========================================
st.markdown("---")
st.subheader("🧬 5物質のふるい係数 比較 (現在の流量設定での参考値)")

compare_rows = []
for name, s in SUBSTANCES.items():
    sd_i, sc_i = calc_sieving(s["mw"], s["free_frac"])
    cl_i = calc_clearance(qb, qd, qf, qs, ht_pct, sd_i, sc_i, dilution_mode)
    pct_i, *_ = simulate_removal_pct(weight, s["v1_per_kg"], s["v2_per_kg"], s["qic"], cl_i["cl_total"], dt=2.0)
    compare_rows.append({
        "物質": name, "MW (Da)": s["mw"], "遊離型分率": f"{s['free_frac']*100:.0f}%",
        "Sd (拡散)": f"{sd_i:.3f}", "Sc (濾過)": f"{sc_i:.3f}",
        "実効CL (mL/min)": f"{cl_i['cl_total']*1000:.2f}",
        "24時間除去率(%)": f"{pct_i:.1f}",
    })
st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)

# ==========================================
# 9. 研修医のための解説
# ==========================================
st.markdown("---")
st.subheader("📚 研修医のための解説")

with st.expander("🔬 1. 拡散(QD)と濾過/対流(QF)の違い、分子量の影響", expanded=True):
    st.markdown(r"""
    **イメージ:「拡散はにじみ拡がる力、濾過(対流)は水流に乗って運ばれる力」**

    * **拡散クリアランス**: $CL_d = Q_D \times S_d$
        透析液との濃度差によって物質が「にじみ拡がる」現象。分子が大きいほど拡散速度が遅くなるため、
        本シミュレーターでは $S_d \propto \sqrt{MW_{尿素}/MW}$ で近似している。
        → **小分子(尿素・カリウム)では非常に効率が良いが、中分子(バンコマイシン)では効率が大きく落ちる。**
    * **濾過(対流)クリアランス**: $CL_c = Q_F \times S_c \times (希釈率)$
        血漿水ごと膜を押し出す現象。分子は水流に「乗っかるだけ」なので、
        膜のカットオフ(約3万Da)に近づくまでは分子量による影響が小さい。
        → **中分子(バンコマイシン・ミオグロビン様物質)を狙うなら、QDよりQFを増やす方が効率的。**
    * **蛋白結合**: 結合した分子は実質的に巨大な蛋白(アルブミン等)と一体化するため、どちらの経路でも
        通過できない。遊離型分率のみが除去対象になる。

    上の比較表で、バンコマイシン(MW 1485, 蛋白結合50%)の **Sd が Sc よりかなり低い** ことに注目すると、
    この違いが直感的に理解できる。
    """)

with st.expander("💧 2. 補充液 (前希釈 / 後希釈) が効率に与える影響", expanded=False):
    st.markdown(r"""
    * **前希釈**: 補充液をフィルターの手前で血液に混ぜる。血液が薄まり凝固しにくくなる(フィルター寿命が延びる)
      が、その分**血漿中の物質濃度も下がる**ため、濾過クリアランスが
      $\dfrac{Q_{B,plasma}}{Q_{B,plasma}+Q_S}$ 倍に低下する(希釈率)。
    * **後希釈**: フィルターを通過した後に補充液を混ぜるため希釈の影響を受けず効率は良いが、
      フィルター内の血液が濃縮されるぶん濾過率(filtration fraction = QF/血漿流量)が上がりすぎると
      フィルター内凝固のリスクが高まる。
    * サイドバーの「希釈方式」を切り替えて、同じQFでも除去率が変化することを確認してみてほしい。
    """)

with st.expander("🩸 3. 血流量(QB)がすべての上限を決める", expanded=False):
    st.markdown(r"""
    どれだけQD・QFを上げても、血液(正確には血漿)が運んでくる物質の量を超えて除去することはできない。

    $$CL_{total} = \min(CL_d + CL_c,\ Q_B \times (1-Ht))$$

    QBを下げた状態でQD・QFだけを増やすシミュレーションをしてみると、ある点から除去率が
    全く伸びなくなる（上の「実効クリアランス」が血漿流量でキャップされる）のが体感できる。
    **「除去量を増やしたいなら、まずQBが十分かを確認する」** という臨床上の優先順位がここから導かれる。
    """)

with st.expander("⏳ 4. 2-コンパートメントモデルと「リバウンド」", expanded=False):
    st.markdown(r"""
    **イメージ:「小さなバケツ(V1=血液)」と「巨大な貯水槽(V2=組織)」、そしてそれをつなぐ「パイプ」**

    * CHDFが直接吸い出せるのは V1(血液側)にある物質だけ。V2(組織側)にある物質は、
      V1とV2をつなぐ「パイプ(組織間移行クリアランス Q)」を通って戻ってこないと除去できない。
    * **パイプが太い(Qが大きい)場合**: 尿素窒素のように、V1の濃度が下がるとすぐV2から補充されるため、
      流量を上げればほぼそのまま除去率も伸びる。
    * **パイプが細い(Qが小さい)場合**: カリウムやバンコマイシンのように、V1だけが先に枯渇してしまい、
      V2にはまだ大量に残っているのに「血液中の値は下がった」ように見える。CHDFを止めると、
      V2からゆっくり戻ってきて血中濃度が再上昇する(**リバウンド**)。
    * これが「カリウムなのに、なぜ流量を上げても思ったほど体内の総カリウムが減らないのか」を説明する
      最大の理由。**膜の通しやすさ(ふるい係数)は尿素と同じくらい良い**のに、組織間移行が遅いせいで
      見かけの効率が悪く見える、という点が研修医にとって混同しやすいポイントである。
    """)

with st.expander("🧪 5. なぜクレアチンキナーゼ(CK)はほとんど抜けないのか", expanded=False):
    st.markdown(r"""
    CK(分子量約86,000)は、標準的な血液濾過膜のカットオフ(約3万Da)を大きく超えているため、
    拡散・濾過のどちらの経路でもほとんど通過できない（本シミュレーターの計算でも除去率は数%程度に
    留まる）。横紋筋融解症の患者でCHDFを行っても、**それ自体でCKの数値が下がることは期待できない**。
    CHDFが有効なのは、横紋筋融解症に伴う急性腎障害・electrolyte異常(高K血症など)・溢水管理であり、
    CK自体の管理は補液・原疾患治療(コンパートメント症候群の除外、原因薬剤の中止等)で行う、という
    整理を意識すると良い。
    """)

with st.expander("⚠️ 6. 本シミュレーターの簡略化・免責事項 (重要)", expanded=True):
    st.markdown(r"""
    本ツールは研修医教育を目的とした**概念理解用の簡略化モデル**であり、実際の処方設計には使用しない。

    * ふるい係数(Sd, Sc)は分子量・蛋白結合率から導いた近似値であり、実際の膜性能(添付文書のSC値、
      fouling・通電時間による劣化等)を反映していない。
    * 拡散クリアランスは「$Q_D \times S_d$」という、QBがQD・QFに対して十分大きい場合に成立する
      effluent-rate近似を用いている。間欠的血液透析(本アプリの「Overdose Simulation」等で使用している
      KoAベースの飽和ダイアランス式)とはモデルが異なる点に注意。
    * 2-コンパートメントモデルのV1・V2・組織間移行クリアランスは教育用の代表値であり、個々の患者の
      体格・病態(浮腫、サードスペースへの移行等)による変動は反映していない。
    * クエン酸抗凝固・フィルター内凝固・再循環(recirculation)・カテーテル機能不全など、実臨床で
      除去効率を左右する要因は考慮していない。
    """)
