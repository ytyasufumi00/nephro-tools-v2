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
        
        # 分布容積 Vd (デフォルト 0.7 L/kg)
        self.Vd = params['Vd_per_kg'] * weight
        
        # 消失速度定数 kel (Matzkeの式などを参考にした線形回帰)
        # kel = 0.00083 * CCr + 0.0044 (Matzke et al.)
        # 補正係数(adj)で微調整可能に
        self.kel_base = (0.00083 * ccr + 0.0044) * params['kel_factor']
        
        # 半減期
        self.t_half = 0.693 / self.kel_base if self.kel_base > 0 else 999
        
    def run_sim(self, doses, intervals, num_doses=14, infusion_time=1.0):
        # doses: [初回量, 維持量]
        # intervals: [初回間隔(通常維持と同じ), 維持間隔]
        
        total_hours = num_doses * intervals[1] + 48 # 少し余裕を持たせる
        time_steps = np.arange(0, total_hours * 60, 60) # 1時間刻み(分換算)
        conc_curve = np.zeros(len(time_steps))
        
        # 1-Compartment Modelの重ね合わせ
        for i in range(num_doses):
            # 投与量とタイミング決定
            if i == 0:
                d = doses[0]
                t_start = 0
            else:
                d = doses[1]
                t_start = intervals[0] + (i - 1) * intervals[1]
            
            # 各時点での濃度加算
            # C = (D / Vd) * (1 - e^(-kel*T_inf)) / (T_inf * kel) * e^(-kel * (t - t_end))
            
            t_inf_min = infusion_time * 60
            ke = self.kel_base / 60 # 分単位のkel
            
            for j, t_min in enumerate(time_steps):
                t_from_start = t_min - (t_start * 60)
                
                if t_from_start < 0:
                    continue
                
                if t_from_start <= t_inf_min:
                    # 点滴中: (Rate / (Vd * ke)) * (1 - exp(-ke * t))
                    rate = d / t_inf_min
                    val = (rate / (self.Vd * ke)) * (1 - np.exp(-ke * t_from_start))
                else:
                    # 点滴終了後
                    t_post = t_from_start - t_inf_min
                    # C_peak (at end of infusion)
                    rate = d / t_inf_min
                    c_peak_calc = (rate / (self.Vd * ke)) * (1 - np.exp(-ke * t_inf_min))
                    val = c_peak_calc * np.exp(-ke * t_post)
                
                conc_curve[j] += val
                
        return time_steps / 60, conc_curve # 時間(h), 濃度

# パラメータフィッティング (TDM解析用)
def fit_kel_from_measured(target_val, measured_hour, weight, dose_history, Vd_est):
    """
    実測値(measured_hour時点)に合うようにkelを逆算する
    簡易的に二分探索を行う
    """
    # 探索範囲 (半減期 2h ~ 200h 相当)
    low_k, high_k = 0.003, 0.35 
    best_k = low_k
    
    # 仮のクラスを作ってシミュレーション
    dummy_params = {'Vd_per_kg': Vd_est, 'kel_factor': 1.0} # factorは1固定でkel自体を直接探す
    
    # ターゲット時間のインデックス
    target_idx = int(measured_hour) 
    
    for _ in range(20):
        mid_k = (low_k + high_k) / 2
        
        # シミュレーション実行 (kelを強制上書きして計算)
        # VCMSimulationCKDを少し改造するか、ここで簡易計算
        # 既存クラスを使うためにハック: CCr=0としてkel_factorでmid_kを表現するのは面倒
        # -> 直接計算ロジックを流用
        
        sim = VCMSimulationCKD(weight, 0, dummy_params)
        sim.kel_base = mid_k # 強制上書き
        
        # dose_history = {'load': ..., 'maint': ..., 'interval': ...}
        t, c = sim.run_sim([dose_history['load'], dose_history['maint']], 
                           [dose_history['interval'], dose_history['interval']], 
                           num_doses=10)
        
        pred = c[target_idx] if target_idx < len(c) else 0
        
        if pred > target_val: # 濃度が高すぎる -> 排泄が遅い(kが小さい)と思いきや逆。
             # 濃度が高い = 排泄されていない = kは小さいはず
             # 今のmid_kだと濃度が高い -> もっと排泄させなきゃ -> kを大きく
             low_k = mid_k
        else:
             # 濃度が低い = 排泄されすぎ = kはもっと小さいはず
             high_k = mid_k
             
    return (low_k + high_k) / 2

# ==========================================
# 2. UI & アプリケーション
# ==========================================

st.set_page_config(page_title="VCM CKD Sim", layout="wide")
st.title("💊 VCM 投与設計 (保存期CKD)")

# --- モバイル表示調整CSS ---
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
age = st.sidebar.number_input("年齢", 70, 100, 70)
sex = st.sidebar.radio("性別", ["男性", "女性"], horizontal=True)
weight = st.sidebar.number_input("体重 (kg)", 40.0, 100.0, 60.0, 1.0)
cr = st.sidebar.number_input("Cr (mg/dL)", 0.3, 10.0, 1.2, 0.1)

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

# 推奨投与量の目安ロジック (Matzkeノモグラム簡易版)
rec_interval = 12
rec_dose = 15.0 * weight # 15mg/kg
rec_dose = round(rec_dose / 100) * 100 # 100mg丸め

if ccr > 60:
    rec_interval = 12
elif 40 <= ccr <= 60:
    rec_interval = 24
elif 20 <= ccr < 40:
    rec_interval = 48 # 実際は24-48だが安全側に
else:
    rec_interval = 72 # 透析などのレベル

st.sidebar.caption(f"💡 CCr {ccr:.1f} での目安: {rec_interval}時間ごと")

# 入力欄
dose_load = st.sidebar.number_input("初回負荷量 (mg)", 500, 3000, 1500, 100)
dose_maint = st.sidebar.number_input("維持投与量 (mg)", 250, 2000, 1000, 100)
interval = st.sidebar.number_input("投与間隔 (時間)", 12, 168, rec_interval, 12)

with st.sidebar.expander("詳細PKパラメータ"):
    vd_pk = st.slider("分布容積 Vd (L/kg)", 0.4, 1.0, 0.7, 0.05)
    kel_factor = st.slider("排泄係数補正", 0.5, 1.5, 1.0, 0.1, help="計算上のKelを倍率補正します")

# ==========================================
# 3. シミュレーション実行 (初期計画)
# ==========================================
pk_params = {'Vd_per_kg': vd_pk, 'kel_factor': kel_factor}
sim = VCMSimulationCKD(weight, ccr, pk_params)

# 2週間分 (336h) 程度の回数を計算
num_doses = int(336 / interval) + 1
times, conc_base = sim.run_sim([dose_load, dose_maint], [interval, interval], num_doses=num_doses)

# ==========================================
# 4. TDM解析エリア
# ==========================================
st.subheader("🩸 TDM解析と投与量調整")

col_t1, col_t2 = st.columns([1.5, 2.5])

with col_t1:
    has_measured = st.checkbox("実測値あり")
    if has_measured:
        # 測定タイミングの入力
        # 3回目の投与直前(トラフ)などを想定しやすいように
        target_dose_num = st.number_input("何回目の投与直前？ (トラフ)", 2, 10, 3)
        # その時間は？
        sampling_time = (target_dose_num - 1) * interval
        
        st.caption(f"想定測定時間: {sampling_time} 時間後")
        
        measured_val = st.number_input("実測値 (µg/mL)", 0.0, 100.0, 0.0, 0.1)
        target_trough = st.slider("目標トラフ", 10.0, 20.0, 15.0)

# 解析ロジック
sim_fitted = None
fitted_kel = 0
mod_conc = None
new_dose = 0
new_interval = interval

if has_measured and measured_val > 0:
    with st.spinner("パラメータ解析中..."):
        # 1. Kelの逆算
        dose_hist = {'load': dose_load, 'maint': dose_maint, 'interval': interval}
        fitted_kel = fit_kel_from_measured(measured_val, sampling_time, weight, dose_hist, vd_pk)
        
        # 2. フィッティングカーブの作成
        sim_fit_obj = VCMSimulationCKD(weight, ccr, pk_params)
        sim_fit_obj.kel_base = fitted_kel # 上書き
        _, sim_fitted = sim_fit_obj.run_sim([dose_load, dose_maint], [interval, interval], num_doses=num_doses)
        
        # 3. 投与設計の提案
        # 新しいKelを使って、定常状態のトラフがTargetになるように計算
        # Css_trough = (D/Vd) * (1 / (e^(ke*tau) - 1)) ... 簡易式
        # 逆に D = Css_trough * Vd * (e^(ke*tau) - 1)
        
        # 間隔は変えず、維持量を変える提案
        vd_total = vd_pk * weight
        tau = interval
        exp_kt = np.exp(fitted_kel * tau)
        
        # トラフをTargetにするための維持量
        # 正確には点滴時間を考慮すべきだが、安全域を見るため簡易式で
        suggest_dose = target_trough * vd_total * (exp_kt - 1)
        new_dose = round(suggest_dose / 100) * 100
        
        with col_t2:
            st.info(f"📊 **解析結果:**\n\n"
                    f"実測値に合わせると、半減期は **{0.693/fitted_kel:.1f} 時間** (予測: {0.693/sim.kel_base:.1f}h) でした。\n\n"
                    f"💡 **推奨維持量:** {interval}時間ごとの場合、**{new_dose} mg** で目標トラフ {target_trough} に近づきます。")
            
            # 修正プランのシミュレーション
            # 測定点以降(次回投与から)切り替える
            # 面倒なので「最初からその量でいってたら」or 「全期間修正プラン」で描画
            sim_mod_obj = VCMSimulationCKD(weight, ccr, pk_params)
            sim_mod_obj.kel_base = fitted_kel
            # 初回はLoadそのまま、維持量をNewに
            _, mod_conc = sim_mod_obj.run_sim([dose_load, new_dose], [interval, interval], num_doses=num_doses)

# ==========================================
# 5. グラフ描画
# ==========================================
st.markdown("---")
st.subheader("📈 血中濃度推移シミュレーション")

fig = go.Figure()

# 1. 初期予測 (Blue)
fig.add_trace(go.Scatter(
    x=times/24, y=conc_base,
    mode='lines', name='初期計画 (Initial)',
    line=dict(color='royalblue', width=2, dash='dot')
))

# 2. 実測フィッティング (Orange)
if sim_fitted is not None:
    fig.add_trace(go.Scatter(
        x=times/24, y=sim_fitted,
        mode='lines', name='実測からの推定 (Fitted)',
        line=dict(color='orange', width=2)
    ))
    # プロット
    fig.add_trace(go.Scatter(
        x=[sampling_time/24], y=[measured_val],
        mode='markers', name='実測値',
        marker=dict(color='red', size=12, symbol='x')
    ))

# 3. 修正プラン (Green)
if mod_conc is not None:
    fig.add_trace(go.Scatter(
        x=times/24, y=mod_conc,
        mode='lines', name=f'修正プラン ({new_dose}mg)',
        line=dict(color='green', width=3)
    ))

# 目標範囲帯
fig.add_hrect(y0=10, y1=20, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Target (10-20)")

# レイアウト調整
fig.update_layout(
    title="Concentration vs Time (Days)",
    xaxis_title="Days", yaxis_title="Concentration (µg/mL)",
    height=450,
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# 投与回ごとのピーク・トラフ目安を表示
if mod_conc is not None:
    target_data = mod_conc
    label = "修正プラン"
else:
    target_data = conc_base
    label = "初期計画"

with st.expander(f"📋 {label} の推定トラフ濃度一覧"):
    cols = st.columns(4)
    for i in range(1, min(9, num_doses)): # 8回目まで表示
        t_idx = int((i * interval) - 0.1) # 投与直前
        val = target_data[t_idx] if t_idx < len(target_data) else 0
        cols[(i-1)%4].metric(f"{i}回目 直前", f"{val:.1f}")
