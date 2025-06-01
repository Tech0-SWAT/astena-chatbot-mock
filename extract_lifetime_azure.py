import os
from collect_law_texts import collect_law_texts_list
import openai
from dotenv import load_dotenv

# .envから環境変数を読み込む
load_dotenv()

def extract_lifetime_info_azure(input_text: str, law_list: list) -> str:
    """
    INPUT_TEXT（見積書等）とxmlファイル群の内容をAzure OpenAIに渡し、該当する耐用年数情報を抽出する
    必要な環境変数:
      AZURE_OPENAI_API_KEY
      AZURE_OPENAI_ENDPOINT
      AZURE_OPENAI_DEPLOYMENT（デプロイメント名）
      AZURE_OPENAI_API_VERSION（例: 2024-02-15-preview など）
    """
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    if not (api_key and azure_endpoint and deployment):
        raise ValueError("AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT を環境変数で指定してください。")

    client = openai.AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
    )

    # すべてのxmlファイルの内容を1つのテキストにまとめる
    law_texts = ""
    for item in law_list:
        law_texts += f"【{item['ファイル名']}】\n{item['内容']}\n\n"

    prompt = f"""
あなたは日本の減価償却資産の法定耐用年数に詳しいAIです。
以下は法定耐用年数に関する法令xmlファイルの全文です。

{law_texts}

--- ここからINPUT_TEXT ---
{input_text}
--- ここまでINPUT_TEXT ---

【タスク】
- INPUT_TEXTに記載された各品目について、最も該当する資産分類・細目・耐用年数をxml群から探し、以下の形式で出力してください。

【出力例】
品目名: ○○○
分類: ○○○
細目: ○○○
耐用年数: ○○年

- 必ず全品目について出力してください。
- xmlに該当がなければ「該当なし」と記載してください。
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "あなたは減価償却資産の法定耐用年数に詳しいAIです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=2048
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    law_list = collect_law_texts_list("document")
    input_text = "エアコン\nパソコン\n木造住宅"
    result = extract_lifetime_info_azure(input_text, law_list)
    print(result)
