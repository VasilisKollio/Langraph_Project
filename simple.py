from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
import os
load_dotenv()


class DocumentManager:
    def __init__(self, directory_path, glob_pattern="./*.md"):
        self.directory_path = directory_path
        self.glob_pattern = glob_pattern
        self.documents = []
        self.all_sections = []
    
    def load_documents(self):
        loader = DirectoryLoader(self.directory_path, glob=self.glob_pattern, show_progress=True, loader_cls=UnstructuredMarkdownLoader)
        self.documents = loader.load()

def split_documents(self):
    headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3"), ("####", "Header 4")]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    for doc in self.documents:
        sections = text_splitter.split_text(doc.page_content)
        self.all_sections.extend(sections)

class EmbeddingManager:
    def __init__(self, all_sections, persist_directory='db'):
        self.all_sections = all_sections
        self.persist_directory = persist_directory
        self.vectordb = None
        
    def create_and_persist_embeddings(self):
        embedding = OllamaEmbeddings()
        self.vectordb = Chroma.from_documents(documents=self.all_sections, embedding=embedding, persist_directory=self.persist_directory)
        self.vectordb.persist()
