"""
Parser（シグネチャ整形）のテスト
"""
import pytest
from bs4 import BeautifulSoup

from src.parser import BakinParser, ClassInfo


class TestParserSignatureFormatting:
    """パーサーのシグネチャ整形機能のテスト"""

    @pytest.fixture
    def parser(self):
        """パーサーインスタンス"""
        return BakinParser()

    @pytest.fixture
    def sample_class_info(self):
        """テスト用のClassInfo"""
        return ClassInfo(
            name="TestClass",
            full_name="Test.TestClass",
            url="class_test_1_1_test_class.html",
            type="class",
            namespace="Test",
            description=""
        )

    def test_parse_method_with_spaced_parameters(self, parser, sample_class_info):
        """型と変数名の間にスペースがあるメソッドのパース"""
        html = """
        <table class="memberdecls">
            <tr class="heading">
                <td colspan="2"><h2 class="groupheader"><a id="pub-methods" name="pub-methods"></a>
                公開メンバ関数</h2></td>
            </tr>
            <tr class="memitem:abc123">
                <td class="memItemLeft">void</td>
                <td class="memItemRight">
                    <a class="el" href="#abc123">doSomething</a> (int value)
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        detail = parser.parse_class_page(soup, sample_class_info)

        assert len(detail.methods) == 1
        method = detail.methods[0]
        assert method['name'] == 'doSomething'
        # HTMLからのテキスト抽出でメソッド名と括弧の間にスペースが入る
        assert method['signature'] == 'doSomething (int value)'
        assert 'int value' in method['signature']

    def test_parse_method_with_linked_type(self, parser, sample_class_info):
        """型がリンク（<a>タグ）になっている場合のパース"""
        html = """
        <table class="memberdecls">
            <tr class="heading">
                <td colspan="2"><h2 class="groupheader"><a id="pub-methods" name="pub-methods"></a>
                公開メンバ関数</h2></td>
            </tr>
            <tr class="memitem:abc123">
                <td class="memItemLeft">bool</td>
                <td class="memItemRight">
                    <a class="el" href="#abc123">play</a>
                    (<a class="el" href="namespace.html">SurroundMode</a> surroundMode,
                     <a class="el" href="namespace.html">VolumeRollOffType</a> volumeRollOff)
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        detail = parser.parse_class_page(soup, sample_class_info)

        assert len(detail.methods) == 1
        method = detail.methods[0]
        assert method['name'] == 'play'
        # 型と変数名の間にスペースがあることを確認
        assert 'SurroundMode surroundMode' in method['signature']
        assert 'VolumeRollOffType volumeRollOff' in method['signature']

    def test_parse_static_method_removes_static_keyword(self, parser, sample_class_info):
        """静的メソッドの戻り値型からstaticキーワードが削除されるか確認"""
        html = """
        <table class="memberdecls">
            <tr class="heading">
                <td colspan="2"><h2 class="groupheader"><a id="pub-static-methods" name="pub-static-methods"></a>
                静的公開メンバ関数</h2></td>
            </tr>
            <tr class="memitem:def456">
                <td class="memItemLeft">static TestClass</td>
                <td class="memItemRight">
                    <a class="el" href="#def456">create</a> ()
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        detail = parser.parse_class_page(soup, sample_class_info)

        assert len(detail.methods) == 1
        method = detail.methods[0]
        assert method['is_static'] is True
        # return_typeからstaticが削除されている
        assert method['return_type'] == 'TestClass'
        assert 'static' not in method['return_type']

    def test_parse_field_with_linked_type(self, parser, sample_class_info):
        """フィールドの型がリンクになっている場合のパース"""
        html = """
        <table class="memberdecls">
            <tr class="heading">
                <td colspan="2"><h2 class="groupheader"><a id="pub-attribs" name="pub-attribs"></a>
                公開変数類</h2></td>
            </tr>
            <tr class="memitem:field123">
                <td class="memItemLeft">
                    <a class="el" href="class.html">kmySound::WaveSound</a> *
                </td>
                <td class="memItemRight">
                    <a class="el" href="#field123">obj</a> = NULL
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        detail = parser.parse_class_page(soup, sample_class_info)

        assert len(detail.fields) == 1
        field = detail.fields[0]
        assert field['name'] == 'obj'
        # HTMLのポインタ記号の配置により、スペースなしになる
        assert field['type'] == 'kmySound::WaveSound*' or field['type'] == 'kmySound::WaveSound *'

    def test_parse_method_with_template_parameter(self, parser, sample_class_info):
        """テンプレート引数を持つパラメータのパース"""
        html = """
        <table class="memberdecls">
            <tr class="heading">
                <td colspan="2"><h2 class="groupheader"><a id="pub-static-methods" name="pub-static-methods"></a>
                静的公開メンバ関数</h2></td>
            </tr>
            <tr class="memitem:xyz789">
                <td class="memItemLeft">static void</td>
                <td class="memItemRight">
                    <a class="el" href="#xyz789">init</a>
                    (cli::array&lt; int &gt;^ seCounts)
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        detail = parser.parse_class_page(soup, sample_class_info)

        assert len(detail.methods) == 1
        method = detail.methods[0]
        assert method['name'] == 'init'
        # テンプレート引数が含まれ、スペースが適切に配置されている
        assert 'cli::array' in method['signature']
        assert 'seCounts' in method['signature']

    def test_parse_multiple_methods(self, parser, sample_class_info):
        """複数メソッドのパース"""
        html = """
        <table class="memberdecls">
            <tr class="heading">
                <td colspan="2"><h2 class="groupheader"><a id="pub-methods" name="pub-methods"></a>
                公開メンバ関数</h2></td>
            </tr>
            <tr class="memitem:m1">
                <td class="memItemLeft">void</td>
                <td class="memItemRight">
                    <a class="el" href="#m1">method1</a> ()
                </td>
            </tr>
            <tr class="memitem:m2">
                <td class="memItemLeft">int</td>
                <td class="memItemRight">
                    <a class="el" href="#m2">method2</a> (float value)
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        detail = parser.parse_class_page(soup, sample_class_info)

        assert len(detail.methods) == 2
        assert detail.methods[0]['name'] == 'method1'
        assert detail.methods[1]['name'] == 'method2'
        # メソッド名と括弧の間にスペースが入る
        assert detail.methods[0]['signature'] == 'method1 ()'
        assert 'float value' in detail.methods[1]['signature']
