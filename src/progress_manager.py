"""
進捗管理モジュール - CSV形式で進捗を追跡
"""
import csv
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from src.parser import ClassInfo

logger = logging.getLogger(__name__)


@dataclass
class ProgressEntry:
    """進捗エントリー"""
    full_name: str
    name: str
    url: str
    type: str
    namespace: str
    description: str
    completed: bool
    last_updated: str  # ISO 8601形式


class ProgressManager:
    """進捗管理クラス"""

    CSV_HEADERS = [
        'full_name', 'name', 'url', 'type',
        'namespace', 'description', 'completed', 'last_updated'
    ]

    def __init__(self, progress_file: Path):
        """
        Args:
            progress_file: 進捗CSVファイルのパス
        """
        self.progress_file = progress_file

    def initialize_from_class_list(self, classes: List[ClassInfo]):
        """
        クラスリストから進捗CSVを初期化

        Args:
            classes: ClassInfoのリスト
        """
        logger.info(f"Initializing progress file: {self.progress_file}")

        with open(self.progress_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()

            for cls in classes:
                entry = ProgressEntry(
                    full_name=cls.full_name,
                    name=cls.name,
                    url=cls.url,
                    type=cls.type,
                    namespace=cls.namespace,
                    description=cls.description,
                    completed=False,
                    last_updated=""
                )
                writer.writerow(asdict(entry))

        logger.info(f"Progress file initialized with {len(classes)} entries")

    def load_progress(self) -> List[ProgressEntry]:
        """
        進捗CSVを読み込み

        Returns:
            ProgressEntryのリスト
        """
        if not self.progress_file.exists():
            return []

        entries = []
        with open(self.progress_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # completedをboolに変換
                row['completed'] = row['completed'].lower() in ('true', '1', 'yes')
                entries.append(ProgressEntry(**row))

        return entries

    def get_pending_entries(self, limit: Optional[int] = None) -> List[ProgressEntry]:
        """
        未完了のエントリーを取得

        Args:
            limit: 取得する最大件数（Noneの場合は全件）

        Returns:
            未完了のProgressEntryのリスト
        """
        all_entries = self.load_progress()
        pending = [e for e in all_entries if not e.completed]

        if limit is not None:
            return pending[:limit]
        return pending

    def mark_completed(self, full_name: str):
        """
        指定されたクラスを完了とマーク

        Args:
            full_name: クラスの完全修飾名
        """
        entries = self.load_progress()

        # 該当エントリーを更新
        updated = False
        for entry in entries:
            if entry.full_name == full_name:
                entry.completed = True
                entry.last_updated = datetime.now().isoformat()
                updated = True
                break

        if not updated:
            logger.warning(f"Entry not found in progress file: {full_name}")
            return

        # CSVを書き直し
        with open(self.progress_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            for entry in entries:
                writer.writerow(asdict(entry))

        logger.debug(f"Marked as completed: {full_name}")

    def get_statistics(self) -> dict:
        """
        進捗統計を取得

        Returns:
            統計情報の辞書
        """
        entries = self.load_progress()
        total_count = len(entries)
        completed_count = sum(1 for e in entries if e.completed)
        pending_count = total_count - completed_count

        return {
            'total': total_count,
            'completed': completed_count,
            'pending': pending_count,
            'progress_percentage': (completed_count / total_count * 100) if total_count > 0 else 0
        }

    def reset_progress(self):
        """全てのエントリーを未完了にリセット"""
        entries = self.load_progress()

        for entry in entries:
            entry.completed = False
            entry.last_updated = ""

        with open(self.progress_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            for entry in entries:
                writer.writerow(asdict(entry))

        logger.info("Progress reset: all entries marked as pending")

    def entry_to_class_info(self, entry: ProgressEntry) -> ClassInfo:
        """
        ProgressEntryをClassInfoに変換

        Args:
            entry: ProgressEntry

        Returns:
            ClassInfo
        """
        return ClassInfo(
            name=entry.name,
            full_name=entry.full_name,
            url=entry.url,
            type=entry.type,
            namespace=entry.namespace,
            description=entry.description
        )
