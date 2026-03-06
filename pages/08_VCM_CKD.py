import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- 選択肢を変数化 (文字のズレによるバグを完全防止) ---
MODE_CALC = "年齢・性別・Creから計算 (💡推奨)"
MODE_EGFR = "eGFRを直接入力 (要BSA補正)"

# ==========================================
# 1. 計算ロジック (保存期CKD VCM)
# ==========================================
class VCMSimulationCKD:
    def __init__(self, weight, ccr, params):
        self.weight = weight
        self.ccr = ccr
        self.Vd = params['Vd_per_kg'] * weight
        
        # kel = (0.00083 * CCr + 0.0044) * factor
        self.kel_base = (0.00083 * ccr + 0.0044) * params['kel_factor']
        self.t_half = 0.693 / self.kel_base if self.kel_base > 0 else 999
        self.cl = self.Vd * self.kel_base

    def run_sim_schedule(self, dose_list, interval, infusion_time=1.0):
        num_doses = len(dose_list)
        total_hours = num_doses * interval + 48 
        time_steps = np.arange(0, total_hours * 60, 60) # 1時間刻み
        conc_curve = np.zeros(len(time_steps))
        
        for i, d in enumerate(dose_list):
            if d <= 0: continue
            
            t_start = i * interval
            t_inf_min = infusion_time * 60
            ke = self.kel_base / 60 
            
            for j, t_min in enumerate(time_steps):
                t_from_start = t_min - (t_start * 60)
                
                if t_from_start < 0: continue
                
                if t_from_start <= t_inf_min:
                    rate = d / t_inf_min
                    val = (rate / (self.Vd * ke)) * (1 - np.exp(-ke * t_from_start))
                else:
                    t_post = t_from_start - t_inf_min
                    rate = d / t_inf_min
                    c_peak_calc = (rate / (self.Vd * ke)) * (1 - np.exp(-ke * t_inf_min))
                    val = c_peak_calc * np.exp(-ke * t_post)
                
                conc_curve[j] += val
                
        return time_steps / 60, conc_curve

    def calc_auc24_steady(self, daily_dose):
        if self.cl == 0: return 0
        return daily_dose / self.cl

# パラメータフィッティング
def fit_kel_from_measured(target_val, measured_hour, weight, dose_list, interval, Vd_est, infusion_time=1.0):
    low_k, high_k = 0.001, 0.5 
    
    dummy_params = {'Vd_per_kg': Vd_est, 'kel_factor': 1.0}
    target_idx = int(measured_hour)
    
    for _ in range(20):
        mid_k = (low_k + high_k) / 2
        
        sim = VCMSimulationCKD(weight, 0, dummy_params)
        sim.kel_base = mid_k
        
        t, c = sim.run_sim_schedule(dose_list, interval, infusion_time)
        
        pred = c[target_idx] if target_idx < len(c) else 0
        
        if pred > target_val:
             low_k = mid_k
        else:
             high_k = mid_k
             
    return (low_k + high_k) / 2

# ==========================================
# 2. UI & アプリケーション
# ==========================================
st.set_page_config(page_title="VCM CKD Sim", layout="wide")
st.title("💊 VCM 投与設計 (保存期CKD)")

st.markdown("""
<style>
@media only screen and (max-width: 600px) {
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    div[data-testid="stSidebar"] button { padding: 0.2rem 0.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# --- 定数 ---
NUM_SLOTS = 14

# --- 自動計算コールバック関数 ---
def auto_calc_recommendation():
    """
    患者情報が変更されたときに呼ばれ、推奨投与量・間隔を計算して更新
    """
    w = st.session_state.get('weight_input', 60.0)
    mode = st.session_state.get('input_mode', MODE_CALC) # ✅ 変数を使用
    
    ccr_est = 0.0
    if mode == MODE_CALC: # ✅ 変数で完全一致判定
        a = st.session_state.get('age_input', 70)
        s = st.session_state.get('sex_input', "男性")
        c = st.session_state.get('cr_input', 1.2)
        if c > 0:
            val = ((140 - a) * w) / (72 * c)
            ccr_est = val * 0.85 if s == "女性" else val
    else:
        # eGFR入力時のBSA補正を反映
        egfr = st.session_state.get('egfr_input_val', 45.0)
        h = st.session_state.get('height_input', 0.0)
        if h > 0:
            bsa = 0.007184 * (w ** 0.425) * (h ** 0.725)
            ccr_est = egfr * (bsa / 1.73)
        else:
            ccr_est = egfr

    # 推奨設計
    if ccr_est > 60: rec_int = 12
    elif 40 <= ccr_est <= 60: rec_int = 24
    elif 20 <= ccr_est < 40: rec_int = 48
    else: rec_int = 72
    
    rec_load = w * 20.0
    rec_load = round(rec_load / 100) * 100
    if rec_load > 2500: rec_load = 2500.0
    
    rec_maint = w * 15.0
    rec_maint = round(rec_maint / 100) * 100
    if rec_maint > 2000: rec_maint = 2000.0
    
    st.session_state['interval_input'] = rec_int
    st.session_state['ckd_dose_1'] = float(rec_load)
    for i in range(2, NUM_SLOTS + 1):
        st.session_state[f'ckd_dose_{i}'] = float(rec_maint)

# --- セッションステート初期化 ---
for i in range(1, NUM_SLOTS + 1):
    key = f'ckd_dose_{i}'
    if key not in st.session_state:
        st.session_state[key] = 1500.0 if i == 1 else 1000.0

# --- 連動更新関数 ---
def update_dose_cascade(target_key, increment):
    new_val = st.session_state[target_key] + increment
    if new_val < 0: new_val = 0.0
    st.session_state[target_key] = new_val
    try:
        current_idx = int(target_key.split('_')[-1])
        for i in range(current_idx + 1, NUM_SLOTS + 1):
            st.session_state[f'ckd_dose_{i}'] = new_val
    except:
        pass

# --- サイドバー: 患者情報 ---
st.sidebar.header("1. 患者情報")

weight = st.sidebar.number_input(
    "体重 (kg)", 30.0, 150.0, 60.0, 1.0, 
    key='weight_input', on_change=auto_calc_recommendation
)

input_mode = st.sidebar.radio(
    "腎機能入力方法", [MODE_CALC, MODE_EGFR], # ✅ 変数を使用
    key='input_mode', on_change=auto_calc_recommendation
)

ccr_for_sim = 0.0

# ✅ 変数で完全一致判定 (これで絶対にズレません)
if input_mode == MODE_CALC:
    age = st.sidebar.number_input("年齢", 18, 100, 70, key='age_input', on_change=auto_calc_recommendation)
    sex = st.sidebar.radio("性別", ["男性", "女性"], horizontal=True, key='sex_input', on_change=auto_calc_recommendation)
    cr = st.sidebar.number_input("Cr (mg/dL)", 0.3, 15.0, 1.2, 0.1, key='cr_input', on_change=auto_calc_recommendation)

    def calc_ccr(age, sex, cr, weight):
        if cr <= 0: return 0
        val = ((140 - age) * weight) / (72 * cr)
        return val * 0.85 if sex == "女性" else val

    ccr_calc = calc_ccr(age, sex, cr, weight)
    eGFR_calc = 194 * (cr**-1.094) * (age**-0.287) * (0.739 if sex == "女性" else 1.0)
    
    st.sidebar.info(f"🧬 **CCr: {ccr_calc:.1f} mL/min**\n\n(eGFR: {eGFR_calc:.1f})")
    ccr_for_sim = ccr_calc 
else:
    egfr_input = st.sidebar.number_input(
        "eGFR (mL/min/1.73m²)", 0.0, 150.0, 45.0, 1.0, 
        key='egfr_input_val', on_change=auto_calc_recommendation
    )
    
    # ✅ 身長入力フィールドの追加（BSA補正用）
    height_input = st.sidebar.number_input(
        "身長 (cm) [任意]", 0.0, 250.0, 0.0, 1.0,
        help="入力するとDuBois式で体表面積(BSA)を計算し、個別化eGFR(mL/min/body)に補正します。",
        key='height_input', on_change=auto_calc_recommendation
    )
    
    if height_input > 0:
        # DuBois式でのBSA計算
        bsa = 0.007184 * (weight ** 0.425) * (height_input ** 0.725)
        egfr_body = egfr_input * (bsa / 1.73)
        st.sidebar.info(f"📐 **BSA:** {bsa:.2f} m²\n\n🧬 **補正eGFR:** {egfr_body:.1f} mL/min/body\n\n(シミュレーションに使用)")
        ccr_for_sim = egfr_body
    else:
        st.sidebar.info(f"🧬 入力値 **{egfr_input:.1f}** をそのまま腎機能指標として使用\n\n(身長を入力するとBSA補正されます)")
        ccr_for_sim = egfr_input


# --- サイドバー: 投与設定 (個別入力) ---
st.sidebar.markdown("---")
st.sidebar.header("2. 投与スケジュール")

# 初期表示用 interval (実質 session_state['interval_input'] が使われる)
interval = st.sidebar.number_input(
    "投与間隔 (時間)", 12, 168, 24, 12, 
    key='interval_input'
)
infusion_hr = st.sidebar.selectbox("点滴時間", [1.0, 2.0], index=0)

st.sidebar.markdown("##### 💉 投与量入力 (連動)")
st.sidebar.caption("※患者情報を変更すると推奨量が自動入力されます")

for i in range(1, NUM_SLOTS + 1):
    key = f'ckd_dose_{i}'
    total_hours = (i - 1) * interval
    day = int(total_hours // 24) + 1
    hour_mod = int(total_hours % 24)
    label = f"{i}回目: Day {day} - {hour_mod:02d}:00"
    
    st.sidebar.markdown(f"**{label}**")
    c1, c2, c3 = st.sidebar.columns([1, 2, 1])
    with c1: st.button("－", key=f"dec_{key}", on_click=update_dose_cascade, args=(key, -50))
    with c2: st.number_input(label, key=key, step=50.0, label_visibility="collapsed")
    with c3: st.button("＋", key=f"inc_{key}", on_click=update_dose_cascade, args=(key, 50))

with st.sidebar.expander("詳細PKパラメータ"):
    vd_pk = st.slider("分布容積 Vd (L/kg)", 0.4, 1.0, 0.7, 0.05)
    kel_factor = st.slider("排泄係数補正", 0.5, 1.5, 1.0, 0.1)

# ==========================================
# 3. シミュレーション実行 (現在値)
# ==========================================
pk_params = {'Vd_per_kg': vd_pk, 'kel_factor': kel_factor}
sim = VCMSimulationCKD(weight, ccr_for_sim, pk_params)

current_dose_list = [st.session_state[f'ckd_dose_{i}'] for i in range(1, NUM_SLOTS + 1)]
times, conc_base = sim.run_sim_schedule(current_dose_list, interval, infusion_time=infusion_hr)

last_dose = current_dose_list[-1]
daily_dose_equiv = last_dose * (24 / interval)
auc24_initial = sim.calc_auc24_steady(daily_dose_equiv)

# ==========================================
# 4. TDM解析エリア
# ==========================================
st.subheader("🩸 TDM解析 / AUC評価")

col_t1, col_t2 = st.columns([1.5, 2.5])

# デフォルト設定: index=1 ("TDM実測値あり")
has_measured = st.radio("入力モード", ["シミュレーションのみ", "TDM実測値あり"], index=1, horizontal=True, label_visibility="collapsed") == "TDM実測値あり"

sim_fitted = None
mod_conc = None
new_dose = 0

with col_t1:
    if has_measured:
        st.markdown("##### 📝 実測値")
        timing_mode = st.selectbox("採血タイミング", ["投与直前 (トラフ)", "投与終了後 (ピーク等)"], index=1)
        target_dose_num = st.number_input("何回目の投与？", 2, NUM_SLOTS, 3) 
        
        t_start_dose = (target_dose_num - 1) * interval
        if timing_mode == "投与直前 (トラフ)":
            sampling_time = t_start_dose
        else:
            hours_after = st.number_input("投与終了から何時間後？", 0.0, float(interval), 3.0, 0.5)
            sampling_time = t_start_dose + infusion_hr + hours_after
            
        st.caption(f"→ 開始から {sampling_time:.1f} 時間後")
        
        # デフォルト: 12.0
        measured_val = st.number_input("実測値 (µg/mL)", 0.0, 100.0, 20.0, 0.1)
    
    st.markdown("---")
    st.markdown("##### 🎯 目標")
    target_mode = st.radio("目標指標", ["AUC24 (推奨)", "トラフ濃度"])
    if target_mode == "AUC24 (推奨)":
        target_auc = st.slider("目標AUC24", 400, 600, 450, 10)
    else:
        target_trough = st.slider("目標トラフ", 10.0, 20.0, 15.0, 0.5)

# 解析
with col_t2:
    if has_measured and measured_val > 0:
        st.markdown("##### 📊 解析結果")
        with st.spinner("パラメータ逆算中..."):
            fitted_kel = fit_kel_from_measured(measured_val, sampling_time, weight, current_dose_list, interval, vd_pk, infusion_hr)
            
            sim_fit_obj = VCMSimulationCKD(weight, ccr_for_sim, pk_params)
            sim_fit_obj.kel_base = fitted_kel
            sim_fit_obj.cl = sim_fit_obj.Vd * fitted_kel
            _, sim_fitted = sim_fit_obj.run_sim_schedule(current_dose_list, interval, infusion_hr)
            
            auc_current = sim_fit_obj.calc_auc24_steady(daily_dose_equiv)
            
            c1, c2 = st.columns(2)
            c1.metric("推定半減期", f"{0.693/fitted_kel:.1f} h", help=f"初期予測: {sim.t_half:.1f} h")
            c2.metric("現在のAUC24", f"{auc_current:.0f}")
            
            used_sim_obj = sim_fit_obj
    else:
        used_sim_obj = sim
        auc_current = auc24_initial
        if not has_measured:
            st.metric("予測AUC24 (初期設定)", f"{auc_current:.0f}")

    if (has_measured and measured_val > 0) or not has_measured:
        st.markdown("##### 💡 投与量提案")
        
        if target_mode == "AUC24 (推奨)":
            req_daily_dose = target_auc * used_sim_obj.cl
        else:
            base_data = sim_fitted if sim_fitted is not None else conc_base
            curr_trough = base_data[-1]
            if curr_trough > 0:
                req_daily_dose = daily_dose_equiv * (target_trough / curr_trough)
            else:
                req_daily_dose = daily_dose_equiv
        
        suggest_raw = req_daily_dose / (24 / interval)
        new_dose = round(suggest_raw / 100) * 100
        
        if new_dose != last_dose:
            st.success(f"推奨維持量: **{new_dose} mg** (間隔 {interval}h のまま)")
            
            mod_dose_list = current_dose_list.copy()
            if has_measured:
                start_mod_idx = int(target_dose_num)
                if start_mod_idx >= NUM_SLOTS: start_mod_idx = NUM_SLOTS - 1
            else:
                start_mod_idx = 1
            
            for k in range(start_mod_idx, NUM_SLOTS):
                mod_dose_list[k] = new_dose
            
            sim_mod_obj = VCMSimulationCKD(weight, ccr_for_sim, pk_params)
            sim_mod_obj.kel_base = used_sim_obj.kel_base
            _, mod_conc = sim_mod_obj.run_sim_schedule(mod_dose_list, interval, infusion_hr)
        else:
            st.info("現在の投与量で目標範囲内です。")


# ==========================================
# 5. グラフ描画
# ==========================================
st.markdown("---")
st.subheader("📈 シミュレーション結果")

fig = go.Figure()

if sim_fitted is not None:
    y_orange = sim_fitted
    name_orange = "実測からの推定 (Current)"
else:
    y_orange = conc_base
    name_orange = "入力値から予測 (Predicted)"

fig.add_trace(go.Scatter(
    x=times/24, y=y_orange,
    mode='lines', name=name_orange,
    line=dict(color='orange', width=2)
))

if has_measured and measured_val > 0:
    fig.add_trace(go.Scatter(
        x=[sampling_time/24], y=[measured_val],
        mode='markers', name='実測値',
        marker=dict(color='red', size=12, symbol='x')
    ))

if mod_conc is not None:
    fig.add_trace(go.Scatter(
        x=times/24, y=mod_conc,
        mode='lines', name=f'修正プラン ({new_dose}mg)',
        line=dict(color='green', width=3)
    ))

fig.add_hrect(y0=10, y1=20, fillcolor="green", opacity=0.05, line_width=0, annotation_text="Trough 10-20")

tick_vals = []
tick_texts = []
for d in range(0, int(times[-1]/24) + 1):
    tick_vals.append(d)
    tick_texts.append(f"Day {d+1}")

fig.update_layout(
    title="Concentration vs Time",
    xaxis_title="Days", yaxis_title="µg/mL",
    xaxis=dict(tickvals=tick_vals, ticktext=tick_texts),
    height=450,
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
with st.expander("📚 目標トラフとMICに関する解説 (Guidelines)", expanded=True):
    st.markdown("""
    ### 🎯 目標トラフ濃度 (Target Trough)
    
    VCMの治療目標は **AUC/MIC $\ge$ 400** ですが、実臨床ではトラフ濃度が代替指標として用いられます。
    
    | 感染症の重症度 | 目標トラフ濃度 | 備考 |
    | :--- | :--- | :--- |
    | **通常・軽症** | **10 - 15 µg/mL** | 尿路感染症、蜂窩織炎など |
    | **重症・複雑性** | **15 - 20 µg/mL** | 肺炎、敗血症、心内膜炎、骨髄炎、MRSA感染症 |
    
    ---
    ### 🦠 MIC (最小発育阻止濃度) との兼ね合い
    
    **AUC/MIC $\ge$ 400** を達成できるかどうかが鍵となります。
    
    * **MIC $\le$ 1.0 µg/mL の場合:**
        * 通常の目標トラフ (15-20 µg/mL) で十分なAUCが確保できます。
    
    * **MIC = 2.0 µg/mL の場合 (重要):**
        * 理論上、AUC/MIC $\ge$ 400 を達成するには **AUC $\ge$ 800** が必要になります。
        * これを達成しようとすると、トラフ濃度を **20 µg/mL 以上** に維持しなければならず、**腎障害や聴覚障害のリスクが著しく増大**します。
        * 💡 **推奨:** VCMの増量で粘るのではなく、**リネゾリド (LZD) や ダプトマイシン (DAP)** など、他の抗MRSA薬への変更を強く推奨します。
    
    ---
    ### 💡 自動計算機能
    患者情報を入力すると、体重とCCrに基づいて推奨投与量・間隔が自動でセットされます。
    """)
