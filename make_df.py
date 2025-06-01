from dotenv import load_dotenv

import pandas as pd
import re


# .env 読み込み
load_dotenv()

# LLM出力をDataFrameに変換する関数（外に定義）
def parse_llm_output_to_dataframe(text: str) -> pd.DataFrame:
    pattern = re.compile(
        r"品目名[:：]\s*(.*?)\s*"
        r"・金額[:：]\s*([^\n]*)\s*"
        r"・勘定科目[:：]\s*([^\n]*)\s*"
        r"・法定耐用年数[:：]\s*([^\n]*)\s*"
        r"・根拠[:：]\s*(.*?)\n(?=\s*品目名|$)",  # 次の品目名または終端まで
        re.DOTALL
    )
    rows = []
    for match in pattern.finditer(text):
        rows.append({
            "品目名": match.group(1).strip(),
            "金額": match.group(2).strip(),
            "勘定科目": match.group(3).strip(),
            "法定耐用年数": match.group(4).strip(),
            "根拠": match.group(5).strip(),
        })
    return pd.DataFrame(rows)

def parse_extracted_items_to_dataframe(text: str) -> pd.DataFrame:
    pattern = re.compile(r"品目名:\s*(.*?)\s+金額:\s*([\d,]+円|該当情報なし)")
    rows = []

    for match in pattern.finditer(text):
        item = match.group(1).strip()
        amount = match.group(2).strip()
        rows.append({"品目名": item, "金額": amount})

    return pd.DataFrame(rows)


