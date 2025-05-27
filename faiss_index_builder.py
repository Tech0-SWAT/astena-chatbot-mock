import os
# from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings.azure_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
import streamlit as st

def build_faiss_index(
    # filename: str = "ey-japan-info-sensor-2023-06-03.pdf",
    data_dir: str = "document/docs_for_index",
    storage_dir: str = "storage",
    model_name: str = "intfloat/multilingual-e5-large",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> FAISS:
    """
    指定されたPDFファイルを読み込み、FAISSインデックスを作成・保存して返す関数

    Parameters:
    - data_dir: str : ファイル格納ディレクトリ（デフォルト: "document"）
    - storage_dir: str : インデックス保存先ディレクトリ（デフォルト: "storage"）
    - model_name: str : 埋め込みモデル名（デフォルト: multilingual-e5-large）
    - chunk_size: int : テキスト分割チャンクサイズ
    - chunk_overlap: int : チャンクの重なり

    Returns:
    - FAISS : 作成されたFAISSインデックスオブジェクト
    """
    # .env読み込み
    # load_dotenv()

    # パス設定
    base_dir = os.path.abspath("")
    data_path = os.path.join(base_dir, data_dir)
    index_path = os.path.join(base_dir, storage_dir)

    print(f"ファイル読み込み: {data_path}")
    os.makedirs(index_path, exist_ok=True)

    # 1. ドキュメント読み込み
    loader = DirectoryLoader(data_path, loader_cls=UnstructuredFileLoader)
    documents = loader.load()
    print(f"ドキュメント数: {len(documents)}")

    # 2. テキスト分割
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_texts = splitter.split_documents(documents)
    print(f"チャンク数: {len(split_texts)}")

    # 3. 埋め込みモデル読み込み（Azure OpenAI埋め込みに変更）
    # embedding_model = AzureOpenAIEmbeddings(
        # chunk_size=2048,
        #azure_deployment="text-embedding-3-large-astena"
    #)
    #print("埋め込みモデル読み込み: Azure OpenAI Embedding")

    # 3. Azure OpenAI埋め込みモデル（環境変数はst.secretsから）
    embedding_model = AzureOpenAIEmbeddings(
        chunk_size=2048,
        azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"], 
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],                
        api_key=os.environ["AZURE_OPENAI_API_KEY"]                         
    )
    print("埋め込みモデル読み込み: Azure OpenAI Embedding")

    # 4. FAISSインデックス作成
    index = FAISS.from_documents(documents=split_texts, embedding=embedding_model)
    print("FAISSインデックス作成完了")

    # 5. 保存
    index.save_local(folder_path=index_path)
    print(f"インデックス保存済み: {index_path}")

    return index


import sys
import traceback
if __name__ == "__main__":
    try:
        build_faiss_index()
        print("\n=== 完了 ===")
    except Exception as e:
        print("\n❌ エラーが発生しました:")
        traceback.print_exc(file=sys.stdout)
