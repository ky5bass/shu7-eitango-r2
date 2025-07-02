# ![ヘッダー画像](https://raw.githubusercontent.com/ky5bass/shu7-eitango/refs/heads/main/docs/img/header.svg)

ウェブサイト [週7英単語](https://shu7-eitango.com) のプロジェクトです。

# 初回ローカル環境構築時の履歴

```shell
# ベースとなるgitリポジトリをクローン
git clone git@github.com:ky5bass/shu7-eitango.git shu7-eitango-r2
cd shu7-eitango-r2

# プロジェクト名を変更
vi package-lock.json    # ファイル編集(shu7-nihongo→shu7-eitangoに置換)
vi package.json         # 同上
vi wrangler.toml        # 同上

# dependenciesをインストール
npm install             # dependenciesをインストール
npm audit fix           # 脆弱性のあるdependenciesを更新

# 本プロジェクト向けにコンテンツを修正
vi src/index.ts
vi src/__STATIC_CONTENT_MANIFEST.d.ts
vi static/css/bootstrap_custom.css
cp /path/to/new_logo.svg ./static/img/logo.svg
vi templates/base.tpl
vi templates/bunch.tpl
vi templates/index.tpl
vi main.py
vi README.md
vi requirements.txt

npx wrangler login
mkdir public            # 公開ディレクトリを用意(無いとデプロイ失敗)
npx wrangler deploy
```