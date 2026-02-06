import streamlit as st
import math
import pandas as pd
import numpy as np
import os
import altair as alt

# --- ページ設定 ---
st.set_page_config(page_title="SePE Sim Ver.2.5 信州上田医療センター腎臓内科", layout="wide")

# --- CSS設定 (スマホ対応: タイトル文字サイズ調整) ---
st.markdown("""
    <style>
    /* スマホ画面（幅600px以下）の時だけ適用される設定 */
    @media (max-width: 600px) {
        /* タイトル (h1) を小さくする */
        h1 {
            font-size: 1.6rem !important;
            padding-bottom: 0.5rem !important;
        }
        /* 見出し (h2) も少し小さく */
        h2 {
            font-size: 1.4rem !important;
            padding-top: 0.5rem !important;
        }
        /* サブ見出し (h3) */
        h3 {
            font-size: 1.2rem !important;
        }
        /* 本文の文字サイズも少し調整 */
        p, .stMarkdown {
            font-size: 0.95rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# タイトル
st.title("🧮 SePE Simulator Ver.2.5 信州上田医療センター腎臓内科")
st.markdown("### 選択的血漿交換療法 (Selective Plasma Exchange)　患者情報は左上>>から入力")

# ==========================================
# ⬅️ サイドバー：入力パラメータ
# ==========================================
with st.sidebar:
    st.header("1. 条件設定")
    
    # --- 患者データ ---
    with st.expander("👤 患者データ (EPV計算用)", expanded=True):
        weight = st.number_input("体重 (kg)", 20.0, 150.0, 50.0, 0.5)
        # 身長入力
        height = st.number_input("身長 (cm) [任意]", 0.0, 250.0, 0.0, 1.0, help="入力なし(0.0)の場合は簡易式(70mL/kg)が適用されます。")
        hct = st.number_input("ヘマトクリット (%)", 10.0, 60.0, 30.0, 0.5)
        alb_initial = st.number_input("血清アルブミン (g/dL)", 1.0, 6.0, 3.5, 0.1)

    # --- 治療目標 ---
    with st.expander("🎯 治療目標", expanded=True):
        target_removal = st.slider("病因物質の除去目標 (%)", 30, 95, 50, 5)
        qp = st.number_input("血漿流量 QP (mL/min)", 10.0, 60.0, 30.0, 5.0)

    # --- アルブミン収支 ---
    with st.expander("⚖️ アルブミン収支設定", expanded=True):
        target_balance_ratio = st.slider("収支目標 (対喪失量 %)", -10, 20, 5, 1, help="予測喪失量に対して、何％上乗せして補充するか設定します。")

    # --- 膜特性 ---
    with st.expander("⚙️ 膜特性 (Evacure EC-4A10c)", expanded=True):
        st.info("💡 **設定のポイント:**\n初期値はカタログ値のアルブミンSC=0.6と設定していますが、実際の治療(in vivo)では、タンパク付着(ファウリング)によりSCはカタログ値より低下する可能性があります。")
        sc_pathogen = st.slider("病因物質SC", 0.0, 1.0, 0.40, 0.01)
        sc_albumin = st.slider("アルブミンSC", 0.0, 1.0, 0.60, 0.01)

# ==========================================
# 🧮 計算ロジック
# ==========================================
def run_simulation():
    # A. 循環血液量 (BV)
    if height > 0:
        h_m = height / 100.0
        bv_L = 0.16874 * h_m + 0.05986 * weight - 0.0305
        bv_calc = bv_L * 1000
        bv_method = "小川の式 (日本人成人)"
    else:
        bv_calc = weight * 70
        bv_method = "簡易式 (70mL/kg)"

    epv = bv_calc * (1 - hct / 100)

    # B. 必要処理量
    if sc_pathogen > 0:
        required_pv = -np.log(1 - target_removal/100.0) * epv / sc_pathogen
    else:
        required_pv = 0

    # C. 治療時間
    treatment_time_min = required_pv / qp if qp > 0 else 0

    # D. 喪失量計算 (線形モデル)
    filtrate_alb_conc = alb_initial * sc_albumin
    base_loss_g = (required_pv / 100.0) * filtrate_alb_conc
    target_supply_g = base_loss_g * (1 + target_balance_ratio / 100.0)

    return epv, bv_method, required_pv, treatment_time_min, base_loss_g, filtrate_alb_conc, target_supply_g

# 計算実行
epv, bv_method, required_pv, treatment_time_min, base_loss_g, filtrate_alb_conc, target_supply_g = run_simulation()

# ==========================================
# 🧪 レシピ最適化ロジック
# ==========================================
def optimize_recipe(required_pv, target_supply_g):
    # レシピパターンの定義
    recipe_patterns = [
        {"name": "Std-500", "p_vol": 500, "alb_btl": 1, "vol": 550, "alb_g": 10},
        {"name": "Std-450", "p_vol": 450, "alb_btl": 1, "vol": 500, "alb_g": 10},
        {"name": "Std-400", "p_vol": 400, "alb_btl": 1, "vol": 450, "alb_g": 10},
        {"name": "Std-350", "p_vol": 350, "alb_btl": 1, "vol": 400, "alb_g": 10},
        {"name": "Dbl-450", "p_vol": 450, "alb_btl": 2, "vol": 550, "alb_g": 20},
        {"name": "Dbl-400", "p_vol": 400, "alb_btl": 2, "vol": 500, "alb_g": 20},
        {"name": "Dbl-350", "p_vol": 350, "alb_btl": 2, "vol": 450, "alb_g": 20},
        {"name": "Plain-500", "p_vol": 500, "alb_btl": 0, "vol": 500, "alb_g": 0},
        {"name": "Plain-400", "p_vol": 400, "alb_btl": 0, "vol": 400, "alb_g": 0},
    ]

    best_plan = None
    approx_sets = int(required_pv / 500)
    search_range = range(max(1, approx_sets - 2), approx_sets + 4)
    found_plans = []

    for n_total_sets in search_range:
        for i in range(len(recipe_patterns)):
            for j in range(i, len(recipe_patterns)):
                rec_a = recipe_patterns[i]
                rec_b = recipe_patterns[j]
                
                for k in range(n_total_sets + 1):
                    count_a = k
                    count_b = n_total_sets - k
                    
                    total_vol = (rec_a["vol"] * count_a) + (rec_b["vol"] * count_b)
                    total_alb = (rec_a["alb_g"] * count_a) + (rec_b["alb_g"] * count_b)
                    
                    # スコア計算
                    diff_g = abs(total_alb - target_supply_g)
                    score_g = (diff_g ** 2) * 50
                    
                    diff_vol = abs(total_vol - required_pv)
                    if 0.85 * required_pv <= total_vol <= 1.25 * required_pv:
                          score_vol = diff_vol / 10
                    else:
                          score_vol = diff_vol * 10 
                    
                    score_complex = 0
                    if count_a > 0 and count_b > 0: score_complex += 50
                    if rec_a["p_vol"] != 500: score_complex += 5
                    if count_b > 0 and rec_b["p_vol"] != 500: score_complex += 5
                    
                    total_score = score_g + score_vol + score_complex
                    
                    found_plans.append({
                        "rec_a": rec_a, "count_a": count_a,
                        "rec_b": rec_b, "count_b": count_b,
                        "total_g": total_alb, "total_vol": total_vol,
                        "score": total_score
                    })

    if found_plans:
        found_plans.sort(key=lambda x: x["score"])
        best_plan = found_plans[0]
    else:
        def_rec = recipe_patterns[0]
        n = int(required_pv / 550) + 1
        best_plan = {"rec_a": def_rec, "count_a": n, "rec_b": def_rec, "count_b": 0, "total_g": n*10, "total_vol": n*550, "score": 999}
    
    return best_plan

best_plan = optimize_recipe(required_pv, target_supply_g)
rec_a = best_plan["rec_a"]
count_a = best_plan["count_a"]
rec_b = best_plan["rec_b"]
count_b = best_plan["count_b"]
actual_replacement_vol = best_plan["total_vol"]
supplied_albumin_g = best_plan["total_g"]

# 指標計算
repl_alb_conc = supplied_albumin_g / actual_replacement_vol * 100 if actual_replacement_vol > 0 else 0
final_diff_g = supplied_albumin_g - base_loss_g

# 警告判定
alert_msg = None
alert_type = "none"
if final_diff_g < -20:
    alert_type = "error"
    alert_msg = f"⚠️ 警告: アルブミンが大幅に不足します ({int(final_diff_g)}g)。スライダー設定を上げてください。"
elif final_diff_g > 30:
    alert_type = "warning"
    alert_msg = f"⚠️ 警告: アルブミンが過剰です (+{int(final_diff_g)}g)。スライダー設定を下げてください。"


# ==========================================
# 🖥️ メインエリア：結果表示
# ==========================================

if alert_msg:
    if alert_type == "error":
        st.error(alert_msg)
    else:
        st.warning(alert_msg)

st.header("2. シミュレーション結果")

m1, m2, m3 = st.columns(3)
m1.metric("予測循環血漿量 (EPV)", f"{int(epv)} mL", f"{bv_method}")
m2.metric("治療時間", f"{int(treatment_time_min)} 分", f"QP: {qp} mL/min")
m3.metric(f"必要処理量 ({target_removal}%除去)", f"{int(required_pv)} mL", f"{required_pv/epv:.2f} PV", delta_color="inverse")

m4, m5, m6 = st.columns(3)
m4.metric("予想Alb喪失量", f"{base_loss_g:.1f} g", f"廃液中濃度: {filtrate_alb_conc:.2f}g/dL", delta_color="inverse")
m5.metric("排液中アルブミン濃度", f"{filtrate_alb_conc:.2f} g/dL", f"患者Alb {alb_initial} × SC {sc_albumin}")
m6.metric("補充液アルブミン濃度 (平均)", f"{repl_alb_conc:.2f} g/dL", f"総Alb {supplied_albumin_g}g / {actual_replacement_vol}mL")

# -----------------------------------------------------
# 🧪 アルブミン収支とレシピ
# -----------------------------------------------------
st.markdown("---")
c_bal, c_plan = st.columns([1, 2])

with c_bal:
    st.subheader("⚖️ アルブミン収支")
    balance_color = "normal"
    if final_diff_g < -20 or final_diff_g > 30:
        balance_color = "off"
    st.metric(f"収支結果", f"{int(final_diff_g):+d} g", f"目標:{target_supply_g:.1f}g → 採用:{int(supplied_albumin_g)}g", delta_color=balance_color)
    
    st.markdown(f"""
    * **補充:** {supplied_albumin_g} g
    * **喪失:** {base_loss_g:.1f} g
    * **設定目標:** {target_balance_ratio:+}%
    """)

with c_plan:
    st.subheader("📋 最適化補充液プラン")
    
    def display_plan(rec, count, label):
        vol = rec['vol']
        p_vol = rec['p_vol']
        btl = rec['alb_btl']
        alb_text = f"**{btl}本** ({btl*10}g)" if btl > 0 else "なし"
        
        st.markdown(f"""
        #### {label}: {vol}mL × **{count}回**
        * **細胞外液:** 500mLバッグのうち **{p_vol}mL** を使用
        * **20%アルブミン 50ml:** {alb_text} 添加
        """)

    if count_a > 0:
        display_plan(rec_a, count_a, "🅰️ パターンA")
        
    if count_b > 0:
        display_plan(rec_b, count_b, "🅱️ パターンB")
        
    st.info(f"""
    **合計準備数**
    * 細胞外液 (500mL): **{count_a+count_b}** 袋
    * 20%アルブミン 50ml: **{count_a*rec_a['alb_btl'] + count_b*rec_b['alb_btl']}** 本
    * 総液量: **{actual_replacement_vol}** mL
    """)

# -----------------------------------------------------
# 🖼️ 回路図
# -----------------------------------------------------
st.markdown("---")
st.subheader("🖼️ 回路構成図")
current_dir = os.path.dirname(os.path.abspath(__file__))
img_path_png = os.path.join(current_dir, "circuit.png")
img_path_jpg = os.path.join(current_dir, "circuit.jpg")

if os.path.exists(img_path_png):
    st.image(img_path_png, use_container_width=True)
elif os.path.exists(img_path_jpg):
    st.image(img_path_jpg, use_container_width=True)
else:
    st.warning("⚠️ 回路図画像 (circuit.png または circuit.jpg) が見つかりません。")

# -----------------------------------------------------
# 📊 グラフ (Altair: 数値拡大・X軸整数・除去率版)
# -----------------------------------------------------
st.markdown("---")
st.subheader("📊 治療経過シミュレーション")

# データ作成
steps = 100
max_plot_vol = max(required_pv * 1.5, epv * 3.0)
log_v = np.linspace(0, max_plot_vol, steps)

# 除去率の計算: 100 * (1 - exp(...))
log_removal = 100 * (1 - np.exp(-log_v * sc_pathogen / epv))

# アルブミン喪失量の計算 (累積)
log_alb_loss_cum = (log_v / 100.0) * filtrate_alb_conc

df_chart = pd.DataFrame({
    "血漿処理量 (mL)": log_v,
    "病因物質 除去率 (%)": log_removal,
    "アルブミン喪失量 (g)": log_alb_loss_cum
})
df_melt = df_chart.melt("血漿処理量 (mL)", var_name="項目", value_name="値")

# --- Altair チャート定義 ---
nearest = alt.selection_point(nearest=True, on='mouseover', fields=['血漿処理量 (mL)'], empty=False)

base = alt.Chart(df_melt).encode(
    x=alt.X("血漿処理量 (mL)", title="血漿処理量 (mL)", axis=alt.Axis(format="d")),
    color=alt.Color("項目", legend=alt.Legend(title=None, orient="bottom"))
)

lines = base.mark_line().encode(
    y=alt.Y("値", title="値 (%, g)")
)

points = base.mark_circle().encode(
    y="値",
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)

selectors = base.mark_point().encode(
    x="血漿処理量 (mL)",
    opacity=alt.value(0),
).add_params(
    nearest
)

text = base.mark_text(align='left', dx=8, dy=-8, fontSize=20, fontWeight='bold').encode(
    y="値",
    text=alt.Text("値", format=".1f"),
    opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
    color=alt.value("black")
)

rules = alt.Chart(df_melt).mark_rule(color='gray').encode(
    x="血漿処理量 (mL)",
).transform_filter(
    nearest
)

chart = alt.layer(
    lines, selectors, points, rules, text
).properties(
    height=400
).configure_axis(
    labelFontSize=12,
    titleFontSize=14
)

st.altair_chart(chart, use_container_width=True)

st.caption(f"ℹ️ 目標達成ポイント: {int(required_pv)} mL 処理時 (除去率 {target_removal}%)")

# -----------------------------------------------------
# 📚 解説
# -----------------------------------------------------
st.markdown("---")
st.header("用語解説・計算根拠")

with st.expander("1. 用語解説 (QP, SC, RC)", expanded=True):
    st.markdown(r"""
    * **QP (Plasma Flow Rate):** * 血漿分離器（EC-4A10c）へ供給される血漿流量（mL/min）です。
    * **ふるい係数 (SC, Sieving Coefficient):** * 膜における物質の「通りやすさ」を示す指標です（0.0～1.0）。
        * $SC = \frac{C_{Filtrate}}{C_{Plasma}}$
        * 1.0に近いほど素通りし、0に近いほど阻止されます。SePEでは「病因物質は1.0に近く、アルブミンは0.6～0.7程度」の膜を使用します。
    * **阻止率 (RC, Rejection Coefficient):** * 膜が物質を「どれだけ通さないか」を示す指標です。$RC = 1 - SC$
    * **排液中アルブミン濃度:**
        * 膜を通過して廃棄される液体中のアルブミン濃度です。本システムでは $\text{患者Alb} \times SC$ で計算します。
    """)

with st.expander("2. Evacure EC-4A10c におけるSC設定の根拠と調整", expanded=True):
    st.markdown("""
    **カタログ値と臨床値の乖離（Safety Margin）**
    In vivo（実際の治療）では、タンパク質の付着や目詰まり（**ファウリング**）により、二次膜が形成され、実効SCはカタログ値よりも低下する傾向があります。
    
    **推奨される調整:**
    * **病因物質SC:** 大きな物質ほどSCは小さくなり除去しづらくなります。＝目標除去率を達成するための必要な血漿処理量が増大します。（DFPPとは意味合いが逆になります）。初期値はエバキュアー4AのIgGに対するカタログ値 SC=0.4が入力されています。
    * **アルブミンSC:** 大きい程アルブミンは失われ、アルブミンの必要補重量が増大します。治療経過によるファウリングで、カタログ値より低下する可能性があります。
    """)

with st.expander("3. 循環血漿量・必要処理量の計算根拠", expanded=True):
    st.markdown(r"""
    **A. 予測循環血漿量 (EPV)**
    * **小川の式:** $BV(L) = 0.16874 \times Height(m) + 0.05986 \times Weight(kg) - 0.0305$
    * **血漿量:** $EPV = BV \times (1 - Hct/100)$

    **B. 必要な血漿処理量 (Required PV)**
    * 病因物質は補充されないため、指数関数的に減少（Washout）します。
      $$V = \frac{- \ln(1 - R) \times EPV}{SC_{pathogen}}$$

    **C. アルブミン喪失量の予測**
    * アルブミンは補充液により濃度が維持される前提のため、処理量に比例して喪失します（線形モデル）。
      $$\text{Loss} (g) = \text{排液中濃度} (g/dL) \times \text{処理量} (dL)$$
    """)
