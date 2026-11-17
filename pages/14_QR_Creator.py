import streamlit as st
import qrcode
from io import BytesIO

# ページ設定
st.set_page_config(page_title="QRコード作成", layout="centered")

st.title("📱 QRコード作成アプリ")
st.write("入力したWebアドレス（URL）からQRコード画像を生成します。")

# URL入力欄
url = st.text_input("QRコード化したいURLを入力してください:", placeholder="https://example.com")

if st.button("QRコードを作成"):
    if url:
        with st.spinner('作成中...'):
            # QRコードの生成設定
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H, # エラー訂正レベル高め
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            # 画像オブジェクトの作成
            img = qr.make_image(fill_color="black", back_color="white")

            # Streamlitで表示・ダウンロードできるようにバイトストリームに変換
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()

            # 画像の表示
            st.image(byte_im, caption="生成されたQRコード", use_column_width=False)

            # ダウンロードボタン
            st.download_button(
                label="📥 QRコード画像をダウンロード",
                data=byte_im,
                file_name="qrcode.png",
                mime="image/png"
            )
    else:
        st.warning("URLを入力してください。")