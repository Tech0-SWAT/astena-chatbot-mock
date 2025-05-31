import os
import openai
from dotenv import load_dotenv
from make_df import parse_llm_output_to_dataframe

from collect_law_texts import collect_law_texts_list
from extract_lifetime_azure import extract_lifetime_info_azure
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings.azure_openai import AzureOpenAIEmbeddings
import pandas as pd
import re
import csv


# .env 読み込み
load_dotenv()

def load_account_titles(csv_path: str) -> list:
    """
    勘定科目一覧CSVを読み込み、リストで返す
    """
    account_list = []
    import streamlit as st
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i == 0:
                st.write("CSVヘッダー:", list(row.keys()))
            account_list.append(row)
    return account_list

def asset_judge(user_chat: str, old_chat: str = "", document_text :str = "") -> str:
    """
    ユーザーからの質問文を受け取り、法令・PDF情報・耐用年数データをもとに
    会計的な観点から勘定科目と耐用年数を出力する回答を返す

    Parameters:
        user_chat (str): ユーザーの質問文（例: "エアコンとPCの仕訳教えて"）

    Returns:
        str: 回答文
    """
    
        
    # === STEP 1: FAISSインデックスから類似コンテキスト取得 ===
    # 埋め込みモデル読み込み（Azure OpenAI埋め込みに変更）
    embedding_model = AzureOpenAIEmbeddings(
        chunk_size=2048,
        azure_deployment="text-embedding-3-large-astena"
    )
    index = FAISS.load_local(
        folder_path="storage",
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )

    query_text = user_chat + "\n" + document_text
    print("クエリの内容:")
    print(query_text)
    retrieved_docs = index.similarity_search(query_text, k=2)
    retrieved_context = "\n".join([doc.page_content for doc in retrieved_docs])
    print("類似度の高いチャンク:")
    print(retrieved_context)

    # === STEP 2: 法定耐用年数の情報抽出 ===
    law_list = collect_law_texts_list("document")
    account_list = load_account_titles("document/勘定科目一覧.csv")
    lifetime_info = extract_lifetime_info_azure(user_chat, law_list)

    # 勘定科目一覧をテキスト化
    account_texts = "【勘定科目一覧】\n"
    for row in account_list:
        account_texts += f"{row['勘定科目']}: {row['解説']}\n"

    # === STEP 3: 減価償却に関する法令テキスト読込 ===
    txt_file = "減価償却に関する法令.txt"
    txt_path = os.path.join("document", txt_file)
    txt_content = ""
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            txt_content = f.read()
    else:
        txt_content = "（法令テキストが見つかりませんでした）"

    # === STEP 4: 仕訳例を読込 ===
    example_dir = "document/example_accounting_entry/"
    os.makedirs(example_dir, exist_ok=True)

    # エクセル読み込み
    excel_files = [f for f in os.listdir(example_dir) if f.endswith(('.xlsx', '.xls'))]

    dataframes = {}
    for file in excel_files:
        file_path = os.path.join(example_dir, file)
        try:
            df = pd.read_excel(file_path)
            dataframes[file] = df
            print(f"\n {file} の内容:")
            print(df.head())
        except Exception as e:
            print(f"{file} の読み込み中にエラーが発生しました: {e}")
   
    # 複数Excelファイルの仕訳例を文字列化してまとめる
    accounting_examples_text = ""
    for file, df in dataframes.items():
        accounting_examples_text += f"\n■ {file} の仕訳例:\n"
        accounting_examples_text += df.to_string(index=False)
        accounting_examples_text += "\n"
    print("仕訳実績:")
    print(accounting_examples_text)


    # === STEP 5: Azure OpenAIへ問い合わせ ===
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    client = openai.AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
    )

    # f-string内で複雑な式展開を避けるため、履歴部分を事前に組み立てる
    history_text = f"【過去の会話履歴】\n{old_chat}" if old_chat.strip() else ""

    prompt = f"""
        あなたは日本の会計に精通した経理アシスタントAIです。

        添付の証憑に関する固定資産を取得しました。会計基準および過去の当社の会計処理実績、そして下記の勘定科目一覧に整合するように、各品目ごとに適切な勘定科目と金額（税抜経理ベース）を提案してください。  
        また、以下の点に注意してください：

        - 当社は税抜経理方式を採用しており、仮払消費税の計上が必要です  
        - 証憑の中には非課税・課税対象外取引が含まれている可能性があります  
        - 各固定資産の法定耐用年数も併せて提示してください  
        - 勘定科目、金額については根拠を明確に示してください  
        - 必ず【勘定科目一覧】を参考に、最も適切な勘定科目を選んでください

        勘定科目一覧：
        {account_texts}

        【情報】有形固定資産に関連する会計基準・実務資料の抜粋:
        {retrieved_context}

        【情報】対象品目に対する法定耐用年数（xmlファイルなどから抽出）:
        {lifetime_info}

        【情報】減価償却に関する法令（法令テキスト）:
        {txt_content}

        【情報】仕訳例:
        {accounting_examples_text}

        【ユーザーの質問】
        {user_chat}

        【対象となる証憑テキスト】
        {document_text}

        【過去のチャット情報】
        {history_text}

        【出力形式】
        品目を抽出し各品目について以下の形式で出力してください：

        品目名: （例: ノートPC）  
        ・金額：150,000円  
        ・勘定科目：備品  
        ・法定耐用年数：4年  
        ・根拠：〇〇会計基準第○条、法定耐用年数表より

        - 不明な場合は「該当情報なし」と明記してください。
        - 補足説明があれば端的に記載してください。
        """

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "あなたは日本の会計に精通した経理アシスタントAIです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2048
        )
        print(response)

        response_text = response.choices[0].message.content
        # 表形式に変換
        df = parse_llm_output_to_dataframe(response_text)
        # 表示
        print("\n=== 表形式に整形 ===")
        print(df)

        return response_text
    
    except Exception as e:
        # 詳細なエラー内容を返す
        import traceback
        error_message = f"OpenAI APIリクエストでエラーが発生しました。\n"
        error_message += f"型: {type(e)}\n"
        error_message += f"内容: {str(e)}\n"
        tb = traceback.format_exc()
        error_message += f"トレースバック:\n{tb}\n"
        # openaiのAPIエラーの場合、response属性があれば詳細も出す
        if hasattr(e, "response") and hasattr(e.response, "text"):
            error_message += f"APIレスポンス: {e.response.text}\n"
        return error_message
    


if __name__ == "__main__":
    user_input = input("質問を入力してください: ")
    response = asset_judge(user_input)
    print("\n=== 回答 ===")
    print(response)
