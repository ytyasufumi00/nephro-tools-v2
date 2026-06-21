# 軽量なPython 3.13の公式イメージを使用
FROM python:3.13-slim

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# matplotlib(回路図)が日本語を描画できるよう、CJKフォントを導入
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 必要なパッケージの一覧をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# アプリケーションのコード（Home.pyなど）をすべてコピー
COPY . .

# Cloud Runが使用するポート（8080）を開放
EXPOSE 8080

# StreamlitをCloud Run用の設定（ポート8080）で起動
CMD ["streamlit", "run", "Home.py", "--server.port=8080", "--server.address=0.0.0.0"]
