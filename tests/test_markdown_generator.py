"""
markdown_generator.pyのテストコード
"""
import sys
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import ClassInfo, ClassDetail
from src.markdown_generator import MarkdownGenerator


def test_generate_class_markdown():
    """クラスMarkdown生成のテスト"""
    info = ClassInfo(
        name="TestClass",
        full_name="Test.Namespace.TestClass",
        url="test.html",
        type="class",
        namespace="Test.Namespace",
        description="テスト用"
    )
    detail = ClassDetail(info=info)
    detail.description_full = "テストの説明"

    gen = MarkdownGenerator()
    md = gen.generate_class_markdown(detail)

    assert "# Test.Namespace.TestClass" in md
    assert "Test.Namespace" in md


def test_generate_index_markdown():
    """索引Markdown生成のテスト"""
    classes = [
        ClassInfo("C1", "NS1.C1", "c1.html", "class", "NS1"),
        ClassInfo("C2", "NS2.C2", "c2.html", "struct", "NS2"),
    ]

    gen = MarkdownGenerator()
    index_md = gen.generate_index_markdown(classes)

    assert "# RPG Developer Bakin C# リファレンス索引" in index_md
    assert "NS1" in index_md
    assert "NS2" in index_md


def test_save_markdown():
    """ファイル保存のテスト"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        gen = MarkdownGenerator()
        test_file = temp_dir / "test.md"
        gen.save_markdown("# Test", test_file)
        assert test_file.exists()
    finally:
        shutil.rmtree(temp_dir)
