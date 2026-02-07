import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. 計算ロジック (VCM専用)
# ==========================================
class VCMSimulation:
    def __init__(self, weight, params):
        self.weight = weight
        self.V1 = params['V1_per_kg'] * weight
        self.V2 = params['V2_per_kg'] * weight
        self.Q = params['Q'] 
        self.t_half = params['T_half_off']
        
        total_V = self.V1 + self.V2
        t_half_min = self.t_half * 60
        if t_half_min > 0:
            self.k_el = (0.693 * total_V) / (t_half_min * self.V1)
        else:
            self.k_el = 0
            
        self.k12 = self.Q / self.V1
        self.k21 = self.Q / self.V2

    def calculate_hd_clearance(self, Qb, Qd, KoA):
        if Qb == 0: return 0
        ratio = Qb / Qd
        Z = (KoA / Qb) * (1 - ratio)
        if abs(1 - ratio) < 0.001:
            clearance = Qb * (KoA / (KoA + Qb))
        else:
            exp_z = np.exp(Z)
            clearance = Qb * (exp_z - 1) / (exp_z - ratio)
        return clearance / 1000.0 # mL/min -> L/min

    def run_sim(self, schedule_events, total_hours=336, start_adjust=None):
        """
        start_adjust: {'idx': time_index, 'conc': value}
        指定したタイミングで濃度を強制的に実測値に合わせるオプション
        """
        time_steps = np.arange(0, total_hours * 60, 1) # 分単位
        conc_v1 = np.zeros(len(time_steps))
        
        A1 = 0.0
        A2 = 0.0
        
        hd_map = np.zeros(len(time_steps))
        infusion_map = np.zeros(len(time_steps))
        
        for ev in schedule_events:
            start = int(ev['start'])
            end = int(ev['start'] + ev['duration'])
            start = max(0, start)
            end = min(len(time_steps), end)
            
            if ev['type'] == 'hd':
                hd_map[start:end] = ev['val'] 
            elif ev['type'] == 'dose':
                rate = ev['val'] / ev['duration']
                infusion_map[start:end] += rate

        for i in range(len(time_steps)):
            # --- 【修正点】実測値による状態リセット ---
            if start_adjust and i == start_adjust['idx']:
                measured_val = start_adjust['conc']
                current_conc = A1 / self.V1 if self.V1 > 0 else 0
                
                # A1を実測値に合わせる。A2(組織内量)も比率を保って補正する
                if current_conc > 0:
                    ratio = measured_val / current_conc
                    A1 = measured_val * self.V1
                    A2 = A2 * ratio
                else:
                    A1 = measured_val * self.V1
                    # A2は不明だが、ゼロからの立ち上がりでない限り維持または0
            # ------------------------------------------

            conc_v1[i] = A1 / self.V1
            
            trans = (self.k21 * A2) - (self.k12 * A1)
            elim = self.k_el * A1
            rem_hd = (A1 / self.V1) * hd_map[i]
            input_drug = infusion_map[i]
            
            A1 = A1 + trans - elim - rem_hd + input_drug
            A2 = A2 - trans
            if A1 < 0: A1 = 0
            
        return time_steps, conc_v1

# パラメータフィッティング
def fit_parameter_robust(target_conc, target_idx, current_params, weight, events, mode='trough'):
    best_params = current_params.copy()
    
    def get_pred_conc(params):
        sim = VCMSimulation(weight, params)
        _, c = sim.run_sim(events)
        return c[target_idx] if target_idx < len(c) else 0

    # Phase 1: T_half
    low_t, high_t = 5.0, 1000.0
    for _ in range(20):
        mid_t = (low_t + high_t) / 2
        best_params['T_half_off'] = mid_t
        pred = get_pred_conc(best_params)
        if pred < target_conc: low_t = mid_t
        else: high_t = mid_t
            
    final_pred_p1 = get_pred_conc(best_params)
    error_p1 = abs(final_pred_p1 - target_conc) / target_conc if target_conc > 0 else 0
    if error_p1 < 0.05:
        return best_params, 'T_half_off'

    # Phase 2: V1
    low_v, high_v = 0.05, 1.0
    for _ in range(20):
        mid_v = (low_v + high_v) / 2
        best_params['V1_per_kg'] = mid_v
        pred = get_pred_conc(best_params)
        if pred < target_conc: high_v = mid_v
        else: low_v = mid_v
            
    return best_params, 'V1_per_kg (Combined)'

# ==========================================
# 2. UI & アプリケーション
# ==========================================

st.set_page_config(page_title="VCM TDM Sim", layout="wide")
st.title("💊 バンコマイシン(VCM) 2週間シミュレーター")

# --- CSS ---
st.markdown("""
<style>
@media only screen and (max-width: 600px) {
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    div[data-testid="stSidebar"] button { padding: 0.2rem 0.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# --- 定数 ---
DOSE_SLOTS = 6

# --- 自動推奨ロジック ---
def auto_calc_hd_recommendation():
    w = st.session_state.get('weight_input', 60.0)
    rec_load = w * 20.0
    rec_load = round(rec_load / 50) * 50 
    if rec_load > 2000: rec_load = 2000.0 
    rec_maint = w * 10.0
    rec_maint = round(rec_maint / 50) * 50
    if rec_maint > 1000: rec_maint = 1000.0
    
    st.session_state['dose_1'] = float(rec_load)
    for i in range(2, DOSE_SLOTS + 1):
        st.session_state[f'dose_{i}'] = float(rec_maint)

# --- セッションステート初期化 ---
for i in range(1, DOSE_SLOTS + 1):
    key = f'dose_{i}'
    if key not in st.session_state:
        st.session_state[key] = 1000.0 if i == 1 else 500.0

# --- 連動ロジック ---
def update_dose_cascade(target_key, increment):
    new_val = st.session_state[target_key] + increment
    if new_val < 0: new_val = 0.0
    st.session_state[target_key] = new_val
    try:
        current_idx = int(target_key.split('_')[-1])
        for i in range(current_idx + 1, DOSE_SLOTS + 1):
            st.session_state[f'dose_{i}'] = new_val
    except:
        pass

# --- サイドバー設定 ---
st.sidebar.header("1. 患者・透析条件")

weight = st.sidebar.number_input(
    "体重 (kg)", 30.0, 150.0, 60.0, 1.0, 
    key='weight_input', on_change=auto_calc_hd_recommendation
)

qb = st.sidebar.slider("血流量 Qb (mL/min)", 150, 400, 200, step=10)
qd = st.sidebar.slider("透析液流量 Qd (mL/min)", 400, 600, 500, step=50)
hd_hours = st.sidebar.slider("透析時間 (時間)", 3.0, 5.0, 4.0, 0.5)

with st.sidebar.expander("詳細PKパラメータ", expanded=False):
    v1_pk = st.slider("V1 (L/kg)", 0.1, 0.5, 0.25, 0.01)
    v2_pk = st.slider("V2 (L/kg)", 0.3, 1.2, 0.65, 0.01)
    t_half_pk = st.number_input("非透析時半減期 (h)", value=70.0, step=5.0)
    q_inter = st.number_input("組織間移行Q (L/min)", value=0.15)
    koa = st.number_input("膜KoA", value=350)

# --- スケジュール設定 ---
st.sidebar.markdown("---")
st.sidebar.subheader("📅 透析スケジュール")
hd_pattern = st.sidebar.selectbox("透析パターン", ["月・水・金", "火・木・土"])

weekdays_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
if hd_pattern == "月・水・金":
    start_options = ["月曜日 (Mon)", "水曜日 (Wed)", "金曜日 (Fri)"]
    pattern_indices = [0, 2, 4]
else:
    start_options = ["火曜日 (Tue)", "木曜日 (Thu)", "土曜日 (Sat)"]
    pattern_indices = [1, 3, 5]

start_day_label = st.sidebar.selectbox("開始曜日 (Day 1)", start_options)

if "(Mon)" in start_day_label: start_day_idx = 0
elif "(Tue)" in start_day_label: start_day_idx = 1
elif "(Wed)" in start_day_label: start_day_idx = 2
elif "(Thu)" in start_day_label: start_day_idx = 3
elif "(Fri)" in start_day_label: start_day_idx = 4
elif "(Sat)" in start_day_label: start_day_idx = 5
else: start_day_idx = 6

hd_days_offset = []
hd_labels = []
current_day_idx = start_day_idx
cum_days = 0

for i in range(DOSE_SLOTS): 
    hd_days_offset.append(cum_days)
    label = f"Day {cum_days + 1} ({weekdays_map[current_day_idx]})"
    hd_labels.append(label)
    
    next_day_candidates = [d for d in pattern_indices if d > current_day_idx]
    if next_day_candidates:
        next_day_idx = next_day_candidates[0]
        gap = next_day_idx - current_day_idx
    else:
        next_day_idx = pattern_indices[0]
        gap = (pattern_indices[0] + 7) - current_day_idx
    cum_days += gap
    current_day_idx = next_day_idx

hd_days_offset_next = cum_days
next_label = f"Day {cum_days + 1} ({weekdays_map[current_day_idx]})"


# --- 投与スケジュール入力UI ---
st.sidebar.markdown("---")
st.sidebar.subheader("投与計画 (50mg調整)")
st.sidebar.caption("※患者情報を変更すると推奨量が自動入力されます")

def dose_input_row(label, key):
    st.sidebar.markdown(f"**{label}**")
    c1, c2, c3 = st.sidebar.columns([1, 2, 1])
    with c1: st.button("－", key=f"dec_{key}", on_click=update_dose_cascade, args=(key, -50), use_container_width=True)
    with c2: st.number_input(label, key=key, step=50.0, label_visibility="collapsed")
    with c3: st.button("＋", key=f"inc_{key}", on_click=update_dose_cascade, args=(key, 50), use_container_width=True)

for i in range(DOSE_SLOTS):
    dose_input_row(hd_labels[i], f'dose_{i+1}')


# ==========================================
# 3. シミュレーション準備
# ==========================================
init_params = {'V1_per_kg': v1_pk, 'V2_per_kg': v2_pk, 'Q': q_inter, 'T_half_off': t_half_pk}
sim_dummy = VCMSimulation(weight, init_params)
cl_hd_val = sim_dummy.calculate_hd_clearance(qb, qd, koa)
hd_duration_min = hd_hours * 60
infusion_duration = 60
t_start = 9 

def build_events(doses_list, offsets):
    evs = []
    hd_start_times = []
    for i, day_offset in enumerate(offsets):
        t_hd = (t_start + day_offset * 24) * 60
        hd_start_times.append(t_hd)
        evs.append({'type': 'hd', 'start': t_hd, 'duration': hd_duration_min, 'val': cl_hd_val})
        if i < len(doses_list) and doses_list[i] > 0:
            t_dose = t_hd + hd_duration_min
            evs.append({'type': 'dose', 'start': t_dose, 'duration': infusion_duration, 'val': doses_list[i]})
    return evs, hd_start_times

current_doses = [st.session_state[f'dose_{i+1}'] for i in range(DOSE_SLOTS)]
events_current, hd_times = build_events(current_doses, hd_days_offset)
t_next_hd = (t_start + hd_days_offset_next * 24) * 60
hd_times.append(t_next_hd)

sim_engine = VCMSimulation(weight, init_params)
time_steps, sim_conc = sim_engine.run_sim(events_current, total_hours=(hd_days_offset_next + 2) * 24)

# ==========================================
# 4. TDM入力エリア
# ==========================================
st.subheader("🩸 実測値 (TDM) の入力")

col_in1, col_in2, col_in3 = st.columns([2, 1.5, 1.5])

with col_in1:
    tdm_options = [f"{l} 透析前" for l in hd_labels] + [f"{next_label} 透析前"]
    selected_label_full = st.selectbox("測定ポイント", tdm_options, index=1)
    selected_idx = tdm_options.index(selected_label_full)

with col_in2:
    measured_val = st.number_input("血中濃度 (µg/mL)", value=0.0, step=0.1)

with col_in3:
    target_val = st.number_input("目標値 (µg/mL)", value=15.0, step=1.0)

# ==========================================
# 5. パラメータ解析 & 修正プラン
# ==========================================
fitted_params = None
sim_conc_fitted = None
sim_conc_modified = None
events_modified = None
modified_dose = 0
future_dose_days = []

if measured_val > 0:
    target_min = hd_times[selected_idx]
    target_idx_sim = int(target_min)
    
    # 1. パラメータ逆算
    with st.spinner("パラメータ解析中..."):
        fitted_params, adjusted_key = fit_parameter_robust(measured_val, target_idx_sim, init_params, weight, events_current, 'trough')
    
    # 2. 成り行きシミュレーション (【修正】実測値でリセット)
    sim_fit = VCMSimulation(weight, fitted_params)
    start_adj = {'idx': target_idx_sim, 'conc': measured_val}
    _, sim_conc_fitted = sim_fit.run_sim(events_current, total_hours=(hd_days_offset_next + 2) * 24, start_adjust=start_adj)

    # 3. 修正プランの提案
    st.markdown("---")
    st.subheader("💡 投与量変更シミュレーション")

    start_dose_idx = selected_idx
    if start_dose_idx > 5: start_dose_idx = 5 

    future_dose_days = [l.split(" ")[0] + " " + l.split(" ")[1] for l in hd_labels[start_dose_idx:]] 
    
    # 推奨投与量の計算
    next_idx = min(selected_idx + 1, 6)
    target_sim_idx = int(hd_times[next_idx])
    pred_next_trough = sim_conc_fitted[target_sim_idx] if target_sim_idx < len(sim_conc_fitted) else 0
    
    current_planned_dose = current_doses[min(start_dose_idx, 5)]
    
    if pred_next_trough > 0:
        ratio = target_val / pred_next_trough
        suggest_dose = current_planned_dose * ratio
        suggest_dose = round(suggest_dose / 50) * 50
    else:
        suggest_dose = current_planned_dose

    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        modified_dose = st.number_input(
            f"修正投与量 (mg)", 
            value=float(suggest_dose), 
            step=50.0,
            help=f"{future_dose_days} の投与量が一括変更されます"
        )
    with col_m2:
        if len(future_dose_days) > 0:
            st.info(f"**変更対象:** {future_dose_days[0]} 以降\n\n"
                    f"実測値に基づく推奨は **{suggest_dose:.0f} mg** です。")
        else:
            st.warning("シミュレーション期間内の投与予定は終了しています。")

    # 4. 修正プランシミュレーション (【修正】実測値でリセット)
    modified_doses = current_doses.copy()
    for i in range(start_dose_idx, DOSE_SLOTS):
        modified_doses[i] = modified_dose
        
    events_modified, _ = build_events(modified_doses, hd_days_offset)
    
    sim_mod = VCMSimulation(weight, fitted_params)
    _, sim_conc_modified = sim_mod.run_sim(events_modified, total_hours=(hd_days_offset_next + 2) * 24, start_adjust=start_adj)


# ==========================================
# 6. グラフ描画 (Plotly)
# ==========================================
st.markdown("---")
st.subheader("📈 2週間予測グラフ")

x_days = time_steps / (60 * 24)
fig = go.Figure()

# 1. 初期設定
fig.add_trace(go.Scatter(
    x=x_days, y=sim_conc, 
    mode='lines', name='初期計画 (Initial Plan)',
    line=dict(color='gray', width=2, dash='dot'),
    opacity=0.6
))

if measured_val > 0:
    # 2. 成り行き
    fig.add_trace(go.Scatter(
        x=x_days, y=sim_conc_fitted,
        mode='lines', name='入力値から予測 (Predicted from Input)',
        line=dict(color='orange', width=2)
    ))
    
    # 3. 修正プラン
    fig.add_trace(go.Scatter(
        x=x_days, y=sim_conc_modified,
        mode='lines', name=f'修正プラン ({modified_dose}mg)',
        line=dict(color='green', width=3)
    ))

    # 実測点
    meas_day = hd_times[selected_idx] / (60 * 24)
    fig.add_trace(go.Scatter(
        x=[meas_day], y=[measured_val],
        mode='markers', name='実測値 (Measured)',
        marker=dict(color='red', size=15, symbol='x')
    ))

# 目標範囲
fig.add_hrect(y0=10, y1=20, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Target")

# HD帯
for t_hd in hd_times[:-1]:
    start = t_hd
    end = start + hd_duration_min
    fig.add_vrect(x0=start/(60*24), x1=end/(60*24), fillcolor="red", opacity=0.1, line_width=0)

tick_vals = []
tick_texts = []
all_labels = hd_labels + [next_label]
all_offsets = hd_days_offset + [hd_days_offset_next]

for i, offset in enumerate(all_offsets):
    tick_vals.append(offset)
    txt = all_labels[i].replace("Day ", "D").replace("Monday", "Mon").replace("Tuesday", "Tue").replace("Wednesday", "Wed").replace("Thursday", "Thu").replace("Friday", "Fri").replace("Saturday", "Sat")
    tick_texts.append(txt)

fig.update_layout(
    title="Concentration vs Time",
    xaxis_title="Days", yaxis_title="Concentration (µg/mL)",
    xaxis=dict(tickvals=tick_vals, ticktext=tick_texts),
    height=450, 
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# 7. メトリクス
if measured_val > 0:
    st.info(f"📊 **解析結果:** 実測値 {measured_val} µg/mL に合わせるため、"
            f"消失半減期を **{fitted_params['T_half_off']:.1f} 時間** "
            f"(初期値 {init_params['T_half_off']} 時間) として計算しました。")
else:
    st.markdown("##### 📅 透析前トラフ予測値 (初期計画)")
    cols = st.columns(3) 
    for i, col in enumerate(cols + st.columns(3)):
        if i < 6:
            idx = int(hd_times[i])
            val = sim_conc[idx] if idx < len(sim_conc) else 0
            col.metric(hd_labels[i].split(" ")[1], f"{val:.1f}") 

# 目標トラフ解説
st.markdown("---")
with st.expander("📚 目標トラフとMICに関する解説", expanded=True):
    st.markdown("""
    ### 🎯 推奨投与量（初期設定）
    * **初回負荷量:** 実体重 × **20 mg/kg**
    * **維持投与量:** 実体重 × **10 mg/kg** (透析終了ごと)
    
    上記計算式に基づき、体重を入力すると自動的に推奨量がセットされます。
    
    ### ⚠️ MIC = 2.0 µg/mL の場合
    VCMで治療目標(AUC/MIC $\ge$ 400)を達成しようとすると、トラフ濃度を20 µg/mL以上に保つ必要があり、副作用リスクが高まります。
    他剤（リネゾリド、ダプトマイシンなど）への変更を強く推奨します。
    """)
