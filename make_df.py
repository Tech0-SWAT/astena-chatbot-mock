from dotenv import load_dotenv

import pandas as pd
import re


# .env 読み込み
load_dotenv()

# LLM出力をDataFrameに変換する関数（外に定義）
def parse_llm_output_to_dataframe(text: str) -> pd.DataFrame:
    """
    LLM出力テキストをDataFrameに変換する関数
    
    対応する形式:
    品目名: [品目名]
    ・金額：[金額]
    ・勘定科目：[勘定科目] 
    ・法定耐用年数：[年数]
    ・根拠：[根拠]
    """
    # より柔軟な正規表現パターン
    # ・・（全角・半角どちらも対応）、：:（全角・半角どちらも対応）
    pattern = re.compile(
        r"品目名[:：]\s*(.*?)\s*"
        r"[・・]\s*金額[:：]\s*(.*?)\s*"
        r"[・・]\s*勘定科目[:：]\s*(.*?)\s*"
        r"[・・]\s*法定耐用年数[:：]\s*(.*?)\s*"
        r"[・・]\s*根拠[:：]\s*(.*?)(?=\n\s*品目名[:：]|$)",
        re.DOTALL | re.MULTILINE
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


