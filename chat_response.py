import os
import openai
from dotenv import load_dotenv

from collect_law_texts import collect_law_texts_list
from extract_lifetime_azure import extract_lifetime_info_azure
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings.azure_openai import AzureOpenAIEmbeddings

# .env 読み込み
load_dotenv()

def generate_response(user_chat: str, old_chat: str = "", document_text :str = "") -> str:
    """
    ユーザーからの質問文を受け取り、法令・PDF情報・耐用年数データをもとに
    会計的な観点から勘定科目と耐用年数を出力する回答を返す

    Parameters:
        user_chat (str): ユーザーの質問文（例: "エアコンとPCの仕訳教えて"）

    Returns:
        str: 回答文
    """

    # === STEP 1: FAISSインデックスから類似コンテキスト取得 ===
    # 3. 埋め込みモデル読み込み（Azure OpenAI埋め込みに変更）
    embedding_model = AzureOpenAIEmbeddings(
        chunk_size=2048,
        azure_deployment="text-embedding-3-large-astena"
    )
    index = FAISS.load_local(
        folder_path="storage",
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )

    retrieved_docs = index.similarity_search(user_chat, k=2)
    retrieved_context = "\n".join([doc.page_content for doc in retrieved_docs])

    # === STEP 2: 法定耐用年数の情報抽出 ===
    law_list = collect_law_texts_list("document")
    lifetime_info = extract_lifetime_info_azure(user_chat, law_list)

    # === STEP 3: 減価償却に関する法令テキスト読込 ===
    txt_file = "減価償却に関する法令.txt"
    txt_path = os.path.join("document", txt_file)
    txt_content = ""
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            txt_content = f.read()
    else:
        txt_content = "（法令テキストが見つかりませんでした）"

    # === STEP 4: Azure OpenAIへ問い合わせ ===
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
        以下の情報をもとに、ユーザーの質問に対して会計的な観点から適切な回答をしてください。

        【情報】有形固定資産に関連する会計基準・実務資料の抜粋:
        {retrieved_context}

        【情報】対象品目に対する法定耐用年数（xmlファイルなどから抽出）:
        {lifetime_info}

        【情報】減価償却に関する法令（法令テキスト）:
        {txt_content}

        【ユーザーの質問】
        {user_chat}

        [質問対象]
        {document_text}

        {history_text}

        【出力形式】
        ユーザーの質問に対する総合的な回答を端的に記述してください。
        - 可能であれば、根拠となる法令や会計基準の抜粋を添えてください。
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
        return response.choices[0].message.content
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
    response = generate_response(user_input)
    print("\n=== 回答 ===")
    print(response)
