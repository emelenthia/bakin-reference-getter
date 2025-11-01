# Bakin C# リファレンス HTML構造分析

このドキュメントは、RPG Developer BakinのC#リファレンスドキュメントの実際のHTML構造を記録したものです。
パーサー実装時（フェーズ3）にこの情報を参照してください。

**作成日**: 2025-01-08
**対象URL**: https://rpgbakin.com/csreference/doc/ja/

---

## ⚠️ 重要な注意事項

**HTML構造はページタイプによって異なる可能性があります。**

- クラス、インターフェース、構造体、列挙型などで構造が異なる場合がある
- 名前空間の有無、継承の有無などでセクションの構成が変わる可能性がある
- パーサー実装時は**柔軟な抽出ロジック**を実装する必要がある
- 一つのパターンで全てをカバーできない可能性を考慮する

### 推奨されるパーサー実装方針

1. **複数のセレクタを試す**: 最初のセレクタで取得できない場合、代替セレクタを試す
2. **存在チェック**: 要素が存在しない場合のフォールバック処理
3. **テストケース**: 異なるタイプのページ（クラス、インターフェース、構造体）で動作確認
4. **ログ出力**: パース失敗時に詳細なログを出力して構造を把握

---

## 1. annotated.html（クラス一覧ページ）の構造

**調査URL**: https://rpgbakin.com/csreference/doc/ja/annotated.html

### 全体構造

```
<body>
  <ul>  ← クラスリストのメインコンテナ
    <li>
      C[ClassName](link.html)  ← クラスリンク
      説明文（オプション）
    </li>
  </ul>
</body>
```

### クラスリンクの詳細

**形式**: `C[クラス名](リンクURL)`

**具体例**:
```
C[Sound](class_sharp_kmy_audio_1_1_sound.html)
C[Asset](class_sharp_kmy_base_1_1_asset.html)
C[DebugUI](class_sharp_kmy_base_1_1_debug_u_i.html)
```

### href パターン

- **クラス**: `class_[名前空間]_1_1_[クラス名].html`
  - 例: `class_yukar_1_1_common_1_1_rom_1_1_cast.html`
- **インターフェース**: `interface_[名前空間]_1_1_[名前].html`
  - 例: `interface_yukar_1_1_common_1_1_rom_1_1_i_available_info.html`
- **構造体**: `struct_[名前空間]_1_1_[名前].html`

名前空間の区切りは `_1_1_` で表現される（`::`の代わり）

### クラス名の表示形式

- **表示**: 短縮名のみ（例: `Cast`）
- **完全修飾名**: 名前空間情報は別途抽出が必要（URLから逆算）

### 説明文の位置

クラスリンクの直後にテキストとして配置される場合がある：

```
C[BgmPlaySettings](...)
BGMに関するセーブ情報を格納するクラス
```

### パーサー実装のポイント

```python
# 推奨セレクタ
soup.find_all('a', href=re.compile(r'^(class|interface|struct)_'))

# URLから名前空間とクラス名を抽出
# 例: class_yukar_1_1_common_1_1_rom_1_1_cast.html
#  -> Yukar.Common.Rom.Cast
```

---

## 2. 個別クラスページの構造

**調査URL**: https://rpgbakin.com/csreference/doc/ja/class_yukar_1_1_common_1_1_rom_1_1_cast.html
**対象クラス**: `Yukar.Common.Rom.Cast`

### ページ全体の構造

```
<body>
  <!-- パンくずナビ -->
  <ul>
    <li><a href="namespace_yukar.html">Yukar</a></li>
    <li><a href="...">Common</a></li>
    <li><a href="...">Rom</a></li>
  </ul>

  <!-- クラス説明 -->
  <p>データベース・キャスト 登場するキャラクタ等を定義するクラス</p>

  <!-- 継承図（画像） -->
  <p>Yukar.Common.Rom.Cast の継承関係図</p>
  <img src="class_yukar_1_1_common_1_1_rom_1_1_cast.png" />

  <!-- セクション群 -->
  <h3>公開メンバ関数</h3>
  <dl>...</dl>

  <h3>プロパティ</h3>
  <dl>...</dl>

  <!-- 継承メンバー -->
  <h3>![-](closed.png) 基底クラス Yukar.Common.Rom.RomItem に属する継承公開メンバ関数</h3>
  <dl>...</dl>
</body>
```

### 2.1 クラス説明文

**位置**: パンくずナビの直後の最初の `<p>` タグ

**例**:
```html
<p>データベース・キャスト 登場するキャラクタ等を定義するクラス [詳解]</p>
```

**パーサー実装**:
```python
# パンくずの後の最初のpタグ
description = soup.find('p')
if description:
    text = description.get_text(strip=True)
```

### 2.2 継承関係

**表示方法**:
1. 画像として継承図が表示される
2. テキストで基底クラス名が記載される場合がある

**例**:
```html
<p>Yukar.Common.Rom.Cast の継承関係図</p>
<img src="class_yukar_1_1_common_1_1_rom_1_1_cast.png" />

<!-- または -->
<p>基底クラス <a href="...">Yukar.Common.Rom.RomItem</a> に属する...</p>
```

**パーサー実装**:
```python
# 継承クラスはリンクから抽出
inherit_links = soup.find_all('a', href=re.compile(r'class_.*\.html'))
# テキストに「基底クラス」や「継承」が含まれるものを探す
```

### 2.3 メソッド一覧

**セクション見出し**: `<h3>公開メンバ関数</h3>`

**構造**: `<dl>` + `<dt>` + `<dd>`

**例**:
```html
<h3>公開メンバ関数</h3>
<dl>
  <dt>void Initialize()</dt>
  <dd>初期化メソッド [詳解]</dd>

  <dt>string GetName()</dt>
  <dd>名前を取得 [詳解]</dd>
</dl>
```

**メソッドの構成要素**:
- `<dt>`: 戻り値の型 + メソッド名 + パラメータ
- `<dd>`: 説明文 + [詳解]リンク

**パーサー実装**:
```python
method_section = soup.find('h3', string=re.compile(r'メンバ関数'))
if method_section:
    dl = method_section.find_next_sibling('dl')
    if dl:
        for dt, dd in zip(dl.find_all('dt'), dl.find_all('dd')):
            signature = dt.get_text(strip=True)
            description = dd.get_text(strip=True)
```

### 2.4 プロパティ一覧

**セクション見出し**: `<h3>プロパティ</h3>`

**構造**: `<dl>` + `<dt>` + `<dd>`

**例**:
```html
<h3>プロパティ</h3>
<dl>
  <dt>string Name [get, set]</dt>
  <dd>キャラクタ名 [詳解]</dd>

  <dt>int Level [get, set]</dt>
  <dd>レベル [詳解]</dd>
</dl>
```

**プロパティの構成要素**:
- `<dt>`: 型 + プロパティ名 + `[get, set]` / `[get]` / `[set]`
- `<dd>`: 説明文

**パーサー実装**:
```python
prop_section = soup.find('h3', string=re.compile(r'プロパティ'))
if prop_section:
    dl = prop_section.find_next_sibling('dl')
    # dtからget/setアクセサを抽出
    # 例: "string Name [get, set]" -> type="string", name="Name", accessors="[get, set]"
```

### 2.5 公開変数（フィールド）

**セクション見出し**: `<h3>公開変数類</h3>` または `<h3>静的公開変数類</h3>`

**構造**: `<dl>` + `<dt>` + `<dd>`

**例**:
```html
<h3>公開変数類</h3>
<dl>
  <dt>const int MAX_LEVEL = 99</dt>
  <dd>最大レベル [詳解]</dd>

  <dt>float speed = 1.0f</dt>
  <dd>移動速度 [詳解]</dd>
</dl>
```

**パーサー実装**:
```python
field_section = soup.find('h3', string=re.compile(r'公開変数'))
```

### 2.6 継承されたメンバー

**セクション見出しの特徴**:
- `<h3>` タグに折りたたみアイコンが含まれる: `![-](closed.png)`
- テキストに「継承」や「基底クラス」が含まれる

**例**:
```html
<h3>
  <img src="closed.png" alt="-" />
  基底クラス <a href="...">Yukar.Common.Rom.RomItem</a> に属する継承公開メンバ関数
</h3>
<dl>
  <dt>void BaseMethod()</dt>
  <dd>基底クラスのメソッド</dd>
</dl>
```

**パーサー実装**:
```python
# 継承メンバーのセクションを見つける
inherited_sections = soup.find_all('h3', string=re.compile(r'継承'))

for section in inherited_sections:
    # 基底クラス名を抽出
    base_class_link = section.find('a')
    if base_class_link:
        base_class = base_class_link.get_text(strip=True)

    # 継承メンバーのリストを取得
    dl = section.find_next_sibling('dl')
```

### 2.7 セクション見出しの一覧

実際に使用される `<h3>` 見出しのパターン：

- `クラス` - ネストされたクラス定義
- `公開型` - 公開された型定義
- `公開メンバ関数` - インスタンスメソッド
- `静的公開メンバ関数` - 静的メソッド
- `公開変数類` - インスタンスフィールド
- `静的公開変数類` - 静的フィールド
- `プロパティ` - プロパティ（C#）
- `詳解` - 詳細説明セクション
- `[基底クラス名] に属する継承[種類]` - 継承メンバー

---

## 3. パーサー実装時の推奨アプローチ

### 3.1 柔軟なセレクタ戦略

```python
def find_section(soup, keywords):
    """複数のパターンで要素を検索"""
    for keyword in keywords:
        section = soup.find('h3', string=re.compile(keyword))
        if section:
            return section
    return None

# 使用例
method_section = find_section(soup, [r'メンバ関数', r'Member Functions', r'Methods'])
```

### 3.2 存在チェックとフォールバック

```python
def extract_methods(soup):
    methods = []

    # パターン1: h3 + dl
    section = soup.find('h3', string=re.compile(r'メンバ関数'))
    if section:
        dl = section.find_next_sibling('dl')
        if dl:
            methods = parse_dl_methods(dl)

    # パターン2: 代替構造（もしあれば）
    if not methods:
        # 別のパターンを試す
        pass

    return methods
```

### 3.3 ログ出力

```python
import logging

logger.debug(f"Found {len(methods)} methods in section")
if not methods:
    logger.warning(f"No methods found for {class_name}. HTML structure may differ.")
```

### 3.4 テストケース

実装後、以下のページで動作確認を推奨：

1. **クラス**: `Yukar.Common.Rom.Cast`（継承あり、フルメンバー）
2. **インターフェース**: `Yukar.Common.Rom.IAvailableInfo`（メソッドのみ）
3. **構造体**: 構造体のページ（もしあれば）
4. **列挙型**: 列挙型のページ（もしあれば）
5. **シンプルなクラス**: 継承なし、メンバー少ない

---

## 4. 実装計画との主な相違点

| 項目 | 実装計画の想定 | 実際の構造 |
|------|----------------|------------|
| クラスリスト構造 | `<div class="directory">` + `<table>` | `<ul>` + `<li>` |
| メンバーリスト | `<table class="memberdecls">` | `<dl>` + `<dt>` + `<dd>` |
| セクション見出し | `<h2>` | `<h3>` |
| クラス名表示 | 完全修飾名 | 短縮名（URLから完全名を復元） |
| 継承メンバー表示 | `<td class="inherit">` | `<h3>`の見出しに「継承」キーワード |
| 説明文の位置 | `<div class="textblock">` | パンくず後の `<p>` |

これらの違いに対応するため、**フェーズ3（パーサー実装）で実際のHTML構造に合わせた調整**を行います。

---

## 5. 今後の調査が必要な項目

実装を進める中で、以下の項目について追加調査が必要になる可能性があります：

- [ ] 列挙型（enum）のページ構造
- [ ] 構造体（struct）のページ構造
- [ ] デリゲート（delegate）のページ構造
- [ ] 名前空間ページの詳細構造
- [ ] メソッドの詳細ページ（パラメータ、戻り値の詳細）
- [ ] 静的メンバーと通常メンバーの区別方法
- [ ] ジェネリック型の表示方法

これらは実装時に必要に応じて調査します。

---

**更新履歴**:
- 2025-01-08: 初版作成（annotated.htmlとCastクラスページを調査）
