import streamlit as st
import math
import pandas as pd
import numpy as np
import os
import altair as alt

# --- ページ設定 ---
st.set_page_config(page_title="DFPP Sim Ver.36.3 信州上田医療センター腎臓内科", layout="wide")

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
st.title("🧮 DFPP Advanced Simulator Ver.36.3 信州上田医療センター腎臓内科")
st.markdown("### 📱 スマホ最適化＆グラフ機能強化版")

# ==========================================
# ⬅️ サイドバー：入力パラメータ
# ==========================================
with st.sidebar:
    st.header("1. 条件設定")
    
    # --- 患者データ ---
    with st.expander("👤 患者データ (EPV計算用)", expanded=True):
        weight = st.number_input("体重 (kg)", 20.0, 150.0, 60.0, 0.5)
        # 身長入力
        height = st.number_input("身長 (cm) [任意]", 0.0, 250.0, 0.0, 1.0, help="入力すると「小川の式」で精密計算します。0の場合は「簡易式(体重/13)」を使用します。")
        sex = st.radio("性別 (小川の式で使用)", ("男性", "女性"), horizontal=True)
        ht = st.number_input("ヘマトクリット (%)", 10.0, 60.0, 30.0, 0.5)
        pre_alb = st.number_input("治療前アルブミン (g/dL)", 1.0, 6.0, 3.0, 0.1)

    # --- 膜とターゲット ---
    with st.expander("⚙️ 膜とターゲット", expanded=True):
        membrane_preset = st.radio(
            "膜のプリセット選択",
            ("EC-20 (小孔径)", "EC-30 (中孔径)", "EC-40 (大孔径)"),
            index=0
        )
        
        # デフォルト設定
        if "EC-20" in membrane_preset:
            def_sc_target = 0.10
            def_sc_alb = 0.40 
            desc = "小孔径: IgG除去は強力だが、二次膜形成によりAlbも抜けやすい(実測SC 0.35~0.4)。"
        elif "EC-30" in membrane_preset:
            def_sc_target = 0.40
            def_sc_alb = 0.70
            desc = "中孔径: バランス型。"
        else: # EC-40
            def_sc_target = 0.70
            def_sc_alb = 0.85
            desc = "大孔径: Albはよく戻る(SC高)が、除去効率は悪い。"
            
        st.caption(f"特徴: {desc}")

        sc_target = st.slider(
            "目的物質 SC", 0.0, 1.0, def_sc_target, 0.01, 
            help="低いほどよく抜ける（除去される）。",
            key=f"sc_target_{membrane_preset}"
        )
        sc_alb = st.slider(
            "アルブミン SC", 0.0, 1.0, def_sc_alb, 0.01, 
            help="高いほど体内に戻る（回収される）。",
            key=f"sc_alb_{membrane_preset}"
        )

        st.markdown("---")
        target_rr_pct = st.number_input("🎯 目的物質の目標除去率 (%)", 10.0, 99.9, 70.0, 1.0)

    # --- 運用計画 ---
    with st.expander("⏱️ 運用計画 (流量算出)", expanded=True):
        st.write("目標の処理量をどれくらいの時間で回すか計画します")
        target_time_hr = st.number_input("目標治療時間 (時間)", 1.0, 6.0, 3.0, 0.5)
        discard_ratio_pct = st.slider("廃棄率 (QD/QP比) %", 5, 30, 20)
        
        st.markdown("---")
        st.write("🧪 **補充液レシピ設定**")
        recipe_mode = st.radio(
            "調製モード",
            ("喪失量に合わせる (推奨)", "濃度固定 (4.0%)"),
            help="通常は「喪失量に合わせる」を選択してください。EC-20等でAlb喪失が多い場合、4%固定では補充不足になります。"
        )

# ==========================================
# 🧮 計算ロジック (変更なし)
# ==========================================
def run_simulation():
    # --- EPV計算ロジック分岐 ---
    calc_method_name = ""
    calc_description = ""
    bv_liter = 0.0
    
    if height > 0:
        # 小川の式
        h_m = height / 100.0
        if sex == "男性":
            bv_liter = 0.168 * (h_m**3) + 0.050 * weight + 0.444
        else:
            bv_liter = 0.250 * (h_m**3) + 0.0625 * weight + 0.662
        
        epv = bv_liter * (1 - ht / 100)
        calc_method_name = "小川の式 (Ogawa Formula)"
        calc_description = f"身長({height}cm)・体重・性別から精密計算"
    else:
        # 簡易式
        bv_liter = weight / 13.0
        epv = bv_liter * (1 - ht / 100)
        calc_method_name = "簡易式 (Weight based)"
        calc_description = "体重 ÷ 13 × (1 - Ht) で計算"

    efficiency_target = 1 - sc_target
    efficiency_alb = 1 - sc_alb
    
    if efficiency_target <= 0.001: return None, "⚠️ SCが高すぎて計算不可"
    
    target_rr = target_rr_pct / 100.0
    if target_rr >= 0.999: target_rr = 0.999
    
    try:
        required_pv = -math.log(1 - target_rr) / efficiency_target
    except:
        required_pv = 100.0
        
    v_treated = required_pv * epv
    total_alb_loss = v_treated * (pre_alb * 10) * efficiency_alb
    
    req_qp = (v_treated * 1000) / (target_time_hr * 60)
    req_qd = req_qp * (discard_ratio_pct / 100.0)
    total_waste_vol = req_qd * (target_time_hr * 60) / 1000
    
    return epv, v_treated, required_pv, total_alb_loss, req_qp, req_qd, total_waste_vol, calc_method_name, calc_description

results = run_simulation()

# ==========================================
# 🖥️ メインエリア：結果表示
# ==========================================
if results[0] is None:
    st.error(results[1])
else:
    epv, v_treated, required_pv, loss_alb_mass, req_qp, req_qd, total_waste_vol, calc_name, calc_desc = results

    st.header("2. シミュレーション結果")
    
    if required_pv > 2.0:
        st.warning(f"⚠️ **高負荷警告**: {required_pv:.1f} PV の処理が必要です。")

    # 計算式の明示
    if "小川" in calc_name:
        st.success(f"✅ **{calc_name}** を使用: {calc_desc}")
    else:
        st.info(f"ℹ️ **{calc_name}** を使用: {calc_desc}")

    # メトリクス表示
    m1, m2, m3 = st.columns(3)
    m1.metric("推定循環血漿量 (EPV)", f"{epv:.2f} L", help=f"計算式: {calc_name}")
    m2.metric("必要な総処理量", f"{v_treated:.1f} L", f"{required_pv:.2f} PV", delta_color="inverse")
    
    bottles_needed = math.ceil(loss_alb_mass / 10.0)
    m3.metric(
        "予想Alb喪失量", 
        f"{loss_alb_mass:.0f} g", 
        f"補充目安: {bottles_needed} 本 (20% 50mL)", 
        delta_color="inverse",
        help="この量を補充液に混ぜて戻す必要があります"
    )
    
    st.info(f"📋 **処方目安** ({target_time_hr}時間): QP **{req_qp:.0f}** mL/min / QD **{req_qd:.1f}** mL/min / 置換液 **{total_waste_vol:.1f}** L")

    # -----------------------------------------------------
    # 🧪 補充液調製シミュレーション
    # -----------------------------------------------------
    st.markdown("---")
    st.subheader("🧪 補充液調製レシピ (フィジオ140 + 20%Alb)")
    
    if "喪失量に合わせる" in recipe_mode:
        needed_alb_g = loss_alb_mass
        needed_alb_vol_L = needed_alb_g / 200.0 # 20% = 200g/L
        final_conc_percent = (needed_alb_g / (total_waste_vol * 10))
        
        if needed_alb_vol_L > total_waste_vol:
            st.error("⚠️ **警告**: アルブミン喪失量が多すぎて、予定の置換液量(廃液量)に収まりません！QDを増やすか、別経路での補充を検討してください。")
        else:
            needed_physio_vol_L = total_waste_vol - needed_alb_vol_L
            
            st.markdown(f"##### ✅ 目標: 喪失した **{loss_alb_mass:.0f}g** を完全に補充する")
            
            rec_c1, rec_c2 = st.columns(2)
            with rec_c1:
                st.warning(f"**推奨レシピ (全体量 {total_waste_vol:.1f}L 分)**")
                st.code(f"""
[ ベース液 ]
フィジオ140  : {needed_physio_vol_L:.2f} L

[ 添加剤 ]
20%アルブミン : {needed_alb_vol_L*1000:.0f} mL
             (約 {needed_alb_vol_L*1000 / 50:.1f} 本)
---------------------------
合計液量     : {total_waste_vol:.2f} L
アルブミン量 : {loss_alb_mass:.0f} g ({final_conc_percent:.1f}%)
                """, language="text")
            with rec_c2:
                st.info("**作成のポイント**")
                if final_conc_percent > 6.0:
                    st.write("⚠️ **高濃度です**: EC-20等を使用時は喪失量が多いため、通常より高濃度の補充が必要です。")
                else:
                    st.write("標準的な濃度範囲です。")
    else:
        # 濃度固定モード (4.0%)
        fixed_conc = 4.0
        supplied_alb_g = total_waste_vol * 10 * fixed_conc 
        diff_g = supplied_alb_g - loss_alb_mass
        
        st.markdown(f"##### ⚠️ 設定: 濃度 **4.0%** で固定作成")
        if diff_g < -5.0:
            st.error(f"⛔ **危険**: アルブミンが **{abs(diff_g):.0f} g 不足** します！")
        elif diff_g > 5.0:
            st.warning(f"アルブミンが **{diff_g:.0f} g 過剰** です。")
        else:
            st.success("バランスは概ね良好です。")

        vol_alb_L = total_waste_vol * 0.2
        vol_physio_L = total_waste_vol * 0.8
        
        st.code(f"""
[ 4%固定レシピ ]
フィジオ140  : {vol_physio_L:.2f} L
20%アルブミン : {vol_alb_L*1000:.0f} mL ({vol_alb_L*1000/50:.1f} 本)
補充Alb量    : {supplied_alb_g:.0f} g (不足: {abs(diff_g):.0f} g)
        """, language="text")

    # -----------------------------------------------------
    # 🖼️ 回路図と設定流量
    # -----------------------------------------------------
    st.markdown("---")
    st.subheader("🖼️ 回路図と設定流量")
    
    # 画像と数値を左右に並べる
    col_img, col_metrics = st.columns([1, 1])

    with col_img:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "dfpp_circuit.png")
        try:
            st.image(image_path, caption="DFPP回路図", use_container_width=True)
        except:
            st.warning(f"⚠️ 画像が見つかりません: {image_path}")

    with col_metrics:
        st.markdown("#### ⚙️ 計算された流量")
        st.metric("🟡 QP (血漿流量)", f"{req_qp:.0f} mL/min", help="分離器への供給流量")
        st.metric("🔴 QD (廃棄流量)", f"{req_qd:.1f} mL/min", help="成分分離器からの廃棄流量")
        st.metric("🟢 置換液 (=補充液)", f"{total_waste_vol:.1f} L", help="総廃液量と同じ量を補充します")
        
        st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:10px; border-radius:5px; font-size:0.9em;">
        <b>設定内容:</b><br>
        治療時間: {target_time_hr} 時間<br>
        廃棄率: {discard_ratio_pct} %
        </div>
        """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # 📊 グラフ (Altair: 強化版)
    # -----------------------------------------------------
    st.markdown("---")
    st.subheader("📊 除去量・喪失量シミュレーション")
    
    steps = 100
    x_pv = np.linspace(0, max(2.0, required_pv * 1.2), steps)
    y_rr = (1 - np.exp( -x_pv * (1 - sc_target) )) * 100
    slope = epv * (pre_alb * 10) * (1 - sc_alb)
    y_alb_loss = x_pv * slope
    
    df_chart = pd.DataFrame({
        "処理量 (PV)": x_pv,
        "目的物質 除去率 (%)": y_rr,
        "Alb 喪失量 (g)": y_alb_loss
    })
    df_melt = df_chart.melt("処理量 (PV)", var_name="項目", value_name="値")

    # --- Altair チャート定義 ---
    nearest = alt.selection_point(nearest=True, on='mouseover', fields=['処理量 (PV)'], empty=False)

    base = alt.Chart(df_melt).encode(
        # PVは小数(1.0, 1.5)が重要なので .1f フォーマットで表示
        x=alt.X("処理量 (PV)", title="処理量 (PV)", axis=alt.Axis(format=".1f")),
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
        x="処理量 (PV)",
        opacity=alt.value(0),
    ).add_params(
        nearest
    )

    # 数値を大きく太く表示
    text = base.mark_text(align='left', dx=8, dy=-8, fontSize=20, fontWeight='bold').encode(
        y="値",
        text=alt.Text("値", format=".1f"),
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        color=alt.value("black")
    )

    rules = alt.Chart(df_melt).mark_rule(color='gray').encode(
        x="処理量 (PV)",
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

    # -----------------------------------------------------
    # 📚 詳細用語解説
    # -----------------------------------------------------
    st.markdown("---")
    st.subheader("📚 専門医・研修医のための詳細用語解説")

    with st.expander("🔍 1. QP と QD の臨床的意義 (Detailed)", expanded=True):
        st.markdown(f"""
        #### **QP (Plasma Flow: 血漿流量)**
        * **定義**: 一次膜（分離器）で血液から分離され、二次膜（成分分離器）へ送られる血漿の流量。
        * **設定目安**: $20 \\sim 40$ mL/min。
        
        #### **QD (Drainage Flow: 廃棄流量)**
        * **定義**: 二次膜内で濃縮され、最終的に廃棄バッグへ捨てられる流量。
        * **臨床における「U字カーブ」の罠 (重要)**:
            1. **シミュレーターの計算**: 膜特性(SC)が一定と仮定しているため、QDを変更してもAlb喪失量は変化しません。
            2. **実際の臨床**: QDとAlb喪失量は **「U字型」** の関係にあります。
                * **低すぎる (<15%)**: 膜内で濃縮が起き、**目詰まり(Fouling)** で穴が塞がります。行き場を失ったAlbが廃棄ラインへ漏れ出し、喪失が増えます。
                * **高すぎる (>30%)**: 膜は綺麗になりますが、物理的な廃棄量が増え **全血漿交換(PE)** に近づくため、Alb喪失が増えます。
            3. **結論**: **QPの 20% 前後** が、目詰まりを防ぎつつ廃棄を抑える最適解（スイートスポット）です。
        """)
    
    with st.expander("💉 2. アルブミン補充目安 (20%製剤)", expanded=True):
            st.info("現在は **20%アルブミン製剤** が主流のため、**50mL = 10g** で計算しています。")

    with st.expander("⚗️ 3. SC (ふるい係数) と 阻止率 (RC)", expanded=True):
        st.markdown("""
        * **SC (Sieving Coefficient)**: 膜を「通り抜けて体に戻る」割合 ($0.0 \\sim 1.0$)。
        * **RC (Rejection Coefficient)**: 膜で「阻止されて廃棄される」割合 ($RC = 1 - SC$)。
        """)

    with st.expander("⚠️ 4. カタログ値・他サイトとの乖離理由 (重要)", expanded=True):
        st.info("""
        **「メーカーの計算サイトと結果が違う」** 場合、使用しているデータの前提が異なることが主な要因です。
        """)
        st.markdown("""
        #### **① ふるい係数 (SC) の基準差 (In vitro vs In vivo)**
        * **他サイト**: 
            * 添付文書に記載された **牛アルブミン血清 (In vitro)** のデータである **SC=0.6 (EC-20)** や、
            * 旭化成カスケードフロー資料にある **SC=0.35 (ヒト血漿 In vitro)** など、
            * データソースが混在しており、他サイトの予測式もこれら（特に仕様値の0.6）を参照している場合が多いと思われます。
        
        * **本アプリ**: 
            * ヒト血漿での **二次膜形成 (Fouling)** を考慮し、実測値に近い **SC=0.4** で厳しく計算しています。
        
        * **結果**: 
            * 本アプリの方がアルブミン喪失量（補充必要量）が多く算出されます。これは **補充不足による低血圧等のトラブルを防ぐため、安全サイド** の数値を出すように設計しているためです。

        #### **② 循環血漿量 (EPV) 計算式の違い**
        * **簡易式**: `体重 ÷ 13`。簡便ですが、肥満や痩せ型で誤差が出ます。
        * **小川の式**: 日本人の体格に合わせた精密式。身長・体重・性別を用います。
        * **結果**: 身長を入力して小川の式を使うと、簡易式より正確なPVが算出され、処理量設定の精度が上がります。
        """)

    with st.expander("🩸 5. 循環血漿量 (EPV) の計算ロジック詳細", expanded=True):
        st.markdown("""
        **EPV (Estimated Plasma Volume)** は、治療のベースとなる「患者さんの体内の血漿総量」です。
        * **簡易式**: $EPV = \\text{Weight}/13 \\times (1 - Ht/100)$
        * **小川の式**: 身長・体重・性別から $BV$ を求め、$(1-Ht)$ を掛けて算出します。
        """)

    with st.expander("🧮 6. 必要処理量の計算ロジック (One-compartment model) 詳細", expanded=True):
        st.markdown("""
        血液浄化では、浄化された血液が体内に戻って混ざるため、濃度は対数的に減衰します。
        #### **計算式**
        """)
        st.latex(r"V_{treated} = \frac{- EPV \times \ln(1 - RR)}{RC}")
        st.markdown(f"""
        1.  **$RR$ (Removal Rate)**: 目標除去率。
        2.  **$\\ln$ (自然対数)**: 「薄まりながら減る」効率低下を補正。
        3.  **$RC$ (Rejection Coefficient)**: 膜の実質的な除去能力 ($1-SC$)。
        """)
