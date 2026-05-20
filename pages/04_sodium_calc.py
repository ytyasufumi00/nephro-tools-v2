import streamlit as st
import pandas as pd

# --- 計算ロジック関数 ---
def calculate_sodium(
    weight, current_na, current_k,
    urine_vol, urine_na, urine_k,
    infusion_vol, infusion_na_total, infusion_k_total,
    diet_water, diet_salt_g,
    stool_water, stool_salt_g,
    insensible_vol,
    gender_factor
):
    SALT_TO_MEQ = 17.1
    
    # 1. 初期状態
    initial_tbw = weight * gender_factor
    
    # 2. INPUT
    in_infusion_solutes = infusion_na_total + infusion_k_total
    in_infusion_water = infusion_vol
    in_diet_solutes = (diet_salt_g * SALT_TO_MEQ)
    in_diet_water = diet_water
    
    total_in_solutes = in_infusion_solutes + in_diet_solutes
    total_in_water = in_infusion_water + in_diet_water

    # 3. OUTPUT
    out_urine_solutes = (urine_na + urine_k) * urine_vol
    out_urine_water = urine_vol
    out_stool_solutes = (stool_salt_g * SALT_TO_MEQ)
    out_stool_water = stool_water
    out_insensible_water = insensible_vol

    total_out_solutes = out_urine_solutes + out_stool_solutes
    total_out_water = out_urine_water + out_stool_water + out_insensible_water

    # 4. 結果
    final_tbw = initial_tbw + total_in_water - total_out_water
    delta_vol = total_in_water - total_out_water
    
    # Na予測 (Mass Balance)
    final_total_osmoles = (current_na * initial_tbw) + total_in_solutes - total_out_solutes
    predicted_na = final_total_osmoles / final_tbw

    return predicted_na, delta_vol, final_tbw, initial_tbw

# --- UI構築 ---
st.set_page_config(page_title="Na予測計算", layout="wide")

# --- CSS設定 (スマホ対応: タイトル文字サイズ調整) ---
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

st.title("🩸 血中ナトリウム濃度 補正予測")
st.markdown("体重入力で不感蒸泄が自動計算されます。発熱時などは手動で修正してください。")

# --- Session State ---
if "prev_weight" not in st.session_state:
    st.session_state.prev_weight = 60.0
if "insensible_val" not in st.session_state:
    st.session_state.insensible_val = 0.9

def update_insensible():
    w = st.session_state.weight_input
    st.session_state.insensible_val = round(w * 15 / 1000, 2)
    st.session_state.prev_weight = w

# --- メイン画面 入力セクション ---
st.divider()

# 1. 患者基本情報
st.header("1. 患者基本情報")
col1, col2 = st.columns(2)

with col1:
    weight = st.number_input(
        "体重 (kg)", 
        value=60.0, step=0.1, key="weight_input", on_change=update_insensible
    )
    gender = st.radio("性別", ["男性 (0.6)", "女性/高齢者 (0.5)"], horizontal=True)
    gender_factor = 0.6 if "男性" in gender else 0.5

with col2:
    current_na = st.number_input("血清 Na (mEq/L)", value=125.0, step=1.0)
    current_k = st.number_input("血清 K (mEq/L)", value=4.0, step=0.1)

st.divider()

# 2. インプット (治療)
st.header("2. インプット (治療)")
col3, col4 = st.columns(2)

with col3:
    st.subheader("補液設定")
    infusion_vol = st.number_input("補液量 (L)", value=2.0, step=0.1)
    infusion_na_total = st.number_input("補液総 Na量 (mEq/日)", value=308.0, step=10.0)
    infusion_k_total = st.number_input("補液総 K量 (mEq/日)", value=0.0, step=5.0)

with col4:
    # 事前にデフォルト値を設定しておく（バグ回避）
    diet_water = 0.0
    diet_salt_g = 0.0
    
    # 食事・飲水オプションをデフォルト最小化
    with st.expander("🍽️ 食事・飲水 (オプション)", expanded=False):
        diet_water = st.number_input("経口 水分 (L)", value=0.0, step=0.1)
        diet_salt_g = st.number_input("経口 塩分 (g)", value=0.0, step=0.5)

st.divider()

# 3. アウトプット (喪失)
st.header("3. アウトプット (喪失)")
col5, col6 = st.columns(2)

with col5:
    # 事前に標準値を設定しておく（バグ回避）
    insensible_vol = st.session_state.insensible_val
    urine_vol = 1.5
    urine_na = 80.0
    urine_k = 40.0
    
    # 不感蒸泄・尿オプションをデフォルト最小化
    with st.expander("💧 不感蒸泄・尿 (標準値設定済)", expanded=False):
        insensible_help = "通常: 15mL/kg/日。発熱時: +1℃ごとに +15%増量。"
        insensible_vol = st.number_input(
            "不感蒸泄 (L)",
            value=st.session_state.insensible_val,
            step=0.1, format="%.2f", help=insensible_help
        )
        st.caption(f"基準値(15ml/kg): {round(weight * 0.015, 2)} L")

        urine_vol = st.number_input("予測尿量 (L)", value=1.2, step=0.1)
        urine_na = st.number_input("尿中 Na (mEq/L)", value=80.0, step=10.0)
        urine_k = st.number_input("尿中 K (mEq/L)", value=20.0, step=10.0)

with col6:
    # 事前にデフォルト値を設定しておく（バグ回避）
    stool_water = 0.0
    stool_salt_g = 0.0
    
    # 便・下痢オプションをデフォルト最小化
    with st.expander("💩 便・下痢 (オプション)", expanded=False):
        stool_water = st.number_input("便中 水分 (L)", value=0.0, step=0.1)
        stool_salt_g = st.number_input("便中 塩分 (g)", value=0.0, step=0.5)
        
        st.markdown("##### 💡 一般的な下痢の目安")
        st.caption("""
        * **水様便の塩分濃度**: 一般的に Na 30〜100 mEq/L 程度です。
          (塩分換算で **水分 1L あたり 塩分 2〜6g** 程度)
        * **軟便〜泥状便**: 水分 0.3〜0.5L、塩分 1〜2g 程度
        * **重度の水様下痢**: 水分 1.0L〜、塩分 3〜6g/L 程度
        ※分泌性下痢（感染性など）はNaが高く、浸透圧性下痢（下剤など）は低い傾向があります。
        """)

# --- 計算実行 ---
pred_na, delta_vol, final_tbw, initial_tbw = calculate_sodium(
    weight, current_na, current_k,
    urine_vol, urine_na, urine_k,
    infusion_vol, infusion_na_total, infusion_k_total,
    diet_water, diet_salt_g,
    stool_water, stool_salt_g,
    insensible_vol,
    gender_factor
)
delta_na = pred_na - current_na

# --- 結果表示 ---
st.markdown("---")
st.markdown("### 📊 予測結果")

col_res1, col_res2 = st.columns(2)

with col_res1:
    st.info("##### 血清ナトリウム濃度 (Na)")
    na_color = "#0068c9"
    if abs(delta_na) > 10:
        na_color = "#ff2b2b"
        
    st.markdown(
        f"""
        <div style="text-align: center; font-size: 1.2rem;">
        {current_na:.1f} <span style="color: gray;">mEq/L</span>
        <br>↓<br>
        <span style="font-size: 2.5rem; font-weight: bold; color: {na_color};">{pred_na:.1f}</span> 
        <span style="font-size: 1.5rem; color: {na_color};">mEq/L</span>
        </div>
        """, unsafe_allow_html=True
    )
    if delta_na > 0:
        st.metric("変化量", f"+{delta_na:.2f}", delta_color="normal")
    else:
        st.metric("変化量", f"{delta_na:.2f}", delta_color="inverse")
    if abs(delta_na) > 10:
        st.warning("⚠️ **注意**: Na変化幅が >10 です")

with col_res2:
    st.success("##### 体液量 (体重換算)")
    val_color = "#09ab3b" if delta_vol >= 0 else "#ff2b2b"
    st.markdown(
        f"""
        <div style="text-align: center; font-size: 1.2rem;">
        {initial_tbw:.2f} <span style="color: gray;">L (kg)</span>
        <br>↓<br>
        <span style="font-size: 2.5rem; font-weight: bold; color: {val_color};">{final_tbw:.2f}</span> 
        <span style="font-size: 1.5rem; color: {val_color};">L (kg)</span>
        </div>
        """, unsafe_allow_html=True
    )
    if delta_vol >= 0:
        st.metric("水分バランス", f"+{delta_vol:.2f} L")
    else:
        st.metric("水分バランス", f"{delta_vol:.2f} L")

st.markdown("---")
with st.expander("詳細な収支データを見る", expanded=True):
    balance_df = pd.DataFrame({
        "項目": ["水分 (L)", "Na負荷 (mEq)*"],
        "IN (補液+食事)": [
            infusion_vol + diet_water,
            infusion_na_total + infusion_k_total + (diet_salt_g * 17.1)
        ],
        "OUT (尿+便+不感蒸泄)": [
            urine_vol + stool_water + insensible_vol,
            (urine_na + urine_k) * urine_vol + (stool_salt_g * 17.1)
        ]
    }, index=["Total Volume", "Total Solutes"])
    balance_df["収支 (IN - OUT)"] = balance_df["IN (補液+食事)"] - balance_df["OUT (尿+便+不感蒸泄)"]
    st.table(balance_df)
    st.caption("※不感蒸泄は電解質フリーの水（自由水）喪失として計算に含まれています。")

# --- 計算根拠の表示 ---
st.markdown("---")
with st.expander("📚 計算式の根拠・医学的背景 (クリックで展開)"):
    st.markdown("""
    ### 1. 基礎理論: Edelmanの式
    本システムの計算は、**Tonicity Balance（トニシティ・バランス）** の概念に基づいています。
    血清Na濃度は、体内の「総交換性陽イオン量」と「総体液量」の比で決定されるという **Edelmanの式** が基礎となります。
    """)
    
    st.latex(r"Na_s = \frac{Na_e + K_e}{TBW}")
    
    st.markdown("""
    * $Na_s$: 血清ナトリウム濃度
    * $Na_e$: 総交換性ナトリウム量 (Total Exchangeable Sodium)
    * $K_e$: 総交換性カリウム量 (Total Exchangeable Potassium)
    * $TBW$: 総体液量 (Total Body Water)
    
    細胞内液の主役であるカリウム($K$)も、細胞膜を介した水の移動により血清Na濃度に影響を与えるため（浸透圧物質として等価に振る舞う）、計算式に含まれます。
    
    ### 2. 本アプリの計算ロジック (マスバランス)
    初期状態から治療による「インプット」と「アウトプット」の収支を加算し、最終的な濃度を予測しています。
    """)
    
    st.latex(r"予測Na = \frac{\text{初期総陽イオン} + \Delta\text{陽イオン(in)} - \Delta\text{陽イオン(out)}}{\text{初期総体液量} + \Delta\text{水分(in)} - \Delta\text{水分(out)}}")
    
    st.markdown("""
    #### 各項目の扱い
    * **初期総体液量**: 体重 × 性別係数 (男性0.6, 女性/高齢者0.5)
    * **陽イオン負荷**: Naだけでなく K も浸透圧物質として加算しています。
    * **不感蒸泄 (Insensible Loss)**: 電解質を含まない「自由水」の喪失として水分のアウトプットにのみ加算されます（これによりNaの濃縮を表現）。
    
    ### 3. 免責・注意点
    * **あくまで予測値です**: 生体内での不活性化、血糖値の影響、腎機能の急激な変動などは考慮されていません。
    * **臨床判断**: 必ず実際の採血・尿検査データに基づいて治療方針を決定してください。
    
    Reference: 
    * *Rose BD, Post TW. Clinical Physiology of Acid-Base and Electrolyte Disorders.*
    * *Nguyen MK, et al. A new formula for predicting the plasma sodium concentration.*
    """)