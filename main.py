"""
エントリーポイント
"""
import logging
from pathlib import Path
from src.cli import cli

# ログ設定
log_file = Path('scraper.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()  # コンソールにも出力
    ]
)

if __name__ == '__main__':
    cli()
