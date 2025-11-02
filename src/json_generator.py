"""
JSON生成モジュール

クラス詳細情報をJSON形式に変換し、ファイルに保存する責務を持つ。
"""
import json
import logging
from pathlib import Path
from dataclasses import asdict

try:
    from src.parser import ClassDetail
except ModuleNotFoundError:
    from parser import ClassDetail

logger = logging.getLogger(__name__)


class JsonGenerator:
    """クラス情報をJSON形式で出力するクラス"""

    def generate_class_json(self, detail: ClassDetail) -> dict:
        """
        クラス詳細情報をJSON形式に変換

        Args:
            detail: ClassDetailオブジェクト

        Returns:
            JSON形式の辞書
        """
        # ClassDetailをdictに変換
        data = {
            'class_info': {
                'name': detail.info.name,
                'full_name': detail.info.full_name,
                'url': detail.info.url,
                'type': detail.info.type,
                'namespace': detail.info.namespace,
                'description': detail.info.description,
                'document_url': f"https://rpgbakin.com/csreference/doc/ja/{detail.info.url}"
            },
            'description_full': detail.description_full,
            'inherits_from': detail.inherits_from,
            'methods': self._format_methods(detail.methods),
            'properties': detail.properties,
            'fields': detail.fields
        }

        return data

    def _format_methods(self, methods: list) -> list:
        """
        メソッドリストを整形（静的/インスタンスで分類）

        Args:
            methods: メソッドのリスト

        Returns:
            分類されたメソッドリスト
        """
        formatted = {
            'instance_methods': [],
            'static_methods': []
        }

        for method in methods:
            # anchor_idは内部処理用なのでJSON出力からは除外
            cleaned_method = {k: v for k, v in method.items() if k != 'anchor_id'}

            if method.get('is_static', False):
                formatted['static_methods'].append(cleaned_method)
            else:
                formatted['instance_methods'].append(cleaned_method)

        # フラットなリストではなく、分類された形で返す
        return formatted

    def save_json(self, data: dict, filepath: Path):
        """
        JSON形式でファイルに保存

        Args:
            data: JSON形式の辞書
            filepath: 保存先パス
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved JSON: {filepath}")

    def save_class_json(self, detail: ClassDetail, filepath: Path):
        """
        クラス情報をJSON形式で保存（便利メソッド）

        Args:
            detail: ClassDetailオブジェクト
            filepath: 保存先パス
        """
        data = self.generate_class_json(detail)
        self.save_json(data, filepath)
