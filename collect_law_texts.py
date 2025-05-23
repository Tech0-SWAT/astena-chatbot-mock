import os

def collect_xml_texts(directory: str):
    """
    指定ディレクトリ内のxmlファイルをすべて読み込み、ファイル名と内容の辞書を返す
    """
    xml_texts = {}
    for filename in os.listdir(directory):
        if filename.endswith('.xml'):
            path = os.path.join(directory, filename)
            with open(path, encoding='utf-8') as f:
                xml_texts[filename] = f.read()
    return xml_texts

if __name__ == "__main__":
    # テスト実行
    xml_texts = collect_xml_texts("document")
    for name, text in xml_texts.items():
        print(f"==== {name} ====")
        print(text[:500], "...\n")
