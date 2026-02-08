import streamlit as st

# ------------------------------------------------------------------
# 1. コンテンツデータ（ここを編集して内容を増やします）
# ------------------------------------------------------------------
# 構造: カテゴリ -> [ { "title": 見出し, "points": [箇条書きリスト], "check": [チェック項目] }, ... ]

ICLS_CONTENT = {
    "❤️ BLS": [
        {
            "title": "CPR",
            "points": [
                "深さ、テンポ、リコイル、中断時間、交代の技術",
          
            ]
        },
        {
            "title": "バックバルブマスク (BVM)",
            "points": [
                "EC,VE法、30:2では10秒以内、非同期は6秒に1回",
            
            ]
        }
    ],
    "⚡ モニター": [
        {
            "title": "安全確認・除細動",
            "points": [
                "電極: ",
                "確認: ",
                "薬剤とのタイミング",
                "パドルの要点欠点"
            ]
        },
        {
            "title": "VF / 無脈性VT",
            "points": [
                "ショック　",
                "同期、非同期について",
                "薬剤: アドレナリン（3-5分毎）、アミオダロン（300mg→150mg）"
            ]
        },
        {
            "title": "PEA / 心静止",
            "points": [
                "　フラットラインプロトコール　",
                "原因検索（5H5T）をチームに促す",
                ""
            ]
        }
    ],
    "🫁 気道": [
        {
            "title": "高度な気道確保",
            "points": [
                "気管内挿管の適応とデメリット",
                "器具: 声門上器具(SGA) または 気管挿管",
                "過換気のリスクと2025改訂の見込み"
            ]
        },
        {
            "title": "挿管後の確認",
            "points": [
                "①食道挿管の除外（心窩部聴診）",
                "②左右肺の換気確認",
                "③EtCO2モニター装着（波形確認）",
                "④チューブ固定・深さ確認"
            ]
        }
    ],
    "🏥 ROSC後": [
        {
            "title": "ABCDEアプローチ",
            "points": [
                "A: 気道確保維持",
                "B: SpO2 92-98%, PaCO2 35-45mmHg",
                "C: 12誘導心電図（STEMI?）, 血圧管理（SBP>90）",
                "D: 意識レベル（JCS/GCS）",
                "E: 体温管理（TTMの適応検討）33-36℃"
                "血糖管理"
            ]
        }
    ],
    "🤝 チーム": [
        {
            "title": "リーダーシップ",
            "points": [
                "指示系統、意思疎通の重要性",
                "負荷分散（記録係、タイムキーパーの指名）",
                "Pre-emptive order（次の指示を予告する）"
                "ハイジャックのリスクとリーダー交代"
            ]
        },
        {
            "title": "コミュニケーション",
            "points": [
                "Closed Loop Communication（指示→復唱→報告）",
                "Speak up（懸念事項の共有）",
                "Shared Mental Model（今どういう状況か共有）"
            ]
        }
    ]
}

# ------------------------------------------------------------------
# 2. アプリケーション設定・CSSハック
# ------------------------------------------------------------------
def main():
    st.set_page_config(page_title="ICLS Guide", page_icon="🚑", layout="centered")

    # CSSで余白を極限まで削る
    st.markdown("""
        <style>
            /* 全体のパディングを削減 */
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 0rem !important;
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
            /* ヘッダー・フッターの非表示化 */
            header {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* タブの余白調整 */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 3rem;
                white-space: pre-wrap;
                background-color: #f0f2f6;
                border-radius: 4px 4px 0px 0px;
                padding: 0.5rem;
                font-size: 0.8rem;
            }
            
            /* Expander（開閉リスト）のスタイル調整 */
            .streamlit-expanderHeader {
                font-weight: bold;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                padding: 0.5rem !important;
                margin-top: 0px !important;
            }
            .streamlit-expanderContent {
                border: 1px solid #e0e0e0;
                border-top: none;
                padding: 0.5rem !important;
            }
            
            /* テキストサイズ調整 */
            p, li {
                font-size: 0.9rem !important;
                margin-bottom: 0.2rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("ICLS Instructor Mate")

    # タブの作成（辞書のキーから自動生成）
    tabs = st.tabs(list(ICLS_CONTENT.keys()))

    # 各タブの中身を描画
    for i, category in enumerate(ICLS_CONTENT.keys()):
        with tabs[i]:
            for item in ICLS_CONTENT[category]:
                # 初期状態で開いておくか？（expanded=Falseで閉じる）
                with st.expander(f"📌 {item['title']}", expanded=False):
                    for point in item['points']:
                        st.markdown(f"- {point}")

if __name__ == "__main__":
    main()
