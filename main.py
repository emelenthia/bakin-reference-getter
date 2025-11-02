"""
エントリーポイント
"""
from pathlib import Path
from src.scraper import BakinScraper
from src.parser import BakinParser
from src.markdown_generator import MarkdownGenerator

def main():
    print("Bakin Documentation Scraper")
    print("=" * 50)

    scraper = BakinScraper()
    parser = BakinParser()
    generator = MarkdownGenerator()

    # annotated.htmlから全クラスリストを取得
    print("\n[1/2] Fetching class list...")
    soup = scraper.fetch_annotated_page()
    classes = parser.parse_annotated_page(soup)
    print(f"  Found {len(classes)} classes")

    # 索引ファイルを生成
    print("\n[2/2] Generating index...")
    index_md = generator.generate_index_markdown(classes)
    index_path = Path("output/index.md")
    generator.save_markdown(index_md, index_path)
    print(f"  Saved: {index_path}")

    print("\nDone!")

if __name__ == '__main__':
    main()
