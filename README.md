# CreateSimple Web Application

## 概要 (Overview)

本アプリケーションは、化学物質リスクアセスメントツール「CreateSimple」（Excel VBA版）の機能をWebアプリケーションとして再現したものです。ユーザーは、指定されたフォーマットのCSVファイルをアップロードすることで、複数の化学物質のリスク（吸入、経皮、物理化学的危険性）を一括で評価し、結果をCSVファイルとしてダウンロードすることができます。

このツールは、日本の厚生労働省が提供するCREATE-SIMPLEの計算ロジックに基づいており、事業者における化学物質の初期リスク評価を支援することを目的としています。

## 主な機能 (Features)

-   **一括評価 (Batch Processing):** CSVファイルを使って、複数の作業シナリオにおける化学物質リスクを一度に評価します。
-   **多角的なリスク評価 (Comprehensive Assessment):**
    -   **吸入ばく露リスク (Inhalation Risk):** 作業環境における化学物質の吸入による健康リスクを評価します。
    -   **経皮ばく露リスク (Dermal Risk):** 皮膚接触による健康リスクを評価します。
    -   **物理化学的危険性リスク (Physical Hazard Risk):** 引火性、爆発性などの物理的な危険性を評価します。
-   **結果のダウンロード (Downloadable Results):** 評価結果をまとめたCSVファイルをダウンロードできます。

## ご利用方法 (How to Use)

1.  **テンプレートのダウンロード:**
    -   トップページにある「テンプレートCSVをダウンロード」ボタンをクリックし、入力用のCSVファイル (`template.csv`) をダウンロードします。

2.  **CSVファイルの編集:**
    -   ダウンロードした`template.csv`を開き、評価したい化学物質と作業条件の情報を入力します。
    -   入力形式の詳細は下記の「入力CSVフォーマット」セクションを参照してください。

3.  **ファイルのアップロード:**
    -   編集したCSVファイルを、トップページのアップロードエリアにドラッグ＆ドロップするか、「ファイルを選択」ボタンから選択します。
    -   ファイルを選択すると、自動的にリスクアセスメントが実行されます。

4.  **結果の確認とダウンロード:**
    -   処理が完了すると、評価結果が画面に表示されます。
    -   「結果をダウンロード」ボタンをクリックすると、詳細な評価結果を含むCSVファイルをダウンロードできます。

## 入力CSVフォーマット (Input CSV Format)

アップロードするCSVファイルは、以下のヘッダーと形式に従っている必要があります。一行が一つの評価シナリオに対応します。

### ヘッダー (Headers)

```
CAS_RN,Product_Property,Concentration,Amount_Q1,Spray_Q2,Area_Q3,Ventilation_Q4,Time_Q5,Frequency_Q6,Frequency_Days,Frequency_Events,Variation_Q7,SkinArea_Q8,Glove_Q9,Education_Q10,Temp_Q11,AntiFire_Q12,AntiExplosion_Q13,AntiMetal_Q14,ContactWaterAir_Q15
```

### 入力例 (Example)

以下は、ホルムアルデヒド (CAS RN: 50-00-0) の評価シナリオ例です。各選択肢は日本語のテキストで入力してください。

```csv
CAS_RN,Product_Property,Concentration,Amount_Q1,Spray_Q2,Area_Q3,Ventilation_Q4,Time_Q5,Frequency_Q6,Frequency_Days,Frequency_Events,Variation_Q7,SkinArea_Q8,Glove_Q9,Education_Q10,Temp_Q11,AntiFire_Q12,AntiExplosion_Q13,AntiMetal_Q14,ContactWaterAir_Q15
50-00-0,液体,10,極微量（10mL未満）,はい,はい,換気レベルD（外付け式局所排気装置）,8時間超,週1回以上,5,,ばく露濃度の変動が大きい作業,片手の手のひら付着,耐透過性・耐浸透性の手袋の着用している,十分な教育や訓練を行っている,室温,はい,はい,はい,はい
```

### 各項目の選択肢 (Column Options)

-   **CAS_RN:** 評価対象物質のCAS登録番号 (必須)
-   **Product_Property:** 製品の性状 (`液体` または `固体`)
-   **Concentration:** 含有率 (%)
-   **Amount_Q1:** `大量 (1kL以上)`, `中量 (1L以上～1000L未満)`, `少量 (100mL以上～1000mL未満)`, `微量 (10mL以上～100mL未満)`, `極微量 (10mL未満)`
-   **Spray_Q2:** `はい`, `いいえ`
-   **Area_Q3:** `はい`, `いいえ`
-   **Ventilation_Q4:** `レベルA（特に換気のない部屋）`, `レベルB（全体換気）`, `レベルC（工業的な全体換気、屋外作業）`, `レベルD（外付け式局所排気装置）`, `レベルE（囲い式局所排気装置）`, `レベルF（密閉容器内での取扱い）`
-   **Time_Q5:** `8時間超`, `7時間超～8時間以下`, `...`, `30分以下`
-   **Frequency_Q6:** `週1回以上`, `週1回未満`
-   **Frequency_Days:** 週あたりの作業日数 (`Frequency_Q6`が「週1回以上」の場合に必須)。例: `3`, `5`
-   **Frequency_Events:** 年間の作業回数 (`Frequency_Q6`が「週1回未満」の場合に必須)。例: `12` (月1回の場合), `50`
-   **Variation_Q7:** `ばく露濃度の変動が大きい作業`, `変動が小さい`
-   **SkinArea_Q8:** `大きなコインサイズ`, `片手の手のひら付着`, `...`, `両手の肘から下全体`
-   **Glove_Q9:** `着用していない / 情報のない手袋`, `耐透過性・耐浸透性の手袋の着用している`
-   **Education_Q10:** `行っていない`, `基本的な教育`, `十分な教育や訓練を行っている`
-   **Temp_Q11:** `室温`, `室온以上`
-   **AntiFire_Q12 ~ ContactWaterAir_Q15:** `はい`, `いいえ`

## ローカルでの開発 (Local Development)

1.  **リポジトリのクローン:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **依存ライブラリのインストール:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **アプリケーションの実行:**
    ```bash
    python3 -m flask run
    ```

4.  **ブラウザでアクセス:**
    -   `http://127.0.0.1:5000` を開きます。
