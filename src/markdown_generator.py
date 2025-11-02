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

            # 継承プロパティと独自プロパティを分離
            own_props = [p for p in detail.properties if 'inherited_from' not in p]
            inherited_props = [p for p in detail.properties if 'inherited_from' in p]

            if own_props:
                for prop in own_props:
                    lines.append(f"### {prop['name']}")
                    lines.append("")
                    lines.append(f"- **型**: `{prop.get('type', 'unknown')}`")
                    if 'accessors' in prop:
                        lines.append(f"- **アクセサ**: {prop['accessors']}")
                    if 'description' in prop:
                        lines.append(f"- **説明**: {prop['description']}")
                    lines.append("")

            if inherited_props:
                lines.append("### 継承されたプロパティ")
                lines.append("")
                for prop in inherited_props:
                    lines.append(f"- `{prop['name']}` (継承元: `{prop['inherited_from']}`)")
                lines.append("")

        # メソッド
        if detail.methods:
            lines.append("## メソッド")
            lines.append("")

            # 継承メソッドと独自メソッドを分離
            own_methods = [m for m in detail.methods if 'inherited_from' not in m]
            inherited_methods = [m for m in detail.methods if 'inherited_from' in m]

            if own_methods:
                for method in own_methods:
                    lines.append(f"### {method['name']}")
                    lines.append("")
                    if 'return_type' in method:
                        lines.append(f"**戻り値**: `{method['return_type']}`")
                        lines.append("")
                    if 'description' in method:
                        lines.append(method['description'])
                        lines.append("")
                    lines.append("---")
                    lines.append("")

            if inherited_methods:
                lines.append("### 継承されたメソッド")
                lines.append("")
                for method in inherited_methods:
                    lines.append(f"- `{method['name']}` (継承元: `{method['inherited_from']}`)")
                lines.append("")

        # フィールド
        if detail.fields:
            lines.append("## 公開フィールド")
            lines.append("")

            own_fields = [f for f in detail.fields if 'inherited_from' not in f]
            inherited_fields = [f for f in detail.fields if 'inherited_from' in f]

            if own_fields:
                for field in own_fields:
                    lines.append(f"- `{field.get('type', 'unknown')} {field['name']}`")
                lines.append("")

            if inherited_fields:
                lines.append("### 継承されたフィールド")
                lines.append("")
                for field in inherited_fields:
                    lines.append(f"- `{field['name']}` (継承元: `{field['inherited_from']}`)")
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
