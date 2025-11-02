# RPG Developer Bakin ドキュメントスクレイパー

** このアプリはAIによる実装を行っています。ご利用の際は自己責任でお願いします **

RPG Developer BakinのC#リファレンスドキュメントをスクレイピングし、AI参照用のMarkdown形式で保存するツールです。

## インストール

```bash
pip install -r requirements.txt
```

## テスト

```bash
pytest tests/ -v
```

## 使用方法

### 継続モードで少しずつスクレイピング（推奨）
```bash
# 最初の5件を取得（動作確認）
python main.py scrape --limit 5

# さらに10件を取得（続きから）
python main.py scrape --limit 10

# 残り全てを取得
python main.py scrape
```

### 進捗のリセット
```bash
# 進捗をリセット
python main.py reset-progress

# リセット後、最初からスクレイピング
python main.py reset-progress
python main.py scrape --limit 5
```

### 特定のクラスのみ取得
```bash
python main.py scrape-class "SharpKmyAudio.Sound"
```

### 進捗状況の確認
```bash
python main.py status
```

### クラスリストのみ取得
```bash
python main.py list-classes
```

## 出力形式

- `output/classes/`: 各クラスのMarkdownファイル
- `output/json/`: 各クラスのJSONファイル（AI処理用）
- `output/index.md`: 全体の索引

## 設定

`config.yaml`でスクレイピングの挙動をカスタマイズできます。
