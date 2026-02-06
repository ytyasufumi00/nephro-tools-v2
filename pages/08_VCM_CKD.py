import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. 計算ロジック (保存期CKD VCM)
# ==========================================
class VCMSimulationCKD:
    def __init__(self, weight, ccr, params):
        self.weight = weight
        self.ccr = ccr
        self.Vd = params['Vd_per_kg'] * weight
        
        # kel = (0.00083 * CCr + 0.0044) * factor
        # ※eGFR直接入力の場合はCCrの代わりにeGFR値がそのまま入る想定
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

# --- CSS ---
st.markdown("""
<style>
@media only screen and (max-width: 600px) {
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    div[data-testid="stSidebar"] button { padding: 0.2rem 0.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# --- セッションステート初期化 (14回分) ---
NUM_SLOTS = 14
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

# 共通項目: 体重
weight = st.sidebar.number_input("体重 (kg)", 30.0, 150.0, 60.0, 1.0)

# 入力モード選択
input_mode = st.sidebar.radio("腎機能入力方法", ["年齢・性別・Creから計算", "eGFRを直接入力"])

ccr_for_sim = 0.0

if input_mode == "年齢・性別・Creから計算":
    age = st.sidebar.number_input("年齢", 18, 100, 70)
    sex = st.sidebar.radio("性別", ["男性", "女性"], horizontal=True)
    cr = st.sidebar.number_input("Cr (mg/dL)", 0.3, 15.0, 1.2, 0.1)

    # 計算ロジック
    def calc_ccr(age, sex, cr, weight):
        val = ((140 - age) * weight) / (72 * cr)
        return val * 0.85 if sex == "女性" else val

    ccr_calc = calc_ccr(age, sex, cr, weight)
    eGFR_calc = 194 * (cr**-1.094) * (age**-0.287) * (0.739 if sex == "女性" else 1.0)
    
    st.sidebar.info(f"🧬 **CCr: {ccr_calc:.1f} mL/min**\n\n(eGFR: {eGFR_calc:.1f})")
    ccr_for_sim = ccr_calc # シミュレーションにはCCrを使用

else:
    # eGFR直接入力
    egfr_input = st.sidebar.number_input("eGFR (mL/min)", 0.0, 150.0, 45.0, 1.0, help="本来Matzke式はCCrを用いますが、便宜上eGFR値を代用して計算します。")
    st.sidebar.info(f"🧬 入力値 **{egfr_input:.1f}** を腎機能指標として使用")
    ccr_for_sim = egfr_input # シミュレーションにはeGFRをそのまま使用


# --- サイドバー: 投与設定 (個別入力) ---
st.sidebar.markdown("---")
st.sidebar.header("2. 投与スケジュール")

# 推奨間隔
rec_interval = 24
if ccr_for_sim > 60: rec_interval = 12
elif 40 <= ccr_for_sim <= 60: rec_interval = 24
elif 20 <= ccr_for_sim < 40: rec_interval = 48
else: rec_interval = 72

interval = st.sidebar.number_input("投与間隔 (時間)", 12, 168, rec_interval, 12, help="カレンダー表示の基準となる間隔です")
infusion_hr = st.sidebar.selectbox("点滴時間", [1.0, 2.0], index=0)

st.sidebar.markdown("##### 💉 投与量入力 (連動)")
st.sidebar.caption("※値を変更すると以降も自動更新されます")

# 入力ループ
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

# セッションステートから投与リスト作成
current_dose_list = [st.session_state[f'ckd_dose_{i}'] for i in range(1, NUM_SLOTS + 1)]

# シミュレーション
times, conc_base = sim.run_sim_schedule(current_dose_list, interval, infusion_time=infusion_hr)

# AUC24 (定常状態と仮定して最後の投与量を使用)
last_dose = current_dose_list[-1]
daily_dose_equiv = last_dose * (24 / interval)
auc24_initial = sim.calc_auc24_steady(daily_dose_equiv)

# ==========================================
# 4. TDM解析エリア
# ==========================================
st.subheader("🩸 TDM解析 / AUC評価")

col_t1, col_t2 = st.columns([1.5, 2.5])

# 入力モード
has_measured = st.radio("入力モード", ["シミュレーションのみ", "TDM実測値あり"], horizontal=True, label_visibility="collapsed") == "TDM実測値あり"

sim_fitted = None
mod_conc = None
new_dose = 0

with col_t1:
    if has_measured:
        st.markdown("##### 📝 実測値")
        timing_mode = st.selectbox("採血タイミング", ["投与直前 (トラフ)", "投与終了後 (ピーク等)"])
        target_dose_num = st.number_input("何回目の投与？", 2, NUM_SLOTS, 3)
        
        # サンプリング時間計算
        t_start_dose = (target_dose_num - 1) * interval
        if timing_mode == "投与直前 (トラフ)":
            sampling_time = t_start_dose
        else:
            # float変換してエラー回避
            hours_after = st.number_input("投与終了から何時間後？", 0.0, float(interval), 2.0, 0.5)
            sampling_time = t_start_dose + infusion_hr + hours_after
            
        st.caption(f"→ 開始から {sampling_time:.1f} 時間後")
        measured_val = st.number_input("実測値 (µg/mL)", 0.0, 100.0, 0.0, 0.1)
    
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
            
            # フィッティング線
            sim_fit_obj = VCMSimulationCKD(weight, ccr_for_sim, pk_params)
            sim_fit_obj.kel_base = fitted_kel
            sim_fit_obj.cl = sim_fit_obj.Vd * fitted_kel
            _, sim_fitted = sim_fit_obj.run_sim_schedule(current_dose_list, interval, infusion_hr)
            
            # 推定AUC
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

    # 提案ロジック
    if (has_measured and measured_val > 0) or not has_measured:
        st.markdown("##### 💡 投与量提案")
        
        # 必要1日量計算
        if target_mode == "AUC24 (推奨)":
            req_daily_dose = target_auc * used_sim_obj.cl
        else:
            # トラフ比例計算
            base_data = sim_fitted if sim_fitted is not None else conc_base
            curr_trough = base_data[-1] # 末尾の定常状態
            if curr_trough > 0:
                req_daily_dose = daily_dose_equiv * (target_trough / curr_trough)
            else:
                req_daily_dose = daily_dose_equiv
        
        # 1回量換算
        suggest_raw = req_daily_dose / (24 / interval)
        new_dose = round(suggest_raw / 100) * 100
        
        if new_dose != last_dose:
            st.success(f"推奨維持量: **{new_dose} mg** (間隔 {interval}h のまま)")
            
            # 修正プランシミュレーション (測定回以降を変更)
            mod_dose_list = current_dose_list.copy()
            
            # 変更開始ポイント
            if has_measured:
                start_mod_idx = int(target_dose_num) # 次回から
                if start_mod_idx >= NUM_SLOTS: start_mod_idx = NUM_SLOTS - 1
            else:
                start_mod_idx = 1 # 2回目(維持量)から
            
            for k in range(start_mod_idx, NUM_SLOTS):
                mod_dose_list[k] = new_dose
            
            # シミュレーション
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

# 1. オレンジ: 現在の入力値からの予測 (初期 or フィッティングなし)
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

# 実測点
if has_measured and measured_val > 0:
    fig.add_trace(go.Scatter(
        x=[sampling_time/24], y=[measured_val],
        mode='markers', name='実測値',
        marker=dict(color='red', size=12, symbol='x')
    ))

# 2. 緑: 修正プラン
if mod_conc is not None:
    fig.add_trace(go.Scatter(
        x=times/24, y=mod_conc,
        mode='lines', name=f'修正プラン ({new_dose}mg)',
        line=dict(color='green', width=3)
    ))

# 帯
fig.add_hrect(y0=10, y1=20, fillcolor="green", opacity=0.05, line_width=0, annotation_text="Trough 10-20")

# X軸ラベル生成 (Day 1, Day 2...)
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

# AUC解説
st.markdown("---")
with st.expander("📚 AUCガイドラインとTDMのポイント", expanded=True):
    st.markdown("""
    ### 🎯 AUC24 目標: 400 - 600 μg･h/mL
    * **有効性:** AUC/MIC $\ge$ 400
    * **安全性:** AUC $\ge$ 600-700 で腎障害リスク増
    
    保存期CKDでは半減期が延長しているため、トラフ値だけでなくAUCを確認して蓄積を防ぐことが重要です。
    サイドバーで**個別の投与量**を入力すると、グラフ（オレンジ線）に即座に反映されます。
    """)
