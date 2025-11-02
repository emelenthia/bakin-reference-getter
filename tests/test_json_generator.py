"""
JsonGeneratorのテスト
"""
import json
import tempfile
from pathlib import Path

import pytest

from src.parser import ClassInfo, ClassDetail
from src.json_generator import JsonGenerator


@pytest.fixture
def sample_class_info():
    """テスト用のClassInfo"""
    return ClassInfo(
        name="TestClass",
        full_name="FakeNamespace.TestClass",
        url="class_fake_namespace_1_1_test_class.html",
        type="class",
        namespace="FakeNamespace",
        description="テスト用クラス"
    )


@pytest.fixture
def sample_class_detail(sample_class_info):
    """テスト用のClassDetail"""
    return ClassDetail(
        info=sample_class_info,
        description_full="これはテスト用のクラスです。",
        inherits_from=["BaseClass"],
        methods=[
            {
                "name": "doSomething",
                "signature": "doSomething(int value)",
                "return_type": "void",
                "is_static": False
            },
            {
                "name": "create",
                "signature": "create()",
                "return_type": "TestClass",
                "is_static": True
            }
        ],
        properties=[
            {
                "name": "Value",
                "type": "int",
                "declaration": "Value",
                "is_static": False
            }
        ],
        fields=[
            {
                "name": "data",
                "type": "void*",
                "declaration": "data = NULL"
            }
        ]
    )


class TestJsonGenerator:
    """JsonGeneratorクラスのテスト"""

    def test_generate_class_json_structure(self, sample_class_detail):
        """JSONの基本構造を確認"""
        generator = JsonGenerator()
        result = generator.generate_class_json(sample_class_detail)

        # トップレベルキーの確認
        assert "class_info" in result
        assert "description_full" in result
        assert "inherits_from" in result
        assert "methods" in result
        assert "properties" in result
        assert "fields" in result

    def test_generate_class_json_class_info(self, sample_class_detail):
        """class_infoセクションの確認"""
        generator = JsonGenerator()
        result = generator.generate_class_json(sample_class_detail)

        class_info = result["class_info"]
        assert class_info["name"] == "TestClass"
        assert class_info["full_name"] == "FakeNamespace.TestClass"
        assert class_info["namespace"] == "FakeNamespace"
        assert class_info["type"] == "class"
        assert "document_url" in class_info
        assert "rpgbakin.com" in class_info["document_url"]

    def test_generate_class_json_methods_separation(self, sample_class_detail):
        """メソッドが静的/インスタンスで分離されているか確認"""
        generator = JsonGenerator()
        result = generator.generate_class_json(sample_class_detail)

        methods = result["methods"]
        assert "instance_methods" in methods
        assert "static_methods" in methods

        # インスタンスメソッドの確認
        assert len(methods["instance_methods"]) == 1
        assert methods["instance_methods"][0]["name"] == "doSomething"
        assert methods["instance_methods"][0]["is_static"] is False

        # 静的メソッドの確認
        assert len(methods["static_methods"]) == 1
        assert methods["static_methods"][0]["name"] == "create"
        assert methods["static_methods"][0]["is_static"] is True

    def test_generate_class_json_inherits(self, sample_class_detail):
        """継承情報の確認"""
        generator = JsonGenerator()
        result = generator.generate_class_json(sample_class_detail)

        assert result["inherits_from"] == ["BaseClass"]

    def test_generate_class_json_properties(self, sample_class_detail):
        """プロパティ情報の確認"""
        generator = JsonGenerator()
        result = generator.generate_class_json(sample_class_detail)

        properties = result["properties"]
        assert len(properties) == 1
        assert properties[0]["name"] == "Value"
        assert properties[0]["type"] == "int"

    def test_generate_class_json_fields(self, sample_class_detail):
        """フィールド情報の確認"""
        generator = JsonGenerator()
        result = generator.generate_class_json(sample_class_detail)

        fields = result["fields"]
        assert len(fields) == 1
        assert fields[0]["name"] == "data"
        assert fields[0]["type"] == "void*"

    def test_save_json_creates_file(self, sample_class_detail):
        """JSONファイルが正しく保存されるか確認"""
        generator = JsonGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_file = tmpdir_path / "test.json"

            # JSON保存
            data = generator.generate_class_json(sample_class_detail)
            generator.save_json(data, json_file)

            # ファイルが存在するか確認
            assert json_file.exists()

            # ファイル内容を読み込んで検証
            with open(json_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            assert loaded_data["class_info"]["name"] == "TestClass"
            assert "instance_methods" in loaded_data["methods"]

    def test_save_json_creates_directory(self, sample_class_detail):
        """親ディレクトリが存在しない場合に作成されるか確認"""
        generator = JsonGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_file = tmpdir_path / "subdir" / "nested" / "test.json"

            # JSON保存（親ディレクトリは存在しない）
            data = generator.generate_class_json(sample_class_detail)
            generator.save_json(data, json_file)

            # ファイルとディレクトリが作成されているか確認
            assert json_file.exists()
            assert json_file.parent.exists()

    def test_save_class_json(self, sample_class_detail):
        """save_class_json便利メソッドのテスト"""
        generator = JsonGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_file = tmpdir_path / "test.json"

            # ClassDetailを直接保存
            generator.save_class_json(sample_class_detail, json_file)

            # ファイルが存在するか確認
            assert json_file.exists()

            # 内容確認
            with open(json_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            assert loaded_data["class_info"]["full_name"] == "FakeNamespace.TestClass"

    def test_json_encoding_utf8(self, sample_class_detail):
        """日本語が正しくUTF-8でエンコードされるか確認"""
        generator = JsonGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_file = tmpdir_path / "test.json"

            # JSON保存
            data = generator.generate_class_json(sample_class_detail)
            generator.save_json(data, json_file)

            # ファイル内容を確認（日本語が含まれているはず）
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # ensure_ascii=Falseなので日本語がそのまま含まれる
            assert "テスト用クラス" in content
            assert "これはテスト用のクラスです" in content
