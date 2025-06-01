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

def collect_law_texts_list(directory: str):
    """
    指定ディレクトリ内のxmlファイルをすべて読み込み、
    'ファイル名' と '内容' を持つ辞書のリストを返す（law_list形式）
    """
    xml_dict = collect_xml_texts(directory)
    return [{"ファイル名": name, "内容": content} for name, content in xml_dict.items()]

if __name__ == "__main__":
    # テスト実行
    xml_texts = collect_xml_texts("document")
    for name, text in xml_texts.items():
        print(f"==== {name} ====")
        print(text[:500], "...\n")
