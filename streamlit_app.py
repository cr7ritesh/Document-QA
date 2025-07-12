import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings
from langchain.chat_models import init_chat_model
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv

load_dotenv()

st.title("PDF Question Answering with Gemini & LangChain")

# --- API Key Input ---
COHERE_API_KEY = os.environ["COHERE_API_KEY"]

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

@st.cache_resource(show_spinner="Processing PDF...")
def process_pdf(file):
    # Read PDF
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    # Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.create_documents([text])
    # Embeddings & Vector Store
    embeddings = CohereEmbeddings(model="embed-english-v3.0")
    vectordb = Chroma.from_documents(docs, embeddings)
    return vectordb

if uploaded_file and COHERE_API_KEY:
    vectordb = process_pdf(uploaded_file)
    retriever = vectordb.as_retriever()
    llm = init_chat_model("command-r-plus", model_provider="cohere")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
    )

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        st.chat_message(message['role']).markdown(message["content"])

    prompt = st.text_input("Enter your question:")

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Retrieving answer..."):
            response = qa_chain.invoke({"query": prompt})["result"]
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
elif not COHERE_API_KEY:
    st.info("Please enter your COHERE API key.")
elif not uploaded_file:
    st.info("Please upload a PDF file.")