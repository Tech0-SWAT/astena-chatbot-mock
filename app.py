import streamlit as st
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv
from chat_response import generate_response
from asset_judge import asset_judge
from asset_extract_items import asset_extract_items


# .envから環境変数を読み込む
load_dotenv()
AZURE_ENDPOINT = os.getenv("DOC_ENDPOINT")
AZURE_KEY = os.getenv("DOC_API_KEY")

st.title("固定資産判定アプリ")

# --- docs_for_indexのファイル一覧表示 ---
docs_dir = "document/docs_for_index"
if not os.path.exists(docs_dir):
    os.makedirs(docs_dir, exist_ok=True)
docs_files = os.listdir(docs_dir)
# --- サイドバーにファイル一覧表示 ---
st.sidebar.subheader("docs_for_index内のファイル一覧")
if docs_files:
    for f in docs_files:
        st.sidebar.write(f"- {f}")
else:
    st.sidebar.write("ファイルがありません。")

# --- インデックス再作成用PDFアップローダ（サイドバーへ移動） ---
st.sidebar.subheader("インデックス再作成用PDFアップロード")
uploaded_index_file = st.sidebar.file_uploader("インデックス用PDFをアップロード（docs_for_indexに保存）", type=["pdf"], key="index_pdf")
if uploaded_index_file is not None:
    save_path = os.path.join(docs_dir, uploaded_index_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_index_file.read())
    st.sidebar.success(f"{uploaded_index_file.name} を docs_for_index に保存しました。")

# --- インデックス再作成ボタン（サイドバーへ移動） ---
import subprocess, sys
st.sidebar.markdown("---")
if st.sidebar.button("インデックス再作成"):
    with st.spinner("FAISSインデックスを再作成中..."):
        try:
            result = subprocess.run(
                # sys.executable は「いま動いている仮想環境の Python 」
                [sys.executable, "faiss_index_builder.py"],
                capture_output=True, text=True, check=True
            )
            st.sidebar.success("インデックス再作成が完了しました。")
            st.sidebar.text_area("出力ログ", result.stdout + "\n" + result.stderr, height=200)
        except subprocess.CalledProcessError as e:
            st.sidebar.error("インデックス再作成中にエラーが発生しました。")
            st.sidebar.text_area("エラーログ", e.stdout + "\n" + e.stderr, height=200)

# --- 質問用PDFアップローダ ---
st.subheader("証憑PDFアップロード")
uploaded_qa_file = st.file_uploader("固定資産判定を行いたい証憑のPDFをアップロードしてください", type=["pdf"], key="qa_pdf")

# PDFアップロード時のみ解析し、セッションに保存
if uploaded_qa_file is not None and "qa_file_name" not in st.session_state:
    try:
        with st.spinner("PDFを解析中..."):
            # 一時ファイルとして保存
            with open("temp_upload.pdf", "wb") as f:
                f.write(uploaded_qa_file.read())

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
            st.session_state["qa_file_name"] = uploaded_qa_file.name

            # LLM処理（自動実行）
            with st.spinner("LLMで品目と金額を抽出中..."):
                extracted_result = asset_extract_items(extracted_text)
                st.session_state["extracted_items"] = extracted_result

            # 一時ファイル削除
            os.remove("temp_upload.pdf")
    except Exception as e:
        import traceback
        error_message = "PDF解析中にエラーが発生しました。\n" + traceback.format_exc()
        st.error(error_message)
if "extracted_items" in st.session_state:
    st.subheader("LLMによる品目・金額抽出結果")
    st.markdown(st.session_state["extracted_items"])

if "extracted_text" in st.session_state:
    if st.button("固定資産を判定する"):
        with st.spinner("固定資産の情報を判定中．．．"):
            rag_response = asset_judge(
                user_chat="以下のテキストから品目ごとに金額、勘定科目、法定耐用年数、根拠を抽出してください。",
                document_text = st.session_state["extracted_text"]
            )
            st.session_state["rag_response"] = rag_response

if "rag_response" in st.session_state:
    st.subheader("固定資産判定結果")
    st.markdown(st.session_state["rag_response"])

# --- チャットボット機能 ---
st.markdown("---")
st.header("チャットボット")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("不明点あれば質問を入力してください", key="chat_input")
if st.button("送信"):
    if user_input:
        # 会話履歴（old_chat）をテキスト化
        old_chat = ""
        for speaker, message in st.session_state.chat_history:
            prefix = "ユーザー: " if speaker == "ユーザー" else "ボット: "
            old_chat += f"{prefix}{message}\n"
        # RAGの返答を取得
        document_text = st.session_state.get("rag_response", "")
        # AI応答を生成
        with st.spinner("AIが応答を生成中..."):
            bot_reply = generate_response(user_input, old_chat=old_chat, document_text=document_text)
        st.session_state.chat_history.append(("ユーザー", user_input))
        st.session_state.chat_history.append(("ボット", bot_reply))

# チャット履歴表示（最大幅で表示）
for speaker, message in st.session_state.chat_history:
    with st.container():
        if speaker == "ユーザー":
            st.markdown(
                f'<div style="text-align: left; background-color: #e6f7ff; padding: 8px; border-radius: 8px; margin-bottom: 4px; width:100%;"><b>🧑 {speaker}:</b> {message}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="text-align: left; background-color: #f6f6f6; padding: 8px; border-radius: 8px; margin-bottom: 4px; width:100%;"><b>🤖 {speaker}:</b> {message}</div>',
                unsafe_allow_html=True
            )
