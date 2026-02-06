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
        
        # 分布容積 Vd
        self.Vd = params['Vd_per_kg'] * weight
        
        # 消失速度定数 kel (Matzke式ベース + 補正)
        # kel = 0.00083 * CCr + 0.0044
        self.kel_base = (0.00083 * ccr + 0.0044) * params['kel_factor']
        
        # 半減期
        self.t_half = 0.693 / self.kel_base if self.kel_base > 0 else 999
        
        # クリアランス CL (L/h)
        self.cl = self.Vd * self.kel_base

    def run_sim(self, doses, intervals, num_doses=14, infusion_time=1.0):
        # doses: [初回量, 維持量]
        # intervals: [初回間隔, 維持間隔]
        
        total_hours = num_doses * intervals[1] + 48 
        time_steps = np.arange(0, total_hours * 60, 60) # 1時間刻み
        conc_curve = np.zeros(len(time_steps))
        
        # 重ね合わせ法
        for i in range(num_doses):
            # 投与量とタイミング
            if i == 0:
                d = doses[0]
                t_start = 0
            else:
                d = doses[1]
                t_start = intervals[0] + (i - 1) * intervals[1]
            
            t_inf_min = infusion_time * 60
            ke = self.kel_base / 60 # 分単位
            
            for j, t_min in enumerate(time_steps):
                t_from_start = t_min - (t_start * 60)
                
                if t_from_start < 0:
                    continue
                
                if t_from_start <= t_inf_min:
                    # 点滴中
                    rate = d / t_inf_min
                    val = (rate / (self.Vd * ke)) * (1 - np.exp(-ke * t_from_start))
                else:
                    # 点滴終了後
                    t_post = t_from_start - t_inf_min
                    rate = d / t_inf_min
                    c_peak_calc = (rate / (self.Vd * ke)) * (1 - np.exp(-ke * t_inf_min))
                    val = c_peak_calc * np.exp(-ke * t_post)
                
                conc_curve[j] += val
                
        return time_steps / 60, conc_curve

    def calc_auc24_steady(self, daily_dose):
        # 定常状態のAUC24 = 1日投与量 / CL
        # ※VCMのTDMガイドラインではこの計算（線形1-comp近似）が一般的
        if self.cl == 0: return 0
        return daily_dose / self.cl

# パラメータフィッティング
def fit_kel_from_measured(target_val, measured_hour, weight, dose_history, Vd_est, infusion_time=1.0):
    """
    実測値(measured_hour時点)に合うようにkelを逆算
    """
    low_k, high_k = 0.001, 0.5 
    best_k = low_k
    
    # 仮のパラメータ辞書
    dummy_params = {'Vd_per_kg': Vd_est, 'kel_factor': 1.0}
    target_idx = int(measured_hour) # run_simは1時間刻みなのでindex=時間(h)
    
    for _ in range(20):
        mid_k = (low_k + high_k) / 2
        
        sim = VCMSimulationCKD(weight, 0, dummy_params)
        sim.kel_base = mid_k # 強制上書き
        
        # シミュレーション実行
        t, c = sim.run_sim([dose_history['load'], dose_history['maint']], 
                           [dose_history['interval'], dose_history['interval']], 
                           num_doses=14, infusion_time=infusion_time)
        
        # ターゲット時間の濃度取得 (インデックス範囲チェック)
        if target_idx < len(c):
            pred = c[target_idx]
        else:
            pred = 0
        
        if pred > target_val:
             # 濃度が高すぎる -> 排泄を速くしたい -> kを大きく
             low_k = mid_k
        else:
             high_k = mid_k
             
    return (low_k + high_k) / 2

# ==========================================
# 2. UI & アプリケーション
# ==========================================

st.set_page_config(page_title="VCM CKD Sim", layout="wide")
st.title("💊 VCM 投与設計 (保存期CKD)")

# --- モバイルCSS ---
st.markdown("""
<style>
@media only screen and (max-width: 600px) {
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    div[data-testid="stSidebar"] button { padding: 0.2rem 0.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# --- サイドバー: 患者情報 ---
st.sidebar.header("1. 患者情報")
age = st.sidebar.number_input("年齢", 18, 100, 70)
sex = st.sidebar.radio("性別", ["男性", "女性"], horizontal=True)
weight = st.sidebar.number_input("体重 (kg)", 30.0, 150.0, 60.0, 1.0)
cr = st.sidebar.number_input("Cr (mg/dL)", 0.3, 15.0, 1.2, 0.1)

# 腎機能計算
def calc_ccr(age, sex, cr, weight):
    val = ((140 - age) * weight) / (72 * cr)
    return val * 0.85 if sex == "女性" else val

ccr = calc_ccr(age, sex, cr, weight)
eGFR = 194 * (cr**-1.094) * (age**-0.287) * (0.739 if sex == "女性" else 1.0)

st.sidebar.markdown("---")
st.sidebar.info(f"🧬 **CCr: {ccr:.1f} mL/min**\n\n(eGFR: {eGFR:.1f})")

# --- サイドバー: 投与パラメータ ---
st.sidebar.header("2. 投与スケジュール")

# ノモグラム簡易推奨
rec_interval = 24
if ccr > 60: rec_interval = 12
elif 40 <= ccr <= 60: rec_interval = 24
elif 20 <= ccr < 40: rec_interval = 48
else: rec_interval = 72

st.sidebar.caption(f"💡 CCr {ccr:.1f} での目安: {rec_interval}時間ごと")

dose_load = st.sidebar.number_input("初回負荷量 (mg)", 500, 3000, 1500, 100)
dose_maint = st.sidebar.number_input("維持投与量 (mg)", 250, 2000, 1000, 100)
interval = st.sidebar.number_input("投与間隔 (時間)", 12, 168, rec_interval, 12)
infusion_hr = st.sidebar.selectbox("点滴時間", [1.0, 2.0], index=0, help="シミュレーション上の点滴時間")

with st.sidebar.expander("詳細PKパラメータ"):
    vd_pk = st.slider("分布容積 Vd (L/kg)", 0.4, 1.0, 0.7, 0.05)
    kel_factor = st.slider("排泄係数補正", 0.5, 1.5, 1.0, 0.1)

# ==========================================
# 3. シミュレーション実行 (初期計画)
# ==========================================
pk_params = {'Vd_per_kg': vd_pk, 'kel_factor': kel_factor}
sim = VCMSimulationCKD(weight, ccr, pk_params)

# 2週間分 (336h)
num_doses = int(336 / interval) + 1
times, conc_base = sim.run_sim([dose_load, dose_maint], [interval, interval], num_doses=num_doses, infusion_time=infusion_hr)

# 初期計画のAUC24計算 (維持量での定常状態)
daily_dose_initial = dose_maint * (24 / interval)
auc24_initial = sim.calc_auc24_steady(daily_dose_initial)

# ==========================================
# 4. TDM解析 & AUC評価エリア
# ==========================================
st.subheader("🩸 TDM解析 / AUC評価")

# 入力モード選択
input_type = st.radio("入力タイプ", ["TDM実測値あり", "シミュレーションのみ"], horizontal=True, label_visibility="collapsed")

has_measured = (input_type == "TDM実測値あり")
sim_fitted = None
mod_conc = None
new_dose = 0

col_t1, col_t2 = st.columns([1.5, 2.5])

with col_t1:
    if has_measured:
        st.markdown("##### 📝 実測値入力")
        # タイミング詳細設定
        timing_mode = st.selectbox("採血タイミング", ["投与直前 (トラフ)", "投与終了後 (ピーク等)"])
        
        target_dose_num = st.number_input("何回目の投与？", 2, 20, 3)
        
        if timing_mode == "投与直前 (トラフ)":
            # N回目の直前 = (N-1)回目の間隔終了時
            sampling_time = (target_dose_num - 1) * interval
            st.caption(f"→ 開始から {sampling_time} 時間後")
        else:
            # 投与終了後
            hours_after = st.number_input("投与終了から何時間後？", 0.0, interval, 2.0, 0.5)
            # N回目の開始 + 点滴時間 + 経過時間
            # N回目の開始 = 初回(0) + (N-1)*interval
            # 投与は初回から数えて(0, 1, 2...)なので、target_dose_num(1始まり)に注意
            # 1回目(start=0) -> 終了1h -> 1+2=3h後
            start_time_of_dose = 0 if target_dose_num == 1 else interval * (target_dose_num - 1) # 初回だけload間隔だが簡易的にinterval
            # 初回と2回目以降の間隔が違う場合ここはずれるが、CKDでは通常loadの次はmaint間隔で進む
            # 正確には: 
            if target_dose_num == 1:
                 t_start = 0
            else:
                 t_start = interval * (target_dose_num - 1) # 初回もintervalだったと仮定した簡易計算
                 
            sampling_time = t_start + infusion_hr + hours_after
            st.caption(f"→ 開始から {sampling_time} 時間後")
            
        measured_val = st.number_input("実測値 (µg/mL)", 0.0, 100.0, 0.0, 0.1)
    
    else:
        st.info("実測値がない場合、現在の患者パラメータ(CCr, Vd)に基づく予測が表示されます。")
        measured_val = 0

    st.markdown("---")
    st.markdown("##### 🎯 目標設定")
    target_mode = st.radio("目標指標", ["AUC24 (推奨)", "トラフ濃度"])
    
    if target_mode == "AUC24 (推奨)":
        target_auc = st.slider("目標AUC24", 400, 600, 450, 10, help="ガイドライン推奨: 400-600 μg･h/mL")
    else:
        target_trough = st.slider("目標トラフ", 10.0, 20.0, 15.0, 0.5)

# --- 解析と提案 ---
with col_t2:
    # パラメータ決定 (実測あれば逆算、なければ推算値)
    if has_measured and measured_val > 0:
        st.markdown("##### 📊 解析結果")
        with st.spinner("パラメータ逆算中..."):
            dose_hist = {'load': dose_load, 'maint': dose_maint, 'interval': interval}
            fitted_kel = fit_kel_from_measured(measured_val, sampling_time, weight, dose_hist, vd_pk, infusion_hr)
            
            # フィッティング結果でシミュレーション
            sim_fit_obj = VCMSimulationCKD(weight, ccr, pk_params)
            sim_fit_obj.kel_base = fitted_kel
            sim_fit_obj.cl = sim_fit_obj.Vd * fitted_kel
            _, sim_fitted = sim_fit_obj.run_sim([dose_load, dose_maint], [interval, interval], num_doses=num_doses, infusion_time=infusion_hr)
            
            # 逆算されたAUC
            auc_current = sim_fit_obj.calc_auc24_steady(daily_dose_initial)
            
            # 表示
            c1, c2 = st.columns(2)
            c1.metric("推定半減期", f"{0.693/fitted_kel:.1f} h", help=f"初期予測: {sim.t_half:.1f} h")
            c2.metric("現在のAUC24", f"{auc_current:.0f}", help="定常状態での推定値")
            
            used_sim_obj = sim_fit_obj # 提案計算に使うオブジェクト
    else:
        # 実測なし（初期予測のまま）
        auc_current = auc24_initial
        used_sim_obj = sim # 初期オブジェクト
        if not has_measured:
            st.metric("予測AUC24 (初期設定)", f"{auc_current:.0f}")

    # 投与量提案
    if (has_measured and measured_val > 0) or not has_measured:
        st.markdown("##### 💡 投与量提案")
        
        # 目標達成に必要な1日投与量
        # Target = DailyDose / CL -> DailyDose = Target * CL
        if target_mode == "AUC24 (推奨)":
            req_daily_dose = target_auc * used_sim_obj.cl
        else:
            # トラフ目標の場合: C_trough = (D/V) * ... の逆算だが
            # 簡易的に: NewDose = CurrentDose * (TargetTrough / CurrentTrough)
            # 現在の定常トラフを取得
            # シミュレーションの最後の方のトラフを見る
            if sim_fitted is not None:
                current_trough = sim_fitted[-1] # 簡易
            else:
                current_trough = conc_base[-1]
            
            if current_trough > 0:
                req_daily_dose = daily_dose_initial * (target_trough / current_trough)
            else:
                req_daily_dose = daily_dose_initial

        # 1回量に換算 (間隔はそのまま)
        # req_dose = req_daily / (24/interval)
        suggest_dose_raw = req_daily_dose / (24 / interval)
        new_dose = round(suggest_dose_raw / 100) * 100 # 100mg丸め
        
        # 提案後のAUC予測
        new_daily = new_dose * (24 / interval)
        pred_new_auc = used_sim_obj.calc_auc24_steady(new_daily)
        
        if new_dose != dose_maint:
            st.success(f"推奨維持量: **{new_dose} mg** (予測AUC24: {pred_new_auc:.0f})")
        else:
            st.success("現在の投与量で目標範囲内です。")

        # 修正プランのシミュレーション
        sim_mod_obj = VCMSimulationCKD(weight, ccr, pk_params)
        sim_mod_obj.kel_base = used_sim_obj.kel_base # 評価されたKelを使う
        # 初回はLoadそのまま、維持量をNewに
        _, mod_conc = sim_mod_obj.run_sim([dose_load, new_dose], [interval, interval], num_doses=num_doses, infusion_time=infusion_hr)


# ==========================================
# 5. グラフ描画
# ==========================================
st.markdown("---")
st.subheader("📈 シミュレーション結果")

fig = go.Figure()

# 1. 初期予測
fig.add_trace(go.Scatter(
    x=times/24, y=conc_base,
    mode='lines', name='初期計画',
    line=dict(color='gray', width=2, dash='dot')
))

# 2. 実測フィッティング
if sim_fitted is not None:
    fig.add_trace(go.Scatter(
        x=times/24, y=sim_fitted,
        mode='lines', name='実測からの推定',
        line=dict(color='orange', width=2)
    ))
    # 実測点
    fig.add_trace(go.Scatter(
        x=[sampling_time/24], y=[measured_val],
        mode='markers', name='実測値',
        marker=dict(color='red', size=12, symbol='x')
    ))

# 3. 修正プラン
if mod_conc is not None:
    fig.add_trace(go.Scatter(
        x=times/24, y=mod_conc,
        mode='lines', name=f'修正プラン ({new_dose}mg)',
        line=dict(color='green', width=3)
    ))

# ガイドライン帯 (トラフ 10-20) - あくまで参考
fig.add_hrect(y0=10, y1=20, fillcolor="green", opacity=0.05, line_width=0, annotation_text="Trough 10-20")

fig.update_layout(
    title="Concentration vs Time",
    xaxis_title="Days", yaxis_title="µg/mL",
    height=450,
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 6. 解説: AUC/MICについて
# ==========================================
st.markdown("---")
with st.expander("📚 AUCガイドラインとTDMのポイント", expanded=True):
    st.markdown("""
    ### 🎯 なぜAUCなのか？
    
    最新のTDMガイドラインでは、有効性と安全性のバランスから **AUC24 (400-600 μg･h/mL)** を目標とすることが推奨されています。
    
    * **有効性:** AUC/MIC $\ge$ 400 が治療成功の指標（MIC=1.0の場合、AUC $\ge$ 400）。
    * **安全性:** AUC $\ge$ 600-700 で腎障害リスクが増加する。
    
    従来の「トラフ濃度」はAUCの代替指標ですが、腎機能や分布容積によっては「トラフは低いのにAUCは高い（＝腎障害リスク）」という乖離が起こりえます。
    特にCKD患者や高齢者では、可能な限りAUCでの評価が推奨されます。
    
    ### 💉 CKD患者での注意点
    
    * **早期の採血:** CKDでは半減期が長く、定常状態到達に1週間以上かかることがあります。しかし、待っていると蓄積過剰になるため、**Day 3-4** などの早期に採血し、シミュレーションで将来の蓄積を予測することが重要です。
    * **実測値の入力:** トラフだけでなく、「透析後」や「ピーク」などの濃度も入力可能です。その際は「投与終了後 ○時間」を選択して入力してください。
    """)
