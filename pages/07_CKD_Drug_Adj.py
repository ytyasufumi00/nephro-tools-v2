import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. 計算ロジック & データベース
# ==========================================

def calc_renal_function(age, sex, cr, weight):
    # eGFR (日本腎臓学会推算式)
    egfr = 194 * (cr ** -1.094) * (age ** -0.287)
    if sex == '女性':
        egfr *= 0.739
    
    # CCr (Cockcroft-Gault式) - 実体重ベース
    # ((140-Age) * Weight) / (72 * Cr) (* 0.85 if female)
    ccr = ((140 - age) * weight) / (72 * cr)
    if sex == '女性':
        ccr *= 0.85
        
    return egfr, ccr

# 簡易薬剤データベース
DRUG_DB = {
    "【鎮痛】プレガバリン (リリカ)": [
        {"min": 60, "max": 999, "dose": "通常量 (150-300mg/日 分2)", "note": "腎排泄型"},
        {"min": 30, "max": 60,  "dose": "75-150mg/日 分2", "note": "減量開始"},
        {"min": 15, "max": 30,  "dose": "25-75mg/日 分1 or 分2", "note": "著明に蓄積する"},
        {"min": 0,  "max": 15,  "dose": "25mg/日 週3回 (透析後) or 25mg/日", "note": "透析で抜けるため補充考慮"}
    ],
    "【胃薬】ファモチジン (ガスター)": [
        {"min": 60, "max": 999, "dose": "20-40mg/日 分2", "note": "通常量"},
        {"min": 30, "max": 60,  "dose": "20mg/日 分2 or 20mg 分1", "note": "蓄積すると意識障害のリスク"},
        {"min": 0,  "max": 30,  "dose": "10-20mg/日 分1-2 or 隔日", "note": "透析患者は20mg/日以下推奨"}
    ],
    "【抗菌】レボフロキサシン (クラビット)": [
        {"min": 50, "max": 999, "dose": "500mg 分1", "note": "通常量"},
        {"min": 20, "max": 50,  "dose": "初日500mg → 2日目以降250mg 分1", "note": "用量依存性。ピークは保つ"},
        {"min": 0,  "max": 20,  "dose": "初日500mg → 3日目以降250mg 隔日(48h毎)", "note": "透析患者も同様"}
    ],
    "【痛風】フェブキソスタット (フェブリク)": [
        {"min": 30, "max": 999, "dose": "通常量 (10-60mg)", "note": "肝代謝・腎排泄混合"},
        {"min": 0,  "max": 30,  "dose": "慎重投与 (上限40mg程度が無難)", "note": "重度腎障害でも使用可だがデータ少ない"}
    ],
    "【脂質】ロスバスタチン (クレストール)": [
        {"min": 30, "max": 999, "dose": "2.5mg〜", "note": "通常通り"},
        {"min": 0,  "max": 30,  "dose": "2.5mgから開始 (増量時は慎重に)", "note": "AUC上昇の報告あり"}
    ],
    "【降圧】オルメサルタン (オルメテック)": [
        {"min": 0,  "max": 999, "dose": "通常通り (腎排泄・胆汁排泄)", "note": "用量調節不要だが、高K血症に注意"}
    ],
     "【下剤】酸化マグネシウム": [
        {"min": 30, "max": 999, "dose": "通常通り", "note": "定期的なMg測定推奨"},
        {"min": 0,  "max": 30,  "dose": "原則避ける / 少量投与", "note": "高Mg血症のリスク大。他剤推奨"}
    ],
}

def get_recommendation(drug_name, current_val, mode="eGFR"):
    # current_val (eGFR or CCr) に基づいて推奨を検索
    data = DRUG_DB.get(drug_name, [])
    for rule in data:
        if rule["min"] <= current_val < rule["max"]:
            return rule
    return {"dose": "データなし", "note": ""}

# ==========================================
# 2. UI & アプリケーション
# ==========================================

st.set_page_config(page_title="CKD Dosing Support", layout="wide")
st.title("📉 CKD 腎機能別 投与設計サポート")

# --- サイドバー：患者情報 ---
st.sidebar.header("1. 患者基本情報")
age = st.sidebar.number_input("年齢 (歳)", value=70, step=1)
sex = st.sidebar.radio("性別", ["男性", "女性"])
weight = st.sidebar.number_input("体重 (kg)", value=60.0, step=1.0)
cr = st.sidebar.number_input("血清クレアチニン (mg/dL)", value=1.2, step=0.1)

# --- 腎機能計算 ---
egfr, ccr = calc_renal_function(age, sex, cr, weight)

# CKD Stage判定
if egfr >= 90: stage, color = "G1", "green"
elif egfr >= 60: stage, color = "G2", "lightgreen"
elif egfr >= 45: stage, color = "G3a", "yellow"
elif egfr >= 30: stage, color = "G3b", "orange"
elif egfr >= 15: stage, color = "G4", "red"
else: stage, color = "G5", "darkred"

# --- メインエリア：腎機能メーター ---
st.subheader(f"📊 腎機能評価: {stage}")

col_m1, col_m2, col_m3 = st.columns([1, 1, 1.5])

with col_m1:
    st.metric("eGFR (推算糸球体濾過量)", f"{egfr:.1f}", "mL/min/1.73m²", delta_color="inverse")
with col_m2:
    st.metric("CCr (Cockcroft-Gault)", f"{ccr:.1f}", "mL/min", help="実体重を用いて計算。高齢者や低体重者ではeGFRより実態に近い場合があります。")

with col_m3:
    # Plotly Gauge Chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = egfr,
        title = {'text': "eGFR Status"},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, 120], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 15], 'color': '#ff4b4b'},   # G5
                {'range': [15, 30], 'color': '#ffa421'},  # G4
                {'range': [30, 45], 'color': '#ffe156'},  # G3b
                {'range': [45, 60], 'color': '#fcfebb'},  # G3a
                {'range': [60, 90], 'color': '#d2fbd4'},  # G2
                {'range': [90, 120], 'color': '#21c354'}  # G1
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': egfr
            }
        }
    ))
    fig.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

# --- 薬剤選択と推奨 ---
st.markdown("---")
st.header("💊 薬剤別 投与量チェック")

# タブで表示モード切替
tab1, tab2 = st.tabs(["🔍 個別検索・詳細", "📋 一覧リスト"])

with tab1:
    selected_drug = st.selectbox("確認したい薬剤を選択してください", list(DRUG_DB.keys()))
    
    # 推奨データの取得
    rec = get_recommendation(selected_drug, egfr)
    
    # 結果表示カード
    st.info(f"### {selected_drug}")
    
    c_res1, c_res2 = st.columns([2, 1])
    with c_res1:
        st.markdown(f"#### 💡 推奨投与量: **{rec['dose']}**")
        st.caption(f"臨床メモ: {rec['note']}")
    with c_res2:
        st.metric("現在のeGFR", f"{egfr:.1f}")

    # テーブルで全体像を表示（該当行をハイライト）
    st.markdown("##### 腎機能別 投与量基準")
    df_drug = pd.DataFrame(DRUG_DB[selected_drug])
    
    # 表示用に整形
    df_drug['GFR範囲'] = df_drug.apply(lambda x: f"{x['min']} - {x['max']}", axis=1)
    df_drug = df_drug[['GFR範囲', 'dose', 'note']].rename(columns={'dose': '投与量', 'note': '備考'})
    df_drug = df_drug.sort_values(by='GFR範囲', ascending=False)
    
    # 現在のステージをハイライトする関数
    def highlight_current(row):
        try:
            min_val = float(row['GFR範囲'].split(' - ')[0])
            max_val = float(row['GFR範囲'].split(' - ')[1])
            if min_val <= egfr < max_val:
                return ['background-color: #d1e7dd; font-weight: bold'] * len(row)
        except:
            pass
        return [''] * len(row)

    st.dataframe(df_drug.style.apply(highlight_current, axis=1), use_container_width=True)

with tab2:
    st.markdown("##### 現在のeGFRに基づく全薬剤推奨一覧")
    
    all_recs = []
    for d_name in DRUG_DB.keys():
        r = get_recommendation(d_name, egfr)
        all_recs.append({
            "薬剤名": d_name.split(" ")[1] if " " in d_name else d_name, # 【鎮痛】などを省く簡易処理
            "推奨投与量": r['dose'],
            "備考": r['note']
        })
    
    df_all = pd.DataFrame(all_recs)
    st.table(df_all)

# --- 警告・免責 ---
st.caption("※ 本アプリのデータは一般的な添付文書やガイドラインに基づきますが、患者の個体差（筋肉量、浮腫など）によりCCrと乖離する場合があるため、最終判断は臨床症状やTDM結果を優先してください。")
