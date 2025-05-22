import streamlit as st
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv

# .envから環境変数を読み込む
load_dotenv()
AZURE_ENDPOINT = os.getenv("DOC_ENDPOINT")
AZURE_KEY = os.getenv("DOC_API_KEY")

st.title("PDFテキスト抽出（Azure Document Intelligence）")

uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Azureで解析中..."):
        # 一時ファイルとして保存
        with open("temp_upload.pdf", "wb") as f:
            f.write(uploaded_file.read())

        # Azure Document Intelligenceクライアント作成
        client = DocumentIntelligenceClient(
            endpoint=AZURE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_KEY)
        )

        # PDFファイルを開いて送信
        with open("temp_upload.pdf", "rb") as doc:
            poller = client.begin_analyze_document(
                "prebuilt-layout",
                doc,
                output_content_format="markdown",
                content_type="application/octet-stream",
            )
            result = poller.result()

        # テキスト抽出
        extracted_text = ""
        for page in result.pages:
            for line in page.lines:
                extracted_text += line.content + "\n"

        # セッションに保存
        st.session_state["extracted_text"] = extracted_text

        st.subheader("抽出されたテキスト")
        st.text_area("テキスト", extracted_text, height=400)

        # レイアウト情報（JSON）も表示
        import json
        # st.subheader("レイアウト情報（JSON）")
        # st.text_area("レイアウト情報", json.dumps(result.as_dict(), ensure_ascii=False, indent=2), height=400)

        # 一時ファイル削除
        os.remove("temp_upload.pdf")

# --- チャットボット機能 ---
st.markdown("---")
st.header("チャットボット")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("メッセージを入力してください", key="chat_input")
if st.button("送信"):
    if user_input:
        # 一定の回答を返す
        bot_reply = "こんにちは！ご質問ありがとうございます。"
        st.session_state.chat_history.append(("ユーザー", user_input))
        st.session_state.chat_history.append(("ボット", bot_reply))

# チャット履歴表示
for speaker, message in st.session_state.chat_history:
    col1, col2 = st.columns([5, 5])
    if speaker == "ユーザー":
        with col2:
            st.markdown(
                f'<div style="text-align: left; background-color: #e6f7ff; padding: 8px; border-radius: 8px; margin-bottom: 4px;"><b>🧑 {speaker}:</b> {message}</div>',
                unsafe_allow_html=True
            )
        with col1:
            st.write("")
    else:
        with col1:
            st.markdown(
                f'<div style="text-align: left; background-color: #f6f6f6; padding: 8px; border-radius: 8px; margin-bottom: 4px;"><b>🤖 {speaker}:</b> {message}</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.write("")
