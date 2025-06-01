import pandas as pd
import os
from dotenv import load_dotenv
from openai import OpenAI  # ← 新しいクライアントのインポート
from make_df import parse_llm_output_to_dataframe   
import openai
load_dotenv()

def refine_rag_response_from_df(df: pd.DataFrame, history_text: str = "") -> str:
    # DataFrame を整形済み文字列に変換
    items_text = ""
    for _, row in df.iterrows():
        items_text += f"""品目名: {row["品目名"]}
        ・金額: {row["金額"]}
        ・勘定科目: {row["勘定科目"]}
        ・法定耐用年数: {row["法定耐用年数"]}
        ・根拠: {row["根拠"]}
    """
    print(items_text)

    prompt = f"""
        あなたは日本の会計に精通した経理アシスタントAIです。

        以下は、ユーザーが編集・確認を行った固定資産の一覧です。
        この内容をもとに、固定資産台帳登録用として整合性のある最終整理結果を出力してください。

        - 同じ勘定科目・法定耐用年数に該当する品目は、可能であれば統合し、金額は合算してください。
        - 品目名は代表名または統合表現で問題ありません。
        - 金額は税抜表示とし、「○円」の形式で表示してください。
        - 出力形式は下記の通り。

        【編集後データ】
        {items_text}

        {history_text}

        【出力形式】
        以下の形式で出力してください：

        品目名: （例: ノートPC）  
        ・金額：150,000円  
        ・勘定科目：備品  
        ・法定耐用年数：4年  
        ・根拠：〇〇〇〇
        """

    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    # 新しいクライアントで初期化
    client = openai.AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
    )

    # chat.completions.create に変更
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "あなたは会計処理の専門AIです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2048
    )
    print(response)

    response_text = response.choices[0].message.content
    # 表形式に変換
    df = parse_llm_output_to_dataframe(response_text)
    # 表示
    print("\n=== 表形式に整形（台帳登録用）===")
    print(df)

    return response_text