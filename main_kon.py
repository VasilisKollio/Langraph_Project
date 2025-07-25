import os
import sqlite3
import glob
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from typing import TypedDict, List, Optional
from IPython.display import Image
from langchain import hub
from langchain_core.documents import Document
from langgraph.graph import START, END, StateGraph
from langchain_ollama import ChatOllama
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader

load_dotenv()

def find_license_match(docs, question: str, exact: bool = True):
    """
    Finds a match for the license plate in documents.
    If `exact` is True, looks for exact matches, otherwise, partial matches are allowed.
    """
    import re

    # Extract plate from question (match license plate pattern)
    match = re.search(r'license\s*plate(?:s)?(?:\s*number)?\s*(?:is|=|:)?\s*([A-Z0-9\-]+)', question, re.I)
    if not match:
        return []

    plate = match.group(1).strip().lower()

    matched = []
    
    for doc in docs:
        doc_content = doc.page_content.lower()

        if exact:
            # Check for an exact match
            if plate == doc_content:
                matched.append(doc)
        else:
            # Allow partial matches (fuzzy matching)
            if plate in doc_content:
                matched.append(doc)
    
    return matched



# --- Load police DB documents ---
conn = sqlite3.connect("police_db.db")
cursor = conn.cursor()

cursor.execute('''
    SELECT owner_name, type, brand, color, license_plate, status, fines
    FROM vehicles
''')

rows = cursor.fetchall()

# Each row --> into a LangChain Document with appropriate metadata
police_docs = []
for row in rows:
    owner_name, vehicle_type, brand, color, license_plate, status, fines = row

    license_plate = license_plate.lower()

    content = (
        f"Owner: {owner_name}\n"
        f"Vehicle Type: {vehicle_type}\n"
        f"Brand: {brand}\n"
        f"Color: {color}\n"
        f"License Plate: {license_plate}\n"
        f"Status: {status}\n"
        f"Fines: {fines}"
    )

    metadata = {
        "source": "police_db.db",
        "type": "police_record",
        "owner_name": owner_name,
        "vehicle_type": vehicle_type,
        "brand": brand,
        "color": color,
        "license_plate": license_plate,
        "status": status,
        "fines": fines
    }


    doc = Document(page_content=content, metadata=metadata)
    police_docs.append(doc)

conn.close()




# --- Load witness reports ---
txt_loader = TextLoader("witness_reports.txt")
txt_docs = txt_loader.load()

for doc in txt_docs:
    doc.metadata["source"] = "witness_reports.txt"
    doc.metadata["type"] = "witness_reports"



# --- Load video reports (.md files) separately ---
folder_path = "video_reports"

# Find all .md files in the folder
md_files = glob.glob(os.path.join(folder_path, "*.md"))

video_report_docs = []
for file_path in md_files:
    loader = TextLoader(file_path)
    docs = loader.load()

    for doc in docs:
        doc.metadata["source"] = os.path.basename(file_path)
        doc.metadata["type"] = "camera_log"
        doc.metadata["video_reports"] = os.path.basename(file_path).split('.')[0]

 # Split and chunk the video report docs
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
for doc in docs:
    try:
        chunks = text_splitter.split_documents([doc])
        video_report_docs.extend(chunks)
    except Exception as e:
        print(f"Error splitting document {doc.metadata.get('source', '')}: {e}")
        video_report_docs.append(doc)


all_docs = txt_docs + police_docs + video_report_docs    

embeddings = OllamaEmbeddings(model="llama3.2",)
vectorstore = InMemoryVectorStore(embedding=embeddings)
vectorstore.add_documents(all_docs)

vectorstore_video = InMemoryVectorStore(embedding=embeddings)
vectorstore_video.add_documents(video_report_docs)

vectorstore_police = InMemoryVectorStore(embedding=embeddings)
vectorstore_police.add_documents(police_docs)

vectorstore_witness = InMemoryVectorStore(embedding=embeddings)
vectorstore_witness.add_documents(txt_docs)

custom_prompt = PromptTemplate.from_template(
    """You are an assistant answering questions on police records, witness reports, and video reports.
    When answering, first decide if the question is specifically about video reports by checking for keywords like ‘video report’ or ‘camera log’. 
    If yes, use only the video report documents to find relevant information. 
    If not, search police records, witness reports, and video reports separately, then combine the relevant information from all three sources to answer. 
    If you don't know the answer, just say that you don't know.

    If any feedback is provided take it under consideration and reply based on how the feedback applies to the question. 
    You answer mainly to the question when context and feedback are None.
    Question: {question} 
    Context: {context}
    Feedback: {feedback} 
    Answer:
"""
)

llm = ChatOllama(model="llama3.2", temperature=0.5)

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str
    feedback: Optional[str]


def retrieve(state: State):
    print("--Retrieving Information--")
    question = state['question'].lower()

    video_keywords = ["video report", "video reports", "camera log", "video_report", "video documents", "video document"]
    witness_keywords = ["witness", "saw", "remembered","witnesses", "witness report", "did anyone see" ]

    # Check if question is about video logs only
    if any(keyword in question for keyword in video_keywords):
        print("Searching only video reports documents...")
        k = len(video_report_docs)
        retrieved_docs = vectorstore_video.similarity_search_with_score(query=question, k=k)
        docs_only = [doc for doc, score in retrieved_docs]
        return {'context': docs_only, 'feedback': None}

    else:
        # Step 1: If the question mentions witness or has vague references, use fuzzy search
        if any(keyword in question for keyword in witness_keywords):
            print("Searching witness reports with partial matches for license plates...")
            # Fuzzy matching on witness reports
            matched_docs = find_license_match(txt_docs, question, exact=False)
            if matched_docs:
                return {'context': matched_docs, 'feedback': None}

        # Step 2: Attempt exact license plate match based on user input or document type
        # Here we consider exact matches in the documents you're specifying (e.g., police_docs, txt_docs, etc.)
        exact_match_docs = find_license_match(police_docs + txt_docs + video_report_docs, question, exact=True)

        if exact_match_docs:
            print("Found exact license plate match.")
            return {'context': exact_match_docs, 'feedback': None}

        # Step 3: Fallback to semantic search if no exact match is found
        print("No exact match found. Falling back to semantic similarity search...")
        
        # Perform semantic search on each document set
        police_k = len(police_docs)
        witness_k = len(txt_docs)
        video_k = len(video_report_docs)

        police_results = vectorstore_police.similarity_search_with_score(query=question, k=police_k)
        witness_results = vectorstore_witness.similarity_search_with_score(query=question, k=witness_k)
        video_results = vectorstore_video.similarity_search_with_score(query=question, k=video_k)

        # Extract the documents from the search results
        police_docs_res = [doc for doc, score in police_results]
        witness_docs_res = [doc for doc, score in witness_results]
        video_docs_res = [doc for doc, score in video_results]

        # Combine all results
        combined_docs = police_docs_res + witness_docs_res + video_docs_res

        return {'context': combined_docs, 'feedback': None}




def generate(state: State):
    print("--Generating Response--")
    #docs_contents =  "\n\n".join([doc.page_content for doc in state["context"]])
    docs_contents =  "\n\n".join([f"Document {i+1}: {doc.page_content}" for i, doc in enumerate(state["context"])])
    #print("----------------DOC CONTENTS----------------")
    #print(docs_contents)
    messages = custom_prompt.invoke({'question': state['question'], 'context': state['context'], 'feedback':state['feedback']})
    response = llm.invoke(messages)
    return {'answer': response}

def feedback_loop(state: State):
    print("--Feedback Loop--")
    # Display the current answer and prompt for feedback
    #print(f"Generated Answer: {state['answer']}")
    feedback = input("Do you approve this answer? (yes/no) or provide suggestions: ").strip()

    # Process feedback
    if feedback.lower() == "yes":
        return {'feedback': 'approved', 'answer': None}
    else:
        # Update the feedback state with user input
        
        return {'feedback': feedback, 'answer': None}


def feedback_check(state: State):
    if state['feedback'] != 'approved':
        state['feedback'] = None
        return "generate"
    
    if state['feedback'] == 'approved':
        return END

builder = StateGraph(State)

builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.add_node("feedback_loop", feedback_loop)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", "feedback_loop")

builder.add_conditional_edges("feedback_loop", feedback_check)

graph = builder.compile()

def interactive():
    print("Interactive System. Type 'exit' to quit.")
    
    while True:
        question = input("\nAsk a question: ")
        if question.lower() == "exit":
            break

        # Create the initial state with the user's question
        state = {'question': question,
                 'context': [],
                 'answer': "",
                 'feedback': None}
        
        # Stream responses from the graph
        for event in graph.stream(state, stream_mode='values'):
            answer = event.get('answer', '')
            if answer:
                print("\nAnswer: ")
                answer.pretty_print()
        
            

        print("\n--- End of response ---")

interactive()