"""
フェーズ5のユニットテスト: ProgressManager

実行方法:
    pytest tests/test_progress_manager_integration.py
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import json
import csv

from src.parser import ClassInfo
from src.progress_manager import ProgressManager


@pytest.fixture
def test_classes():
    """テスト用のクラスリストを読み込むフィクスチャ"""
    test_data_path = Path(__file__).parent / "data" / "sample_classes.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        classes_data = json.load(f)
    return [ClassInfo(**data) for data in classes_data]


@pytest.fixture
def temp_dir():
    """テスト用一時ディレクトリを作成するフィクスチャ"""
    test_dir = Path(tempfile.mkdtemp(prefix="bakin_test_"))
    yield test_dir
    shutil.rmtree(test_dir)


def test_initialize_from_class_list(test_classes, temp_dir):
    """progress.csvの初期化テスト"""
    progress_file = temp_dir / "progress.csv"
    pm = ProgressManager(progress_file)

    pm.initialize_from_class_list(test_classes)

    # ファイルが作成されたことを確認
    assert progress_file.exists()

    # CSVファイルの中身を確認
    with open(progress_file, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # ヘッダーを確認
    expected_headers = ['full_name', 'name', 'url', 'type', 'namespace', 'description', 'completed', 'last_updated']
    assert reader.fieldnames == expected_headers

    # データ行数を確認（sample_classes.jsonには5件のクラスが定義されている）
    assert len(rows) == 5

    # 最初のデータ行を確認（sample_classes.jsonの最初のエントリ）
    first_row = rows[0]
    assert first_row['full_name'] == 'FakeEngine.Core.GameEngine'
    assert first_row['name'] == 'GameEngine'
    assert first_row['url'] == 'class_fake_engine_1_1_core_1_1_game_engine.html'
    assert first_row['type'] == 'class'
    assert first_row['namespace'] == 'FakeEngine.Core'
    assert first_row['description'] == 'ゲームエンジンのコアクラス'
    assert first_row['completed'] == 'False'
    assert first_row['last_updated'] == ''

    # 統計を確認
    stats = pm.get_statistics()
    assert stats['total'] == 5
    assert stats['completed'] == 0
    assert stats['pending'] == 5
    assert stats['progress_percentage'] == 0.0


def test_get_pending_entries(test_classes, temp_dir):
    """未完了エントリーの取得テスト"""
    progress_file = temp_dir / "progress.csv"
    pm = ProgressManager(progress_file)
    pm.initialize_from_class_list(test_classes)

    # limitなしで全件取得
    pending = pm.get_pending_entries()
    assert len(pending) == 5

    # limitありで取得
    pending_limited = pm.get_pending_entries(limit=3)
    assert len(pending_limited) == 3

    # 最初のエントリーの内容を確認
    first_pending = pending[0]
    assert first_pending.full_name == 'FakeEngine.Core.GameEngine'
    assert first_pending.completed is False


def test_mark_completed(test_classes, temp_dir):
    """完了マーク機能のテスト"""
    progress_file = temp_dir / "progress.csv"
    pm = ProgressManager(progress_file)
    pm.initialize_from_class_list(test_classes)

    # 特定のクラスを完了マーク
    pm.mark_completed('FakeEngine.Core.GameEngine')

    # 統計を確認
    stats = pm.get_statistics()
    assert stats['completed'] == 1
    assert stats['pending'] == 4
    assert stats['progress_percentage'] == pytest.approx(20.0)

    # エントリーを確認
    entries = pm.load_progress()
    completed_entry = next(e for e in entries if e.full_name == 'FakeEngine.Core.GameEngine')
    assert completed_entry.completed is True
    assert completed_entry.last_updated != ""


def test_entry_to_class_info(test_classes, temp_dir):
    """ProgressEntryからClassInfoへの変換テスト"""
    progress_file = temp_dir / "progress.csv"
    pm = ProgressManager(progress_file)
    pm.initialize_from_class_list(test_classes)

    entries = pm.load_progress()
    first_entry = entries[0]

    class_info = pm.entry_to_class_info(first_entry)

    # 期待値と比較
    assert class_info.name == 'GameEngine'
    assert class_info.full_name == 'FakeEngine.Core.GameEngine'
    assert class_info.url == 'class_fake_engine_1_1_core_1_1_game_engine.html'
    assert class_info.type == 'class'
    assert class_info.namespace == 'FakeEngine.Core'
    assert class_info.description == 'ゲームエンジンのコアクラス'
