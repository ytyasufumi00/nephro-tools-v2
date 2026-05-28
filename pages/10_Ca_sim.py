import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("CKD-MBD：カルシウム・マルチアングル評価システム(信州上田医療センター腎臓内科作成)")
st.markdown("### 〜 アルブミン補正公式からイオン化Ca推定へのパラダイムシフト 〜")

# =================================================================
# 1. 中央画面：検査データ入力欄
# =================================================================
st.subheader("📋 検査データ入力")
input_col1, input_col2 = st.columns(2)

with input_col1:
    st.markdown("**【基本項目】**")
    t_ca = st.number_input("総カルシウム (mg/dL)", value=8.8, min_value=4.0, max_value=16.0, step=0.1)
    alb = st.number_input("アルブミン (g/dL)", value=3.2, min_value=1.0, max_value=6.0, step=0.1)
    phos = st.number_input("無機リン (mg/dL)", value=5.5, min_value=1.0, max_value=15.0, step=0.1)

with input_col2:
    st.markdown("**【アニオン構成項目（精緻モデル用）】**")
    na = st.number_input("ナトリウム (mEq/L)", value=138.0, min_value=100.0, max_value=160.0, step=1.0)
    cl = st.number_input("クロール (mEq/L)", value=102.0, min_value=70.0, max_value=130.0, step=1.0)
    tco2 = st.number_input("総二酸化炭素 または HCO3⁻ (mEq/L)", value=22.0, min_value=5.0, max_value=40.0, step=1.0)

st.markdown("---")

# =================================================================
# 2. 計算ロジック
# =================================================================
# ① 従来のPayneの補正Ca式
corrected_ca = t_ca + (4.0 - alb) if alb < 4.0 else t_ca

# ② 簡易モデル（Pの影響を考慮した調整式）
simplified_ica = (0.125 * t_ca) - (0.02 * alb) - (0.01 * phos) + 0.21

# ③ 精緻モデル（Yap & Goldwasser論文モデル：Na, Cl, tCO2のアニオン動態をフル考慮）
t_ca_mmol = t_ca * 0.25
alb_gl = alb * 10
detailed_ica = 0.219 + (0.365 * t_ca_mmol) - (0.0034 * alb_gl) - (0.0042 * na) + (0.0073 * cl) + (0.0047 * tco2)


# =================================================================
# 3. 各バーの可視化関数（文字切れ完全対策版）
# =================================================================
def draw_bar(val, plot_range, target_range, title, unit, color, show_dual_axis=False):
    fig = go.Figure()
    
    # 現在地のラベルテキスト（デュアル表示の場合は2行にする）
    if show_dual_axis:
        val_mgdl = val * 4.0
        display_text = f"★ {val:.2f} mmol/L<br>({val_mgdl:.2f} mg/dL)"
    else:
        display_text = f"★ {val:.2f} {unit}"

    # 1. メインの現在地プロット
    fig.add_trace(go.Scatter(
        x=[val], y=[0.5], 
        mode='markers+text', text=[display_text], textposition="top center",
        marker=dict(color=color, size=14), textfont=dict(size=14),
        cliponaxis=False  
    ))
    
    # 目標域（緑の網掛け）
    fig.add_vrect(x0=target_range[0], x1=target_range[1], fillcolor="rgba(0, 255, 0, 0.1)", line_width=0)
    
    # X軸・Y軸の基本設定
    fig.update_xaxes(title_text=unit, range=plot_range)
    # 空間の天井を2.5に設定
    fig.update_yaxes(visible=False, range=[0, 2.5]) 
    
    # 2. レイアウトのベース設定
    layout_args = dict(
        height=200 if show_dual_axis else 140, 
        margin=dict(l=20, r=20, t=80 if show_dual_axis else 40, b=20), 
        title=dict(text=title, font=dict(size=15)),
        showlegend=False
    )
    
    # 3. 第2軸（上部）の設定とダミートレース
    if show_dual_axis:
        layout_args["xaxis2"] = dict(
            title=dict(text="換算値 (mg/dL)", font=dict(color="gray", size=13)),
            range=[plot_range[0] * 4.0, plot_range[1] * 4.0],
            overlaying="x",
            side="top",
            tickfont=dict(color="gray"),
            showline=True,  
            visible=True    
        )
        
        # ダミートレース
        fig.add_trace(go.Scatter(
            x=[val * 4.0], y=[0.5], 
            xaxis="x2", 
            mode="markers", 
            marker=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip",
            cliponaxis=False 
        ))
        
    fig.update_layout(**layout_args)
    st.plotly_chart(fig, use_container_width=True)

# =================================================================
# 4. メイン画面：4本のバーと数式の交互表示
# =================================================================
st.subheader("📊 各指標の目標値から見た「現在地」と計算ロジック")

# パート1：総Ca
# 【修正】緑の網掛け目標域を 8.4〜9.5 に変更
draw_bar(t_ca, [6.0, 12.0], [8.4, 9.5], "1.【ベース】 総カルシウム (tCa)", "mg/dL", "blue")
st.markdown("` 💡 計算式: 測定値そのまま（日本JSDT参考基準: 8.4〜9.5 mg/dL） `")
st.write("")

# パート2：補正Ca
# 【修正】緑の網掛け目標域を 8.4〜9.5 に変更
draw_bar(corrected_ca, [6.0, 12.0], [8.4, 9.5], "2.【従来意識】 Payne補正カルシウム (Corrected Ca)", "mg/dL", "orange")
st.markdown("` 💡 計算式: 総Ca + (4.0 - Alb)   ※Alb < 4.0 の時に適用（JSDT目標管理域: 8.4〜9.5 mg/dL） `")
st.write("")

# パート3：簡易iCa 
draw_bar(simplified_ica, [0.8, 1.6], [1.15, 1.29], "3.【変革期モデル】 推定イオン化Ca：簡易式 (リン考慮型)", "mmol/L", "green", show_dual_axis=True)
st.markdown("` 💡 計算式: (0.125 × 総Ca) - (0.02 × Alb) - (0.01 × リン) + 0.21  （KDIGO正常域: 1.15〜1.29 mmol/L ≒ 約 4.6〜5.2 mg/dL） `")
st.write("")

# パート4：精緻iCa 
draw_bar(detailed_ica, [0.8, 1.6], [1.15, 1.29], "4.【精密医療モデル】 推定イオン化Ca：精緻式 (Goldwasser重回帰モデル)", "mmol/L", "purple", show_dual_axis=True)
st.markdown("` 💡 計算式: 0.219 + 0.365 × 総Ca(mmol/L) - 0.0034 × Alb(g/L) - 0.0042 × Na + 0.0073 × Cl + 0.0047 × tCO2 （正常域: 1.15〜1.29 mmol/L ≒ 約 4.6〜5.2 mg/dL）`")
st.write("")

st.markdown("---")

# =================================================================
# 5. 横並びの臨床解釈（タブ機能でコラムも集約）
# =================================================================
tab_eval, tab_column = st.tabs(["💡 今回のギャップ評価と臨床解釈", "📚 変革の背景・エビデンス（補足コラム）"])

with tab_eval:
    st.markdown(f"""
    * **従来のPayne式での判断**: 補正Caは **{corrected_ca:.1f} mg/dL** です。
    * **精緻モデル（アニオン考慮）での判断**: 真の生体活性を持つイオン化Caは **{detailed_ica:.2f} mmol/L (約 {detailed_ica*4.0:.2f} mg/dL)** と推定されます。
    """)
    
    # 乖離の臨床アラート
    if detailed_ica < 1.15 and corrected_ca >= 8.4:
        st.warning("⚠️ **【要注意：Payneの罠（潜在的低Ca）】**\n\n補正Caは正常（あるいは高め）に見えますが、高リン血症やアニオン蓄積の影響で、実際のイオン化Caは**低カルシウム血症**の領域に低下している可能性があります。副甲状腺（CaSR）への刺激が強まり、PTHが上昇しやすい病態です。")
    # 【修正】補正Caが9.5以下の時に変更
    elif detailed_ica > 1.29 and corrected_ca <= 9.5:
        st.error("🚨 **【要注意：潜在的高Ca血症】**\n\n補正Caは上限値以下ですが、生体内では**イオン化高カルシウム血症**の閾値を超えているリスクがあります。血管石灰化を避けるため、カルシウム含有結着薬やビタミンD製剤の調整を考慮すべき現在地です。")
    else:
        st.success("各指標の評価は概ね一致しています。")

with tab_column:
    st.markdown("""
    ### 📌 なぜ今、アルブミン補正（Payneの式）から脱却すべきなのか？
    * **歴史的背景: 50年前の過渡期の遺物**
      Payneの補正公式（1973年発表）は、自動分析機や透析医療の黎明期に作られた簡易的な標準化手法です。半世紀が経過した現代のCKD-MBD管理において、この単純な1次関数に依存し続けるリスクが指摘されています。
    * **科学的根拠: アニオン複合体（Complexation）の無視**
      血中Caはアルブミンだけでなく、**リン（P）や重炭酸（HCO3⁻）、尿毒素などの小さな陰イオン（アニオン）**とも結合します。特に腎不全患者ではこれらが蓄積し、イオン化Caの比率が低下しますが、Payneの式はこの動態を一切計算に入れていません。
    * **ガイドラインの現在地**
      KDIGOガイドラインのCKD-MBDアップデートでは、すでに**「総Caに基づくアルブミン補正公式は、一貫して実際のイオン化カルシウムを正確に予測できない」**と明記され、公式への過度な依存に対する警鐘が鳴らされています。副甲状腺（CaSR）が感知するのは、生体活性の本体である**イオン化カルシウム（$I_{Ca}$）**です。
    
    **【参考文献】**
    * Yap & Goldwasser (2022). *Can ionized calcium estimation equations replace albumin-corrected calcium?* - JLPM
    * *Clin Chem Lab Med (CCLM) 2026;* doi:10.1515/cclm-2026-0545
    """)