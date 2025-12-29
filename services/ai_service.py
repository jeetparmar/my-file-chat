import streamlit as st
from openai import OpenAI as OpenAIClient
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.text_processor import TextProcessor
from config.settings import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    OPENAI_API_KEY,
    SUMMARIZER_TEMPERATURE,
    SUMMARY_MODEL,
)


class AIService:

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        self.vectorstore = None
        self.qa_chain = None

    def build_vector_store(self, text: str):
        try:
            chunks = self.text_splitter.split_text(text)
            self.vectorstore = FAISS.from_texts(chunks, OpenAIEmbeddings())
        except Exception as e:
            st.error(f"Vector store creation failed: {str(e)}", icon="🚨")
            self.vectorstore = None

    def create_qa_chain(self):
        """Create RetrievalQA chain from vector store"""
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized")

        try:
            llm = OpenAI(temperature=0)
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            )
        except Exception as e:
            st.error(f"QA chain creation failed: {str(e)}", icon="🚨")
            self.qa_chain = None

    def query(self, question: str) -> str:
        if self.qa_chain is None:
            self.create_qa_chain()
        try:
            response = self.qa_chain.run(question)
            return TextProcessor.clean_text(response)
        except Exception as e:
            st.error(f"Query failed: {str(e)}", icon="🚨")
            return ""

    @staticmethod
    def generate_summary(text: str) -> str:
        if not TextProcessor.validate_token_limit(text, model_name=SUMMARY_MODEL):
            return "error"

        try:
            client = OpenAIClient(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=SUMMARY_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful research assistant that creates concise summaries.",
                    },
                    {"role": "user", "content": f"Summarize this text:\n\n{text}"},
                ],
                temperature=SUMMARIZER_TEMPERATURE,
                max_tokens=500,
            )

            summary = response.choices[0].message.content
            return TextProcessor.format_text(summary)
        except Exception as e:
            st.error(f"Summary generation failed: {str(e)}", icon="🚨")
            return ""
