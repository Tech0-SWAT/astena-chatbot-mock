import os
import openai
from dotenv import load_dotenv

load_dotenv()

def asset_extract_items(document_text: str) -> str:
    """
    テキストから品目と金額のみをLLMで抽出して返す
    """

    # OpenAIクライアント設定
    client = openai.AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    # プロンプト
    prompt = f"""
あなたは日本の会計に精通したAIです。
以下の証憑テキストから、品目名と金額（税込 or 税抜）をすべて抽出してください。

【証憑テキスト】
{document_text}

【出力形式】
品目名: ●●  
金額: ●●円

- 不明な場合や該当なしの場合は「該当情報なし」と記載してください
    """

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "あなたは日本の会計に精通したAIです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2048
    )

    return response.choices[0].message.content