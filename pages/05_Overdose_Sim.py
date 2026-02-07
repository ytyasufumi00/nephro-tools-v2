import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt

# ==========================================
# 1. 計算ロジッククラス
# ==========================================
class DrugSimulation:
    def __init__(self, drug_params, weight):
        self.weight = weight
        self.V1 = drug_params['V1_per_kg'] * weight
        self.V2 = drug_params['V2_per_kg'] * weight
        
        # 組織間移行速度定数 (L/min -> rate constant)
        self.Q_inter = drug_params['Q_inter_L_min']
        self.k12 = self.Q_inter / self.V1
        self.k21 = self.Q_inter / self.V2
        
        # 消失速度定数 k_el の計算
        total_V = self.V1 + self.V2
        t_half_min = drug_params['T_half_hours'] * 60
        
        if t_half_min > 0:
            self.k_el = (0.693 * total_V) / (t_half_min * self.V1)
        else:
            self.k_el = 0

    def calculate_hd_clearance(self, Qb, Qd, KoA, sc=1.0):
        if Qb == 0: return 0
        ratio = Qb / Qd
        Z = (KoA / Qb) * (1 - ratio)
        
        if abs(1 - ratio) < 0.001:
            clearance = Qb * (KoA / (KoA + Qb))
        else:
            exp_z = np.exp(Z)
            clearance = Qb * (exp_z - 1) / (exp_z - ratio)
        return clearance * sc

def run_scenario(sim, time_steps, A1_init, A2_init, hd_config=None):
    conc_v1 = np.zeros(len(time_steps))
    conc_v2 = np.zeros(len(time_steps))
    
    A1 = A1_init
    A2 = A2_init
    
    # HD設定
    hd_cl_val = hd_config['cl_val'] if hd_config else 0.0
    hd_start = hd_config['start'] if hd_config else -1
    hd_end = hd_config['start'] + hd_config['duration'] if hd_config else -1
    
    for i, t in enumerate(time_steps):
        conc_v1[i] = A1 / sim.V1
        conc_v2[i] = A2 / sim.V2
        
        current_cl = 0.0
        if hd_config and (t >= hd_start) and (t < hd_end):
            current_cl = hd_cl_val
        
        # 差分方程式
        trans_2to1 = sim.k21 * A2
        trans_1to2 = sim.k12 * A1
        trans_net = trans_2to1 - trans_1to2
        
        elim = sim.k_el * A1
        rem_hd = (A1 / sim.V1) * current_cl
        
        A1 = A1 + trans_net - elim - rem_hd
        A2 = A2 - trans_net
        
        if A1 < 0: A1 = 0
        if A2 < 0: A2 = 0
        
    return conc_v1, conc_v2

# ==========================================
# 2. UI & 詳細解説 (Detailed Explanation)
# ==========================================
def draw_detailed_explanation():
    st.markdown("---")
    st.header("📚 パラメータ解説と臨床的意義")
    
    # タブ設定
    tab1, tab2 = st.tabs(["⏱️ 半減期入力ガイド (正常 vs 不全)", "📖 詳細用語解説 (Vd, Q, KoA)"])
    
    with tab1:
        st.markdown("### 腎機能・病態別の消失半減期 ($T_{1/2}$) 目安")
        st.markdown("患者の状態に合わせて、適切な値を入力してください。")
        
        data = [
            {"薬剤": "アシクロビル", "正常": "2.5 時間", "腎不全/中毒": "**20 時間**", "備考": "腎排泄型。腎不全で著明に延長。"},
            {"薬剤": "リチウム", "正常": "18~24 時間", "腎不全/中毒": "**40~50+ 時間**", "備考": "腎排泄型。透析後のリバウンドが大。"},
            {"薬剤": "メタノール", "正常": "2~3 時間", "腎不全/中毒": "**30~50+ 時間**", "備考": "代謝拮抗薬(ホメピゾール等)使用時は著明に延長。"},
            {"薬剤": "カフェイン", "正常": "3~6 時間", "腎不全/中毒": "**10~100 時間**", "備考": "肝代謝。過量服薬による代謝飽和で延長。"},
            {"薬剤": "バルプロ酸", "正常": "10~16 時間", "腎不全/中毒": "**~30 時間**", "備考": "肝代謝。中毒域で蛋白結合が外れ、透析効率UP。"},
            {"薬剤": "カルバマゼピン", "正常": "10~20 時間", "腎不全/中毒": "**20~40 時間**", "備考": "肝代謝。徐放剤による吸収遅延・リバウンドに注意。"},
        ]
        st.table(data)
        st.info("💡 **Point:** アシクロビルやリチウムなど継続投与をしていた場合は、急性腎不全を発症した以降の投薬が蓄積していると考え、急性腎不全を発症したと想定される日時からの総投与量を目安に入力して下さい")

    with tab2:
        # アコーディオン形式で用語解説
        with st.expander("1. 分布容積 V1 (中心室) と V2 (末梢室)", expanded=False):
            st.markdown("""
            **イメージ: 「小さなバケツ(V1)」と「巨大な貯水槽(V2)」**
        
            * **$V_1$ (Central Volume):**
                * 血液および血流が豊富な臓器（心臓、腎臓、肝臓、脳など）を表します。
                * 透析用カテーテルはこの「バケツ」に繋がっているため、**透析で直接薬を除去できるのはこの $V_1$ にある薬だけ**です。
            * **$V_2$ (Peripheral Volume):**
                * 筋肉、脂肪、皮膚、細胞内など、血流が比較的少ない、または薬物が取り込まれやすい組織です。
                * ここにある薬は、一度 $V_1$ に戻ってこないと除去できません。
            * **臨床的意義:**
                * $V_2$ が大きい（脂溶性が高い、組織結合性が強い）薬物は、透析開始直後に血中濃度($C_1$)が急激に下がりますが、体内の総量はあまり減っていないことがあります（見かけの除去）。
            """)

        with st.expander("2. 組織間移行クリアランス Q (Inter-compartmental Clearance)", expanded=True):
            st.markdown("""
            **イメージ: 「V1とV2をつなぐパイプの太さ」**
            
            * **定義:** 単位時間あたりに、血液($V_1$)と組織($V_2$)の間を行き来できる血液量に相当します。
            * **Qが大きい場合 (> 0.5 L/min):**
                * パイプが太い。透析で血中濃度が下がると、組織から速やかに薬が補充されます。
                * 結果、全身から効率よく薬が抜けます（メタノールなど）。
            * **Qが小さい場合 (< 0.2 L/min):**
                * パイプが細い。組織からの移動が追いつかず、透析中は血中濃度だけが急激に下がります（不均衡）。
                * 透析を止めると、組織に残っていた薬がゆっくり戻ってきて、血中濃度が再上昇します（**リバウンド**）。
                * **代表例:** リチウム、ジゴキシンなど。
            """)

        with st.expander("3. KoA (総括物質移動係数)", expanded=False):
            st.markdown("""
            **イメージ: 「ふるいの目の粗さと面積」**
        
            * **定義:** その透析器（ダイアライザ）が、特定の物質をどれだけ通しやすいかを表す物理的な能力値です。
            * **数値の意味:**
                * **KoA > 800 (超高効率):** メタノール、リチウム、尿素など。血流さえあれば制限なく抜けるレベル。血流量($Q_B$)を上げれば上げるほど除去量が増えます。
                * **KoA 500-700 (高効率):** カフェイン、アシクロビルなど。十分に除去可能です。
                * **KoA < 300:** 分子量が大きい（バンコマイシン等）か、膜への吸着などが関与する場合。
            * **注意点:** どんなにKoAが高くても、**蛋白結合している薬物は「網」を通れません**。このシミュレーターでは「遊離型（Free fraction）」が除去される前提でKoAを設定しています。
            """)
            
        with st.expander("4. リバウンド発生のメカニズム", expanded=False):
            st.markdown("""
            1. 透析により $V_1$（血液）の濃度だけが急激に下がる。
            2. $V_2$（組織）は高濃度のまま取り残される。
            3. 透析終了後、$V_2 \to V_1$ への移動だけが続き、血中濃度が再上昇する。
            """)

# ==========================================
# 3. メインアプリケーション
# ==========================================

st.set_page_config(page_title="Overdose Sim", layout="wide")

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

st.title("🚑 薬物過量投与 透析除去シミュレーター\n 対象薬剤　患者情報を左上>>から入力")

# --- サイドバー設定 ---
st.sidebar.header("1. 患者・透析条件")
weight = st.sidebar.number_input("患者体重 (kg)", value=60.0, step=1.0)
qb = st.sidebar.slider("血流量 Qb (mL/min)", 100, 400, 200, step=10)
qd = st.sidebar.slider("透析液流量 Qd (mL/min)", 300, 800, 500, step=50)
hd_duration = st.sidebar.slider("透析時間 (時間)", 1, 12, 4) * 60

# 入力単位を「時間」に変更
hd_start_hours = st.sidebar.number_input("服用から透析開始まで (時間)", value=2.0, step=0.5)
hd_start = int(hd_start_hours * 60) # 分換算

st.sidebar.header("2. 薬剤選択・設定")
drug_list = [
    "カフェイン", "アシクロビル", "カルバマゼピン", "バルプロ酸", "メタノール", "リチウム", 
    "エチゾラム (対象外、教育用)", "ジゴキシン (対象外、教育用)", "カスタム (自由設定)"
]
drug_choice = st.sidebar.selectbox("対象薬剤", drug_list)

# --- パラメータと閾値定義 ---
default_params = {
    'カフェイン': {
        'V1': 0.2, 'V2': 0.4, 
        'Q': 0.5, 'T1/2': 15.0, 'KoA': 700, 'dose': 6000,
        'thresholds': {'Toxic (>80)': 80, 'Fatal (>100)': 100},
        'unit': 'µg/mL'
    },
    'アシクロビル': {
        'V1': 0.15, 'V2': 0.55, 'Q': 0.2, 'T1/2': 20.0, 'KoA': 600, 'dose': 5000,
        'thresholds': {'Neurotoxicity (>50)': 50},
        'unit': 'µg/mL'
    },
    'カルバマゼピン': {
        'V1': 0.3, 'V2': 0.8, 'Q': 
        0.25, 'T1/2': 24.0, 'KoA': 450, 'dose': 8000,
        'thresholds': {'Toxic (>20)': 20, 'Severe (>40)': 40},
        'unit': 'µg/mL'
    },
    'バルプロ酸': {
        'V1': 0.15, 'V2': 0.25, 'Q': 0.3, 'T1/2': 20.0, 'KoA': 650, 'dose': 25000,
        'thresholds': {'Toxic (>100)': 100, 'Severe/HD Indication (>850)': 850},
        'unit': 'µg/mL'
    },
    'メタノール': {
        'V1': 0.6, 
        'V2': 0.1, 'Q': 0.8, 'T1/2': 40.0, 'KoA': 900, 'dose': 30000,
        'thresholds': {'Toxic (>200)': 200, 'HD Indication (>500)': 500},
        'unit': 'mg/L' # 数値的整合性のためmg/L (20mg/dL = 200mg/L)
    },
    'リチウム': {
        'V1': 0.3, 'V2': 0.6, 'Q': 0.15, 'T1/2': 40.0, 'KoA': 850, 'dose': 4000,
        'thresholds': {'Toxic (>10.5)': 10.5, 'Severe (>17.5)': 17.5}, # mg/L換算値
        'unit': 'mg/L' 
    },
    'エチゾラム (対象外、教育用)': {
        'V1': 0.4, 'V2': 0.8, # Vd 1.2 L/kg (脂肪組織への分布)
        'Q': 0.3, 'T1/2': 6.0,
        'KoA': 0, # 蛋白結合率93%のため除去されない
        'dose': 10, # 10mg (過量)
        'thresholds': {},
        'unit': 'µg/mL'
    },
    'ジゴキシン (対象外、教育用)': {
        'V1': 0.5, 'V2': 7.5, # Vd 8.0 L/kg (骨格筋への高度集積)
        'Q': 0.1, 'T1/2': 48.0, # 腎不全では著明に延長(通常3-5日)
        'KoA': 15, # 膜通過性はあってもVdが巨大すぎて除去効率は皆無
        'dose': 5, # 5mg (過量)
        'thresholds': {'Toxic (>2ng/mL)': 0.002}, # 2ng/mL = 0.002 µg/mL
        'unit': 'µg/mL'
    },
    'カスタム (自由設定)': {
        'V1': 0.2, 'V2': 0.4, 'Q': 0.3, 'T1/2': 12.0, 'KoA': 500, 'dose': 5000,
        'thresholds': {},
        'unit': 'µg/mL'
    }
}

p = default_params[drug_choice]

with st.sidebar.expander("薬剤パラメータ詳細設定", expanded=True):
    overdose_amount = st.number_input("摂取量 (mg)", value=p['dose'], step=100)
    
    st.caption(f"▼ {drug_choice} 設定値")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v1_pk = st.slider("V1 (L/kg) 中心室", 0.05, 2.0, p['V1'], 0.01)
    with col_v2:
        v2_pk = st.slider("V2 (L/kg) 末梢室", 0.05, 10.0, p['V2'], 0.01)
    
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        t_half = st.number_input("半減期 (時間)", value=float(p['T1/2']), help="下の表を参考に設定")
    with col_k2:
        koa = st.number_input("KoA (mL/min)", value=int(p['KoA']))
        
    q_inter = st.slider("組織間移行クリアランス Q (L/min)", 0.01, 2.0, p['Q'], 0.01, help="小さいほどリバウンド大")

current_params = {
    'V1_per_kg': v1_pk, 'V2_per_kg': v2_pk, 
    'Q_inter_L_min': q_inter, 'T_half_hours': t_half, 
    'KoA': koa
}

# --- 自動実行ロジック ---
sim = DrugSimulation(current_params, weight)

# グラフ表示範囲: 服用から透析開始までの時間 + 24時間
total_time = hd_start + 24 * 60
time_steps = np.arange(0, total_time, 1)

# 自動計算
a1_pre = overdose_amount
a2_pre = 0.0

for _ in range(hd_start):
    trans = (sim.k21 * a2_pre) - (sim.k12 * a1_pre)
    elim = sim.k_el * a1_pre
    a1_pre = a1_pre + trans - elim
    a2_pre = a2_pre - trans
    if a1_pre < 0: a1_pre = 0
    if a2_pre < 0: a2_pre = 0

A1_init = a1_pre
A2_init = a2_pre

cl_hd_val_L = sim.calculate_hd_clearance(qb, qd, koa) / 1000.0

hd_config = {'start': hd_start, 'duration': hd_duration, 'cl_val': cl_hd_val_L}
c1_hd, c2_hd = run_scenario(sim, time_steps, A1_init, A2_init, hd_config)
c1_none, c2_none = run_scenario(sim, time_steps, A1_init, A2_init, None)

# --- グラフ描画 (Altair) ---
st.subheader(f"Simulation Result: {drug_choice} (24h)")

col1, col2 = st.columns([3, 1])

with col1:
    time_hr = time_steps / 60
    df_chart = pd.DataFrame({
        'Time': np.concatenate([time_hr, time_hr, time_hr, time_hr]),
        'Concentration': np.concatenate([c1_none, c2_none, c2_hd, c1_hd]),
        'Label': (
            ['Blood (No HD)'] * len(time_hr) +
            ['Tissue (No HD)'] * len(time_hr) +
            ['Tissue (With HD)'] * len(time_hr) +
            ['Blood (With HD)'] * len(time_hr)
        )
    })
    
    # 色と線のスタイルの定義 (ダークモード対応 & 判別しやすく変更)
    colors = {
        'Blood (With HD)': '#FF4B4B',   # 赤 (Solid) - 最重要
        'Tissue (With HD)': '#56CCF2',  # 水色 (Long Dash)
        'Blood (No HD)': '#F2994A',     # オレンジ (Dot) - 対照
        'Tissue (No HD)': '#6FCF97'     # 緑 (Dot) - 対照
    }
    dashes = {
        'Blood (With HD)': [0],         # Solid
        'Tissue (With HD)': [6, 4],     # Long Dash
        'Blood (No HD)': [2, 2],        # Dot
        'Tissue (No HD)': [2, 2]        # Dot
    }
    
    max_time_hr = total_time / 60
    base = alt.Chart(df_chart).encode(x=alt.X('Time', title='Time (hours)', scale=alt.Scale(domain=[0, max_time_hr])))
    
    lines = base.mark_line().encode(
        y=alt.Y('Concentration', title=f'Concentration ({p["unit"]})'), # 軸ラベルにも単位反映
        color=alt.Color('Label', scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title=None, orient='top-right')),
        strokeDash=alt.StrokeDash('Label', scale=alt.Scale(domain=list(dashes.keys()), range=list(dashes.values())), legend=None)
    )
    
    hd_area_df = pd.DataFrame({'x': [hd_start/60], 'x2': [(hd_start+hd_duration)/60]})
    hd_rect = alt.Chart(hd_area_df).mark_rect(color='red', opacity=0.1).encode(x='x', x2='x2')
    
    threshold_layers = []
    if p['thresholds']:
        th_df = pd.DataFrame([{'label': k, 'val': v} for k, v in p['thresholds'].items()])
        th_df['display_label'] = '⚠ ' + th_df['label']
        rules = alt.Chart(th_df).mark_rule(color='red', opacity=0.3, strokeWidth=1.5).encode(y='val')
        text = alt.Chart(th_df).mark_text(align='left', baseline='bottom', color='red', opacity=0.8, fontWeight='bold', dx=5).encode(x=alt.value(5), y='val', text='display_label')
        threshold_layers = [rules, text]
    
    final_chart = alt.layer(hd_rect, lines, *threshold_layers).properties(height=400)
    st.altair_chart(final_chart, use_container_width=True)
    
with col2:
    idx_end = -1
    st.markdown(f"### at {max_time_hr:.1f} hours")
    # ✅ 変更点：単位を表示
    unit = p['unit']
    st.metric(f"Blood (With HD)", f"{c1_hd[idx_end]:.1f} {unit}")
    st.metric(f"Blood (No HD)", f"{c1_none[idx_end]:.1f} {unit}")
    
    if c1_none[idx_end] > 0:
        reduction = (1 - c1_hd[idx_end] / c1_none[idx_end]) * 100
        st.success(f"Reduction: {reduction:.1f}%")
        
    st.markdown("---")
    # リバウンド
    end_idx = hd_start + hd_duration
    if end_idx < len(time_steps):
        post_1h_idx = min(end_idx + 60, len(time_steps)-1)
        reb_diff = c1_hd[post_1h_idx] - c1_hd[end_idx]
        
        st.write("### Post-HD Rebound")
        if reb_diff > 1.0: 
            st.warning(f"Rebound (+1h): +{reb_diff:.1f} {unit}")
        else:
            st.info("No significant rebound")

# --- 詳細解説 ---
draw_detailed_explanation()
