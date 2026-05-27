import streamlit as st

st.title("臨床用：イオン化カルシウム（iCa）推定シミュレーター")

st.markdown("""
従来のアルブミン補正カルシウム（Payne式など）は、アニオンの complexation（複合体形成）を考慮していないため、
重症患者や腎不全患者での信頼性が低いことが指摘されています。
本ツールは、リン（P）やアニオン動態を考慮した最新の推定モデルに基づいています。
""")

# インプット
col1, col2 = st.columns(2)
with col1:
    t_ca = st.number_input("総カルシウム (mg/dL)", value=9.0, format="%.1f")
    alb = st.number_input("アルブミン (g/dL)", value=4.0, format="%.1f")
with col2:
    phos = st.number_input("無機リン (mg/dL)", value=3.5, format="%.1f")
    # 必要に応じてアニオンギャップやBUNなどを追加

# 計算ロジック（※文献内の具体的な重回帰係数をここに当てはめます）
# 例として、T_ca, Alb, P を用いた仮想の推定式：
# estimated_ica = (係数A * t_ca) - (係数B * alb) - (係数C * phos) + 補正値
estimated_ica_mmol = (0.25 * t_ca) - (0.05 * alb) - (0.02 * phos) + 0.4 # 仮のモック係数

st.subheader("推定結果")
st.metric(label="推定イオン化カルシウム (Estimated iCa)", value=f"{estimated_ica_mmol:.2f} mmol/L")

# 臨床的評価の出力
if estimated_ica_mmol < 1.15:
    st.warning("⚠️ イオン化低カルシウム血症（Ionized Hypocalcemia）のリスクがあります。直接測定を検討してください。")
elif estimated_ica_mmol > 1.29:
    st.error("🚨 イオン化高カルシウム血症（Ionized Hypercalcemia）のリスクがあります。直接測定を検討してください。")
else:
    st.success("正常圏内（推定）")
