# CREATE-SIMPLE Web (Flask Version)

## 概要 (Overview)

CREATE-SIMPLE Webは、化学物質の吸入リスクを簡易的に評価するためのWebアプリケーションです。厚生労働省が提供するコントロール・バンディングツール「CREATE-SIMPLE」の主要な計算ロジックを、Webインターフェースで利用できるようにしたものです。

個別のリスク評価と、CSVファイルを使用した一括評価の2つのモードをサポートしています。

## 技術スタック (Tech Stack)

-   **Backend**: Python, Flask
-   **Data Processing**: Pandas
-   **Frontend**: HTML, Tailwind CSS (via CDN)
-   **Testing**: Playwright

## 機能 (Features)

-   **個別リスク評価 (Single Assessment)**: Webフォームに作業条件を入力し、化学物質の吸入リスクをリアルタイムで計算します。
-   **一括リスク評価 (Batch Assessment)**: 事前に定義されたフォーマットのCSVファイルをアップロードすることで、複数の評価を一度に実行できます。
-   **結果のダウンロード (Download Results)**: 一括評価の結果をCSVファイルとしてダウンロードできます。

## セットアップと実行方法 (Setup and Usage)

### 1. 前提条件 (Prerequisites)

-   Python 3.10以降
-   pip

### 2. インストール (Installation)

リポジトリをクローンし、必要な依存関係をインストールします。

```bash
git clone <repository_url>
cd CREATE-SIMPLE-Web
pip install -r requirements.txt
```

### 3. アプリケーションの実行 (Running the Application)

以下のコマンドでFlask開発サーバーを起動します。

```bash
python3 app.py
```

アプリケーションは `http://localhost:5000` でアクセス可能になります。

## CSV一括評価フォーマット (Batch CSV Format)

一括評価に使用するCSVファイルは、以下のカラムをUTF-8形式で含んでいる必要があります。

| カラム名 (Column Name) | データ型 (Type) | 説明 (Description)                                                               | 例 (Example)                 |
| :--------------------- | :-------------- | :------------------------------------------------------------------------------- | :--------------------------- |
| `cas`                  | string          | 評価対象物質のCAS登録番号。`data.py`に存在する物質のみが対象です。                | `108-88-3`                   |
| `concentration`        | number          | 含有率 (重量%)。0から100の数値を入力します。                                     | `80`                         |
| `form`                 | string          | 物理的形状。`liquid`、`powder`、または`gas`のいずれか。                           | `liquid`                     |
| `q1_amount`            | integer         | 取扱量。`1` (大量) 〜 `5` (極微量) の整数値。                                    | `2`                          |
| `q2_spray`             | boolean         | スプレー作業の有無。`true`または`false`。                                        | `true`                       |
| `q4_ventilation`       | float           | 換気状況。`0.01` (密閉) 〜 `10` (無換気) の係数値。                              | `1`                          |
| `q5_time`              | float           | 作業時間。`0.1` (短時間) 〜 `2` (長時間) の係数値。                              | `1`                          |
| `title`                | string          | 評価のタイトルや作業名。結果画面で表示されます。                                 | `トルエンを使用した洗浄作業` |

**注意:** CSVの1行目がヘッダーとして扱われます。指定されたカラム名と完全に一致させてください。
