import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv
from langchain.docstore.document import Document

# 環境変数を読み込み
load_dotenv()

def extract_structured_text_from_pdf(pdf_path: str) -> str:
    """
    PDFファイルからAzure Document Intelligenceを使用して構造化テキストを抽出
    
    Parameters:
    - pdf_path: str : PDFファイルのパス
    
    Returns:
    - str : 抽出された構造化テキスト（Markdown形式）
    """
    AZURE_ENDPOINT = os.getenv("DOC_ENDPOINT")
    AZURE_KEY = os.getenv("DOC_API_KEY")
    
    if not AZURE_ENDPOINT or not AZURE_KEY:
        raise ValueError("Azure Document Intelligence の環境変数が設定されていません")
    
    # Azure Document Intelligenceクライアント作成
    client = DocumentIntelligenceClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_KEY)
    )
    
    # PDFファイルを開いて送信
    with open(pdf_path, "rb") as doc:
        poller = client.begin_analyze_document(
            "prebuilt-layout",
            doc,
            output_content_format="markdown",
            content_type="application/octet-stream",
        )
        result = poller.result()
    
    return extract_structured_text(result)


def extract_structured_text(result) -> str:
    """
    Azure Document Intelligence の結果から構造化テキストを抽出
    
    Parameters:
    - result : Azure Document Intelligence の解析結果
    
    Returns:
    - str : 構造化テキスト（Markdown形式）
    """
    texts = []

    # テーブル情報をMarkdown形式で抽出
    tables = getattr(result, "tables", [])
    for table in tables:
        nrows = table.row_count
        ncols = table.column_count
        cells = [["" for _ in range(ncols)] for _ in range(nrows)]
        for cell in table.cells:
            r, c = cell.row_index, cell.column_index
            cells[r][c] = cell.content
        # Markdownテーブル形式
        if nrows > 0 and ncols > 0:
            header = "| " + " | ".join(cells[0]) + " |"
            sep = "| " + " | ".join(["---"] * ncols) + " |"
            body = "\n".join(["| " + " | ".join(row) + " |" for row in cells[1:]])
            table_md = "\n".join([header, sep, body])
            texts.append(table_md)

    # 段落情報を階層付きで抽出
    paragraphs = getattr(result, "paragraphs", [])
    for para in paragraphs:
        # heading_levelがあれば見出しとして出力
        heading_level = getattr(para, "role", None)
        if heading_level and hasattr(para, "content"):
            texts.append(f"## {para.content}")
        else:
            texts.append(para.content)

    return "\n\n".join(texts)


def create_document_from_pdf_ocr(pdf_path: str) -> Document:
    """
    PDFファイルからOCRを使用してLangChain Documentオブジェクトを作成
    
    Parameters:
    - pdf_path: str : PDFファイルのパス
    
    Returns:
    - Document : LangChain Documentオブジェクト
    """
    try:
        extracted_text = extract_structured_text_from_pdf(pdf_path)
        return Document(
            page_content=extracted_text,
            metadata={"source": pdf_path, "extraction_method": "azure_document_intelligence"}
        )
    except Exception as e:
        print(f"OCR処理失敗 {pdf_path}: {e}")
        # フォールバック: 従来の方法でPDF読み込み
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        if docs:
            return docs[0]
        else:
            return Document(
                page_content="",
                metadata={"source": pdf_path, "extraction_method": "fallback_error"}
            )