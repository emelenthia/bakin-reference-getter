"""
Markdown生成モジュール
"""
import logging
from typing import List
from pathlib import Path

try:
    from src.parser import ClassInfo, ClassDetail
except ModuleNotFoundError:
    from parser import ClassInfo, ClassDetail

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """クラス情報をMarkdownに変換"""

    def generate_class_markdown(self, detail: ClassDetail) -> str:
        """
        クラス詳細情報からMarkdownを生成

        Args:
            detail: ClassDetailオブジェクト

        Returns:
            Markdownテキスト
        """
        lines = []

        # ヘッダー
        lines.append(f"# {detail.info.full_name}")
        lines.append("")

        # メタ情報
        lines.append("## メタ情報")
        lines.append("")
        lines.append(f"- **型**: {detail.info.type}")
        lines.append(f"- **名前空間**: {detail.info.namespace}")
        lines.append(f"- **完全修飾名**: {detail.info.full_name}")
        if detail.info.url:
            lines.append(f"- **ドキュメントURL**: https://rpgbakin.com/csreference/doc/ja/{detail.info.url}")
        lines.append("")

        # 説明
        if detail.description_full:
            lines.append("## 説明")
            lines.append("")
            lines.append(detail.description_full)
            lines.append("")

        # 継承関係
        if detail.inherits_from:
            lines.append("## 継承関係")
            lines.append("")
            lines.append("このクラスは以下のクラスを継承しています：")
            lines.append("")
            for parent in detail.inherits_from:
                lines.append(f"- `{parent}`")
            lines.append("")

        # プロパティ
        if detail.properties:
            lines.append("## プロパティ")
            lines.append("")

            # 静的/非静的プロパティを分離
            static_props = [p for p in detail.properties if p.get('is_static', False)]
            instance_props = [p for p in detail.properties if not p.get('is_static', False)]

            if instance_props:
                for prop in instance_props:
                    lines.append(f"### {prop['name']}")
                    lines.append("")
                    if 'declaration' in prop:
                        lines.append(f"```csharp")
                        lines.append(f"{prop.get('type', '')} {prop['declaration']}")
                        lines.append(f"```")
                        lines.append("")
                    else:
                        lines.append(f"- **型**: `{prop.get('type', 'unknown')}`")
                        if 'accessors' in prop:
                            lines.append(f"- **アクセサ**: {prop['accessors']}")
                    if 'description' in prop:
                        lines.append(f"- **説明**: {prop['description']}")
                    lines.append("")

            if static_props:
                lines.append("### 静的プロパティ")
                lines.append("")
                for prop in static_props:
                    lines.append(f"#### {prop['name']}")
                    lines.append("")
                    if 'declaration' in prop:
                        lines.append(f"```csharp")
                        prop_type = prop.get('type', '')
                        # 型に既に'static'が含まれているかチェック
                        if prop_type.startswith('static '):
                            lines.append(f"{prop_type} {prop['declaration']}")
                        else:
                            lines.append(f"static {prop_type} {prop['declaration']}")
                        lines.append(f"```")
                        lines.append("")
                    else:
                        lines.append(f"- **型**: `{prop.get('type', 'unknown')}`")
                    lines.append("")

        # メソッド
        if detail.methods:
            lines.append("## メソッド")
            lines.append("")

            # 静的/非静的メソッドを分離
            static_methods = [m for m in detail.methods if m.get('is_static', False)]
            instance_methods = [m for m in detail.methods if not m.get('is_static', False)]

            if instance_methods:
                for method in instance_methods:
                    lines.append(f"### {method.get('name', 'unknown')}")
                    lines.append("")

                    # シグネチャ全体を表示
                    if 'signature' in method:
                        lines.append("```csharp")
                        sig = method['signature']
                        if 'return_type' in method:
                            lines.append(f"{method['return_type']} {sig}")
                        else:
                            lines.append(sig)
                        lines.append("```")
                        lines.append("")
                    elif 'return_type' in method:
                        lines.append(f"**戻り値**: `{method['return_type']}`")
                        lines.append("")

                    if 'description' in method:
                        lines.append(method['description'])
                        lines.append("")

                    lines.append("---")
                    lines.append("")

            if static_methods:
                lines.append("### 静的メソッド")
                lines.append("")
                for method in static_methods:
                    lines.append(f"#### {method.get('name', 'unknown')}")
                    lines.append("")

                    # シグネチャ全体を表示
                    if 'signature' in method:
                        lines.append("```csharp")
                        sig = method['signature']
                        ret_type = method.get('return_type', '')
                        # 戻り値の型に既に'static'が含まれているかチェック
                        if ret_type.startswith('static '):
                            # 既にstaticが含まれている場合はそのまま使用
                            lines.append(f"{ret_type} {sig}")
                        else:
                            # staticを追加
                            lines.append(f"static {ret_type} {sig}")
                        lines.append("```")
                        lines.append("")

                    if 'description' in method:
                        lines.append(method['description'])
                        lines.append("")

                    lines.append("---")
                    lines.append("")

        # フィールド
        if detail.fields:
            lines.append("## 公開フィールド")
            lines.append("")

            for field in detail.fields:
                if 'declaration' in field:
                    # フィールドの完全な宣言を表示
                    lines.append(f"- `{field.get('type', '')} {field['declaration']}`")
                else:
                    lines.append(f"- `{field.get('type', 'unknown')} {field['name']}`")

            lines.append("")

        return "\n".join(lines)

    def generate_index_markdown(self, classes: List[ClassInfo]) -> str:
        """
        全体の索引Markdownを生成

        Args:
            classes: ClassInfoオブジェクトのリスト

        Returns:
            索引Markdownテキスト
        """
        lines = []

        lines.append("# RPG Developer Bakin C# リファレンス索引")
        lines.append("")
        lines.append("このドキュメントは自動生成されたものです。")
        lines.append("")

        # 名前空間ごとにグループ化
        namespaces = {}
        for cls in classes:
            ns = cls.namespace or "グローバル"
            if ns not in namespaces:
                namespaces[ns] = []
            namespaces[ns].append(cls)

        # 名前空間ごとに出力
        for ns in sorted(namespaces.keys()):
            lines.append(f"## {ns}")
            lines.append("")

            # 型ごとにさらに分類
            ns_classes = namespaces[ns]
            classes_by_type = {
                'class': [],
                'interface': [],
                'struct': [],
                'enum': []
            }

            for cls in ns_classes:
                if cls.type in classes_by_type:
                    classes_by_type[cls.type].append(cls)

            # クラス
            if classes_by_type['class']:
                lines.append("### クラス")
                lines.append("")
                for cls in sorted(classes_by_type['class'], key=lambda x: x.name):
                    desc = f" - {cls.description}" if cls.description else ""
                    lines.append(f"- [{cls.full_name}](classes/{cls.full_name}.md){desc}")
                lines.append("")

            # インターフェース
            if classes_by_type['interface']:
                lines.append("### インターフェース")
                lines.append("")
                for cls in sorted(classes_by_type['interface'], key=lambda x: x.name):
                    desc = f" - {cls.description}" if cls.description else ""
                    lines.append(f"- [{cls.full_name}](classes/{cls.full_name}.md){desc}")
                lines.append("")

            # 構造体
            if classes_by_type['struct']:
                lines.append("### 構造体")
                lines.append("")
                for cls in sorted(classes_by_type['struct'], key=lambda x: x.name):
                    desc = f" - {cls.description}" if cls.description else ""
                    lines.append(f"- [{cls.full_name}](classes/{cls.full_name}.md){desc}")
                lines.append("")

        return "\n".join(lines)

    def save_markdown(self, content: str, filepath: Path):
        """
        Markdownファイルを保存

        Args:
            content: Markdownテキスト
            filepath: 保存先パス
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved markdown: {filepath}")
