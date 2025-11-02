"""
parser.pyのテストコード
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
from src.parser import BakinParser, ClassInfo


def test_parse_annotated_page():
    """annotated.htmlのパーステスト"""
    # テストデータからannotated.htmlを読み込む
    test_data_file = Path(__file__).parent / "data" / "annotated.html"

    assert test_data_file.exists(), f"Test data not found: {test_data_file}"

    with open(test_data_file, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    parser = BakinParser()

    classes = parser.parse_annotated_page(soup)

    # 実際のannotated.htmlから678クラスが抽出されることを確認
    assert len(classes) == 678, f"Expected 678 classes, but found {len(classes)}"

    # いくつかのクラスの内容を具体的に確認
    # 最初のクラス（SharpKmyAudio.Sound）
    first_class = classes[0]
    assert first_class.name == "Sound", f"Expected 'Sound' but got '{first_class.name}'"
    assert first_class.full_name == "SharpKmyAudio.Sound", f"Expected 'SharpKmyAudio.Sound' but got '{first_class.full_name}'"
    assert first_class.url == "class_sharp_kmy_audio_1_1_sound.html", f"Expected specific URL but got '{first_class.url}'"
    assert first_class.type == "class", f"Expected 'class' but got '{first_class.type}'"
    assert first_class.namespace == "SharpKmyAudio", f"Expected 'SharpKmyAudio' but got '{first_class.namespace}'"

    # Yukar.Engine名前空間のクラスが存在することを確認
    yukar_engine_classes = [c for c in classes if c.namespace == "Yukar.Engine"]
    assert len(yukar_engine_classes) > 0, "No classes found in Yukar.Engine namespace"

    # Yukar.Common.Rom名前空間のクラスが存在することを確認
    yukar_common_rom_classes = [c for c in classes if c.namespace == "Yukar.Common.Rom"]
    assert len(yukar_common_rom_classes) > 0, "No classes found in Yukar.Common.Rom namespace"
