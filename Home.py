import streamlit as st

# --- 1. ページ設定 ---
st.set_page_config(
    page_title="信州上田医療センター\n腎臓内科 Tools",
    page_icon="🏥",
)
# Googleの自動翻訳機能を無効化する
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# --- 2. スタイル設定 (ボタン拡大・装飾) ---
st.markdown("""
    <style>
    /* サイドバーの「＞」ボタンを大きくする（スマホ用） */
    [data-testid="stSidebarCollapsedControl"] {
        transform: scale(2.5) !important;
        color: #0068C9 !important;
        background-color: #F0F2F6 !important;
        border-radius: 10px !important;
        padding: 5px !important;
        border: 2px solid #0068C9 !important;
        margin-top: 10px !important;
        margin-left: 10px !important;
        z-index: 999999 !important;
    }
    /* ボタンのタップ領域拡大 */
    [data-testid="stSidebarCollapsedControl"]::after {
        content: "";
        position: absolute;
        top: -20px; left: -20px; right: -20px; bottom: -20px;
    }
    
    /* ページリンクボタンを「カード風」に見せるカスタマイズ */
    div[data-testid="stPageLink-NavLink"] {
        background-color: #f0f2f6;
        border: 1px solid #d6d6d8;
        padding: 1rem;
        border-radius: 10px;
        transition: transform 0.1s;
        margin-bottom: 10px;
    }
    div[data-testid="stPageLink-NavLink"]:active {
        transform: scale(0.98);
        background-color: #e0e2e6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. メインコンテンツ ---
st.title("🏥 信州上田医療センター 腎臓内科")
st.markdown("##### Clinical Calculation Tools Portal")

st.info("👇 使用するツールを選択してください")

# ==========================================
# 🩸 血液浄化療法
# ==========================================
st.markdown("### 🩸 血液浄化療法")

st.page_link("pages/01_DFPP_Simulator.py", 
    label="**DFPP Simulator**\n\n血漿交換療法(二重濾過)の条件設定・予測", 
    icon="🩸", 
    use_container_width=True
)

st.page_link("pages/02_sepe_simulator.py", 
    label="**SePE Simulator**\n\n選択的血漿交換療法の条件設定・予測", 
    icon="🧬", 
    use_container_width=True
)

st.page_link("pages/05_Overdose_Sim.py", 
    label="**Overdose Simulation**\n\n薬物過量投与時の透析除去シミュレーション", 
    icon="🚑", 
    use_container_width=True
)

# ==========================================
# 💊 薬剤投与設計 (TDM/CKD)
# ==========================================
st.markdown("---")
st.markdown("### 💊 薬剤投与設計")

st.page_link("pages/08_VCM_CKD.py", 
    label="**VCM CKD Simulator**\n\n保存期CKD（透析なし）のVCM投与設計", 
    icon="🐢", 
    use_container_width=True
)

st.page_link("pages/06_VCM_Sim.py", 
    label="**VCM TDM Simulator**\n\n透析中のバンコマイシン週間投与設計・トラフ予測", 
    icon="💊", 
    use_container_width=True
)

st.page_link("pages/07_CKD_Drug_Adj.py", 
    label="**CKD Drug Dosing**\n\n腎機能（eGFR/CCr）に応じた薬剤投与設計支援", 
    icon="📉", 
    use_container_width=True
)

# ==========================================
# 🧪 電解質・その他
# ==========================================
st.markdown("---")
st.markdown("### 🧪 電解質・その他")

st.page_link("pages/03_LDL_Manage.py", 
    label="**LDL Management**\n\n脂質管理目標・冠動脈疾患リスク評価", 
    icon="🛡️", 
    use_container_width=True
)

st.page_link("pages/04_sodium_calc.py", 
    label="**Na Correction**\n\n低ナトリウム血症の補正シミュレーション", 
    icon="🧂", 
    use_container_width=True
)

st.markdown("""
<br>
<small style="color:gray">
※ 各ツールの詳細は、ボタンをタップして専用ページへ移動してください。<br>
※ 患者情報の入力は各ページ内のサイドバー（左上ボタン）で行います。
</small>
""", unsafe_allow_html=True)
