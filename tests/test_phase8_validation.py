"""
フェーズ8の自動検証テスト: エラーハンドリングとロバスト性

検証項目:
1. ✓ ログファイルへの出力設定
2. ✓ エラー時のログ記録
3. ✓ 継続モードによる自動再処理
4. - 失敗状態の追跡（不要になったため削除）
5. - retry-failedコマンド（不要になったため削除）
"""
import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from src.cli import BakinDocumentationScraper
from src.progress_manager import ProgressManager
from src.parser import ClassInfo


@pytest.fixture
def temp_dir():
    """テスト用一時ディレクトリ"""
    test_dir = Path(tempfile.mkdtemp(prefix="phase8_test_"))
    yield test_dir
    shutil.rmtree(test_dir)


def test_logging_configuration_exists():
    """[OK] 1. ログファイルへの出力設定が存在するか確認"""
    # main.pyにログ設定があることを確認
    main_file = Path('main.py')
    assert main_file.exists(), "main.py が存在しません"

    content = main_file.read_text(encoding='utf-8')
    assert 'logging.basicConfig' in content, "ログ設定がありません"
    assert 'FileHandler' in content, "ファイルハンドラーが設定されていません"
    assert 'scraper.log' in content, "ログファイル名が指定されていません"
    assert 'encoding=' in content, "エンコーディング指定がありません"
    print("[OK] ログファイル出力設定")


def test_error_logging_in_scrape(temp_dir, caplog):
    """[OK] 2. エラー時にログ記録されることを確認"""
    # config.yamlを作成（Windowsパスを/に変換）
    temp_dir_str = str(temp_dir).replace('\\', '/')
    config_content = f"""
scraping:
  base_url: "https://example.com/"
  delay: 0

output:
  base_dir: "{temp_dir_str}"
  classes_dir: "{temp_dir_str}/classes"
  namespaces_dir: "{temp_dir_str}/namespaces"
  json_dir: "{temp_dir_str}/json"
  class_list_cache: "{temp_dir_str}/class_list.json"
  progress_file: "{temp_dir_str}/progress.csv"
"""
    config_path = temp_dir / 'config.yaml'
    config_path.write_text(config_content, encoding='utf-8')

    scraper = BakinDocumentationScraper(str(config_path))

    # 進捗ファイルを初期化
    test_class = ClassInfo(
        name="TestClass",
        full_name="Test.TestClass",
        url="test.html",
        type="class",
        namespace="Test",
        description="テスト"
    )
    scraper.progress_manager.initialize_from_class_list([test_class])

    # scrape_classをモックして例外を発生させる
    with patch.object(scraper, 'scrape_class', side_effect=Exception("Test error")):
        with caplog.at_level(logging.ERROR):
            scraper.scrape_with_progress(limit=1)

    # エラーログが記録されていることを確認
    error_logs = [record for record in caplog.records if record.levelname == 'ERROR']
    assert len(error_logs) > 0, "エラーログが記録されていません"
    assert any("Failed to scrape" in record.message for record in error_logs), \
        "適切なエラーメッセージが記録されていません"
    assert any("Test error" in record.message for record in error_logs), \
        "例外メッセージが記録されていません"
    print("[OK] エラー時のログ記録")


def test_continuation_mode_retries_failed(temp_dir):
    """[OK] 3. 継続モードで失敗したクラスが自動的に再処理されることを確認"""
    progress_file = temp_dir / "progress.csv"
    pm = ProgressManager(progress_file)

    # テストデータを作成
    test_classes = [
        ClassInfo(
            name="Class1",
            full_name="Test.Class1",
            url="class1.html",
            type="class",
            namespace="Test",
            description="完了したクラス"
        ),
        ClassInfo(
            name="Class2",
            full_name="Test.Class2",
            url="class2.html",
            type="class",
            namespace="Test",
            description="未完了（失敗）のクラス"
        ),
    ]

    pm.initialize_from_class_list(test_classes)

    # Class1を完了とマーク
    pm.mark_completed("Test.Class1")

    # 未完了エントリーを取得
    pending = pm.get_pending_entries()

    # Class2のみが未完了として取得されることを確認
    assert len(pending) == 1, "未完了エントリー数が正しくありません"
    assert pending[0].full_name == "Test.Class2", "未完了エントリーが正しくありません"
    assert pending[0].completed is False, "completed フラグが正しくありません"

    print("[OK] 継続モードによる自動再処理")


def test_failed_state_removed():
    """- 4. 失敗状態の追跡機能が削除されていることを確認（不要機能）"""
    from src.progress_manager import ProgressEntry

    # ProgressEntryにfailed関連フィールドがないことを確認
    entry_fields = ProgressEntry.__dataclass_fields__.keys()
    assert 'status' not in entry_fields, "status フィールドが残っています（削除済みのはず）"
    assert 'error_message' not in entry_fields, "error_message フィールドが残っています（削除済みのはず）"
    assert 'completed' in entry_fields, "completed フィールドが存在しません"

    # ProgressManagerにfailed関連メソッドがないことを確認
    pm_methods = dir(ProgressManager)
    assert 'mark_failed' not in pm_methods, "mark_failed メソッドが残っています（削除済みのはず）"
    assert 'get_failed_entries' not in pm_methods, "get_failed_entries メソッドが残っています（削除済みのはず）"

    print("- 失敗状態の追跡: 削除済み（不要機能）")


def test_retry_failed_command_removed():
    """- 5. retry-failedコマンドが削除されていることを確認（不要機能）"""
    from src.cli import cli

    # CLIコマンドリストを取得
    commands = cli.commands.keys()
    assert 'retry-failed' not in commands, "retry-failed コマンドが残っています（削除済みのはず）"

    # BakinDocumentationScraperにretry_failed_classesメソッドがないことを確認
    scraper_methods = dir(BakinDocumentationScraper)
    assert 'retry_failed_classes' not in scraper_methods, \
        "retry_failed_classes メソッドが残っています（削除済みのはず）"

    print("- retry-failedコマンド: 削除済み（不要機能）")


def test_simple_progress_model():
    """✓ 進捗管理がシンプルなモデルになっていることを確認"""
    from src.progress_manager import ProgressManager

    # CSV_HEADERSがシンプルな構成になっていることを確認
    headers = ProgressManager.CSV_HEADERS
    assert 'completed' in headers, "completed フィールドが存在しません"
    assert 'status' not in headers, "status フィールドが残っています（削除済みのはず）"
    assert 'error_message' not in headers, "error_message フィールドが残っています（削除済みのはず）"

    # 必要最小限のフィールドのみであることを確認
    expected_headers = [
        'full_name', 'name', 'url', 'type',
        'namespace', 'description', 'completed', 'last_updated'
    ]
    assert headers == expected_headers, f"ヘッダーが期待と異なります: {headers}"

    print("✓ シンプルな進捗管理モデル: OK")


def test_phase8_summary():
    """フェーズ8検証サマリー"""
    print("\n" + "="*60)
    print("フェーズ8検証サマリー: エラーハンドリングとロバスト性")
    print("="*60)
    print("✓ 1. ログファイルへの出力設定")
    print("✓ 2. エラー時のログ記録")
    print("✓ 3. 継続モードによる自動再処理")
    print("- 4. 失敗状態の追跡（不要のため削除）")
    print("- 5. retry-failedコマンド（不要のため削除）")
    print("✓ 6. シンプルな進捗管理モデル")
    print("="*60)
    print("結果: フェーズ8完了（シンプル版）")
    print("="*60)
