"""
シグネチャのパース・整形モジュール

C++/C#のメソッドシグネチャを解析して、型と変数名の間にスペースを入れるなど、
読みやすい形式に整形する責務を持つ。
"""
import re
from typing import List


class SignatureParser:
    """シグネチャのパース・整形クラス"""

    @staticmethod
    def format_signature(signature: str) -> str:
        """
        メソッドシグネチャ全体を整形

        Args:
            signature: 整形前のシグネチャ（例：play(bool loop, int typeIndex)）

        Returns:
            整形後のシグネチャ
        """
        # メソッド名と括弧部分を分離
        match = re.match(r'^([^(]+)\((.*)\)(.*)$', signature)
        if not match:
            return signature

        method_name = match.group(1)
        params_str = match.group(2)
        suffix = match.group(3)  # const などの修飾子

        # パラメータがない場合
        if not params_str.strip():
            return signature

        # パラメータをカンマで分割
        params = SignatureParser._split_parameters(params_str)

        # 各パラメータを整形
        formatted_params = [SignatureParser.format_parameter(p) for p in params]

        # 再構築
        return f"{method_name}({', '.join(formatted_params)}){suffix}"

    @staticmethod
    def _split_parameters(params_str: str) -> List[str]:
        """
        パラメータ文字列をカンマで分割（ネストした<>内のカンマは無視）

        Args:
            params_str: パラメータ文字列

        Returns:
            分割されたパラメータのリスト
        """
        params = []
        current = []
        depth = 0  # <> のネストレベル

        for char in params_str:
            if char == '<':
                depth += 1
                current.append(char)
            elif char == '>':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                # トップレベルのカンマで分割
                params.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        # 最後のパラメータ
        if current:
            params.append(''.join(current).strip())

        return params

    @staticmethod
    def format_parameter(param: str) -> str:
        """
        パラメータを整形（型と変数名の間にスペースを入れる）

        Args:
            param: 整形前のパラメータ（例：SurroundModesurroundMode）

        Returns:
            整形後のパラメータ（例：SurroundMode surroundMode）
        """
        param = param.strip()

        # 既にスペースがある場合はそのまま
        if ' ' in param:
            return param

        # 空の場合
        if not param:
            return param

        # 優先度1: 修飾子（*, ^, &）の直後で分割
        for symbol in ['^', '*', '&']:
            idx = param.rfind(symbol)
            if idx >= 0 and idx < len(param) - 1:
                return f"{param[:idx+1]} {param[idx+1:]}"

        # 優先度2: テンプレート終了（>）の後に小文字が来る位置
        idx = param.rfind('>')
        if idx >= 0 and idx < len(param) - 1 and param[idx + 1].islower():
            return f"{param[:idx+1]} {param[idx+1:]}"

        # 優先度3: 数字の後に小文字が来る位置
        for i in range(len(param) - 1, 0, -1):
            if param[i - 1].isdigit() and param[i].islower():
                return f"{param[:i]} {param[i:]}"

        # 優先度4: 型名とキャメルケース変数名の境界を探す
        # 例：SurroundModesurroundMode → SurroundMode surroundMode
        # 大文字→小文字が連続する部分を探し、その後に大文字→小文字が再び現れる位置で分割
        # つまり、"Mode" の後の "surroundMode" を見つける

        # まず、大文字で始まる単語の境界を全て見つける
        upper_positions = [i for i in range(len(param)) if param[i].isupper()]

        if len(upper_positions) >= 2:
            # 最後の大文字位置から逆順に探す
            for i in range(len(upper_positions) - 1, 0, -1):
                pos = upper_positions[i]
                # この位置の次が小文字で、かつ前の文字が小文字の場合
                # （例：...e→s→u... の s の位置）
                if (pos > 0 and
                    pos < len(param) - 1 and
                    param[pos - 1].islower() and
                    param[pos].isupper() and
                    param[pos + 1].islower()):
                    return f"{param[:pos]} {param[pos:]}"

        # 分割できない場合はそのまま
        return param
