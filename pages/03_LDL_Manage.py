import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ページ設定
st.set_page_config(page_title="LDL Global Target & Risk Calculator", layout="wide")

st.title("🌐 LDL管理目標 & 心血管リスク確率計算")
st.markdown("最新の「管理目標値 (Lower is Better)」と、従来の「発症確率 (Risk Score)」の比較")

# ==========================================
# 関数定義：リスクスコア計算
# ==========================================

def calculate_framingham(age, gender, tc, hdl, sbp, is_treated, is_smoker, has_dm):
    """
    Framingham Risk Score (2008 General CVD)
    """
    if gender == "男性":
        beta_age = 3.06117; beta_tc = 1.12370; beta_hdl = -0.93263
        beta_sbp_treated = 1.99881; beta_sbp_untreated = 1.93303
        beta_smoke = 0.65451; beta_dm = 0.57367
        mean_risk = 23.9802; baseline_survival = 0.88936
    else:
        beta_age = 2.32888; beta_tc = 1.20904; beta_hdl = -0.70833
        beta_sbp_treated = 2.82263; beta_sbp_untreated = 2.76157
        beta_smoke = 0.52873; beta_dm = 0.69154
        mean_risk = 26.1931; baseline_survival = 0.95012

    ln_age = np.log(age)
    ln_tc = np.log(tc)
    ln_hdl = np.log(hdl)
    ln_sbp = np.log(sbp)

    score = (beta_age * ln_age) + (beta_tc * ln_tc) + (beta_hdl * ln_hdl)
    score += (beta_sbp_treated * ln_sbp) if is_treated else (beta_sbp_untreated * ln_sbp)
    if is_smoker: score += beta_smoke
    if has_dm: score += beta_dm

    risk = 1 - (baseline_survival ** np.exp(score - mean_risk))
    return min(risk * 100, 99.9)

def calculate_hisayama_score(age, gender, ldl, hdl, sbp, is_smoker, has_dm):
    """
    久山町研究スコア (JAS 2022 ガイドライン準拠)
    ご提示いただいた画像のテーブルロジックを完全再現
    """
    points = 0
    
    # 1. 性別 (Gender)
    if gender == "男性":
        points += 7
    else:
        points += 0

    # 2. 収縮期血圧 (SBP)
    if sbp < 120: points += 0
    elif sbp <= 129: points += 1 # 120-129
    elif sbp <= 139: points += 2 # 130-139
    elif sbp <= 159: points += 3 # 140-159
    else: points += 4          # >= 160

    # 3. 糖代謝異常 (Glucose)
    if has_dm:
        points += 1 # あり=1, なし=0
    
    # 4. LDL-C
    if ldl < 120: points += 0
    elif ldl <= 139: points += 1 # 120-139
    elif ldl <= 159: points += 2 # 140-159
    else: points += 3          # >= 160

    # 5. HDL-C
    if hdl >= 60: points += 0    # >=60
    elif hdl >= 40: points += 1  # 40-59
    else: points += 2            # <40

    # 6. 喫煙 (Smoking)
    if is_smoker:
        points += 2 # あり=2, なし=0

    # --- 確率テーブル参照 (Lookup) ---
    # Rows: Points 0-19
    # Cols: 40-49, 50-59, 60-69, 70-79
    
    # テーブルデータ (画像より転記)
    lookup_table = [
        # 40s,  50s,  60s,  70s
        [1.0,  1.0,  1.7,  3.4], # 0点
        [1.0,  1.0,  1.9,  3.9], # 1点
        [1.0,  1.0,  2.2,  4.5], # 2点
        [1.0,  1.1,  2.6,  5.2], # 3点
        [1.0,  1.3,  3.0,  6.0], # 4点
        [1.0,  1.4,  3.4,  6.9], # 5点
        [1.0,  1.7,  3.9,  7.9], # 6点
        [1.0,  1.9,  4.5,  9.1], # 7点
        [1.1,  2.2,  5.2, 10.4], # 8点
        [1.3,  2.6,  6.0, 11.9], # 9点
        [1.4,  3.0,  6.9, 13.6], # 10点
        [1.7,  3.4,  7.9, 15.5], # 11点
        [1.9,  3.9,  9.1, 17.7], # 12点
        [2.2,  4.5, 10.4, 20.2], # 13点
        [2.6,  5.2, 11.9, 22.9], # 14点
        [3.0,  6.0, 13.6, 25.9], # 15点
        [3.4,  6.9, 15.5, 29.3], # 16点
        [3.9,  7.9, 17.7, 33.0], # 17点
        [4.5,  9.1, 20.2, 37.0], # 18点
        [5.2, 10.4, 22.9, 41.1], # 19点
    ]

    # 年齢インデックスの決定
    if age < 40:
        return 0, points # 40歳未満はデータなし（0%扱いまたは参考値）
    elif age < 50: col_idx = 0
    elif age < 60: col_idx = 1
    elif age < 70: col_idx = 2
    else: col_idx = 3 # 70歳以上（80歳もここに含まれる運用が一般的）

    # ポイントのキャップ処理 (0〜19)
    safe_points = max(0, min(points, 19))
    
    risk_prob = lookup_table[safe_points][col_idx]

    return risk_prob, points


# ==========================================
# サイドバー入力
# ==========================================
st.sidebar.header("患者プロファイル入力")

# 基本情報
age = st.sidebar.number_input("年齢", 20, 100, 50)
gender = st.sidebar.radio("性別", ["男性", "女性"], index=1, horizontal=True)

# 検査値
st.sidebar.subheader("検査値")
current_ldl = st.sidebar.number_input("LDLコレステロール (mg/dL)", 0, 500, 160)
current_hdl = st.sidebar.number_input("HDLコレステロール (mg/dL)", 0, 200, 50)
sbp = st.sidebar.number_input("収縮期血圧 (SBP)", 80, 250, 110)
dbp = st.sidebar.number_input("拡張期血圧 (DBP)", 40, 150, 60)

estimated_tc = current_ldl + current_hdl + 30 

# 病歴・生活習慣
st.sidebar.subheader("病歴・習慣")
is_smoker = st.sidebar.checkbox("喫煙習慣あり", value=False)
has_dm = st.sidebar.checkbox("糖代謝異常 (糖尿病など)", value=False)
has_ckd = st.sidebar.checkbox("慢性腎臓病 (CKD)")
has_ht_med = st.sidebar.checkbox("降圧薬の内服あり")

# 既往歴区分
st.sidebar.markdown("---")
st.sidebar.markdown("**動脈硬化性疾患の既往**")
has_cad = st.sidebar.checkbox("冠動脈疾患 (心筋梗塞・狭心症)")
has_other_history = st.sidebar.checkbox("脳梗塞 / PAD (末梢動脈疾患)")

# 二次予防詳細
is_extreme = False
is_very_high = False
if has_cad or has_other_history:
    st.sidebar.caption("✅ 既往あり (二次予防)")
    is_very_high = st.sidebar.checkbox("高リスク病態 (ACS, FH, DM合併)")
    is_extreme = st.sidebar.checkbox("Extreme Risk (再発・難治性)")
    
has_fh = st.sidebar.checkbox("家族性高コレステロール血症 (FH)")


# ==========================================
# 計算ロジック 1: 目標値
# ==========================================
# (変更なし)

risk_factors_count = 0
if sbp >= 130 or dbp >= 85: risk_factors_count += 1
if is_smoker: risk_factors_count += 1
if current_hdl < 40: risk_factors_count += 1
if (gender == "男性" and age >= 45) or (gender == "女性" and age >= 55):
    risk_factors_count += 1

targets = {"JP": 0, "EU": 0, "US": 0}

# JAS
if has_cad:
    if is_extreme: targets["JP"] = 55
    elif is_very_high: targets["JP"] = 70
    else: targets["JP"] = 100
elif has_other_history:
    targets["JP"] = 120
elif has_fh or has_ckd or has_dm:
    targets["JP"] = 120
elif risk_factors_count >= 2:
    targets["JP"] = 140
else:
    targets["JP"] = 160

# EU
has_ascvd = has_cad or has_other_history
if has_ascvd:
    targets["EU"] = 40 if is_extreme else 55
elif (has_dm and risk_factors_count>=1) or has_ckd or has_fh:
    targets["EU"] = 55
elif has_dm or has_fh:
    targets["EU"] = 70
elif risk_factors_count >= 3:
    targets["EU"] = 100
else:
    targets["EU"] = 116

# US
if has_ascvd:
    targets["US"] = 55 if (is_very_high or is_extreme) else 70
elif has_dm or has_fh:
    targets["US"] = 70
elif risk_factors_count >= 2:
    targets["US"] = 100
else:
    targets["US"] = 130


# ==========================================
# 計算ロジック 2: 確率スコア (修正版)
# ==========================================
is_secondary_prevention = has_cad or has_other_history

if not is_secondary_prevention:
    # Framingham
    frs_prob = calculate_framingham(age, gender, estimated_tc, current_hdl, sbp, has_ht_med, is_smoker, has_dm)
    
    # Hisayama (JAS 2022)
    hisayama_prob, hisayama_points = calculate_hisayama_score(age, gender, current_ldl, current_hdl, sbp, is_smoker, has_dm)
else:
    frs_prob = None
    hisayama_prob = None
    hisayama_points = None


# ==========================================
# UI表示
# ==========================================

tab1, tab2 = st.tabs(["🎯 管理目標値 (Modern)", "📉 発症確率 (Legacy)"])

with tab1:
    st.subheader("現在のガイドラインに基づく管理目標")
    c1, c2, c3 = st.columns(3)
    c1.metric("🇯🇵 日本 (JAS)", f"< {targets['JP']}", delta=current_ldl - targets['JP'], delta_color="inverse")
    c2.metric("🇪🇺 欧州 (ESC)", f"< {targets['EU']}", delta=current_ldl - targets['EU'], delta_color="inverse")
    c3.metric("🇺🇸 米国 (ACC)", f"< {targets['US']}", delta=current_ldl - targets['US'], delta_color="inverse")

    df_bar = pd.DataFrame({
        "Region": ["日本 (JAS)", "欧州 (ESC)", "米国 (ACC)"],
        "Target": [targets['JP'], targets['EU'], targets['US']],
        "Current": [current_ldl, current_ldl, current_ldl]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_bar["Region"], y=df_bar["Target"], name="目標値", marker_color=["#FF9999", "#9999FF", "#99FF99"], text=df_bar["Target"], textposition='auto'))
    fig.add_trace(go.Scatter(x=df_bar["Region"], y=df_bar["Current"], mode='lines+markers', name="あなたの現在値", line=dict(color='red', width=3, dash='dash')))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("10年以内の冠動脈疾患発症確率")
    
    if is_secondary_prevention:
        st.error("⛔ **リスク判定対象外 (Secondary Prevention)**")
        st.markdown(f"""
        **現在、サイドバーで「動脈硬化性疾患の既往」が選択されています。**
        既往がある患者さんの場合、リスクは確率計算の範囲を超えて **「極めて高リスク」** となり、数値化することは不適切です。
        直ちに二次予防の厳格な目標値 (**{targets['JP']} mg/dL未満**) を目指してください。
        """)
    
    else:
        col_prob1, col_prob2 = st.columns(2)
        
        with col_prob1:
            st.markdown("### 🇯🇵 久山町研究スコア (JAS 2022)")
            if hisayama_prob is not None:
                st.markdown(f"**発症確率: 約 {hisayama_prob}%**")
                st.progress(min(hisayama_prob/100, 1.0))
                st.write(f"スコア合計: {hisayama_points}点")
            
            st.caption("出典: 日本動脈硬化学会 動脈硬化性疾患予防ガイドライン2022年版")
            st.warning("⚠️ **注意:** この確率は「冠動脈疾患（心筋梗塞等）」の発症予測です。脳卒中は含まれません。")
            
        with col_prob2:
            st.markdown("### 🌎 世界標準 (Framingham)")
            if frs_prob is not None:
                st.markdown(f"**全心血管疾患 発症確率: 約 {frs_prob:.1f}%**")
                st.progress(min(frs_prob/100, 1.0))
            
            st.info("ℹ️ **CVD全般の予測**")
            st.caption("心筋梗塞に加え、脳卒中、心不全などを含みます。")

    st.markdown("---")
    st.info("""
    **💡 スコアの違いについて:**
    久山町スコア（左）は、画像の通り「年齢を点数に加算せず、年齢別の列を参照する」方式です。
    80代女性でLDLが高値でも、性別点数(0点)などの影響でFraminghamより数値は低く出ますが、
    これは「日本人は欧米に比べて心筋梗塞の発症率が低い」という疫学実態を反映しています。
    """)
