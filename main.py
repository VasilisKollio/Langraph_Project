import os
import glob
import re
import sqlite3
from langchain_ollama.llms import OllamaLLM 
from langchain_core.prompts import ChatMessagePromptTemplate
from langchain_community.document_loaders import  TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from typing import TypedDict, List, Optional
#from IPython.display import Image
from langchain import hub
from langchain_core.documents import Document
from langgraph.graph import START, END, StateGraph
from langchain_ollama import ChatOllama
from langchain_core.vectorstores import InMemoryVectorStore
from dotenv import load_dotenv
#from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
#from langchain_community.document_loaders.csv_loader import CSVLoader

load_dotenv()

# Police vehicle database

def load_vehicles_from_db(db_path: str) -> list[Document]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT vehicle_id, owner_name, type, brand, color, license_plate, status, fines FROM vehicles")
    rows = cursor.fetchall()
    conn.close()

    documents = []
    for row in rows:
        
        vehicle_id, owner_name, type, brand, color, license_plate, status, fines = row
        content = (f"Vehicle ID: {vehicle_id}\n"
                   f"Name Of Owner: {owner_name}\n"
                   f"Type: {type}\n"
                   f"Brand: {brand}\n"
                   f"Color: {color}\n"
                   f"License Plate: {license_plate}\n"
                   f"Status: {status}\n"
                   f"Fines: {fines}\n")
                

        doc = Document(page_content=content, metadata={
            "source": db_path,
            "type": "police_record",
            "vehicle_id": vehicle_id, 
            "owner_name": owner_name,
            "vehicle_type": type,
            "brand": brand,
            "color": color,
            "license_plate": license_plate,
            "status": status,
            "fines": fines
        })
        documents.append(doc)


    return documents

police_docs = load_vehicles_from_db('police_db.db')

# Witness Reports
txt_loader = TextLoader("witness_reports.txt")
txt_docs = txt_loader.load()

for doc in txt_docs:
    doc.metadata["source"] = "witness_reports.txt"
    doc.metadata["type"] = "witness_reports"

    txt_docs = []

# Load video reports
folder_path = "video_reports"
video_report_docs = []  # Initialize the variable


# Load video reports
folder_path = "video_reports"
video_report_docs = []  # Initialize the variable

if os.path.exists(folder_path):
    print(f"Loading files from {folder_path}...")

    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            filepath = os.path.join(folder_path, filename)
            print(f"Loading: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    doc = Document(page_content=content, metadata={
                        "source": filename,
                        "type": "camera_log",
                        "video_reports": filename.split('.')[0]
                    })
                    video_report_docs.append(doc)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    print(f"Loaded {len(video_report_docs)} video report file(s)")

    if video_report_docs:
        for i, doc in enumerate(video_report_docs):
            print(f"  Document {i+1}: {doc.metadata['source']}")
    else:
        print("No video report `.md` files found in the directory.")

else:
    print(f"Directory '{folder_path}' not found. Skipping video report loading.")



     # Chunk the documents if needed
    """" if video_report_docs:
        print("Starting text splitting...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        
        # Split documents one by one to identify problematic files
        video_chunks = []
        for i, doc in enumerate(video_report_docs):
            print(f"Splitting document {i+1}/{len(video_report_docs)}: {doc.metadata['source']}")
            try:
                chunks = text_splitter.split_documents([doc])
                video_chunks.extend(chunks)
                print(f"  Created {len(chunks)} chunks")
            except Exception as e:
                print(f"  Error splitting {doc.metadata['source']}: {e}")
                # Add the original document without splitting if splitting fails
                video_chunks.append(doc)
        
        # Use chunks for video reports
        video_report_docs = video_chunks
        print(f"Total video report chunks created: {len(video_report_docs)}")
else:
    print(f"Directory {folder_path} not found, skipping video report files")
    """  
# Combine all documents
all_docs = txt_docs + police_docs + video_report_docs


embeddings = OllamaEmbeddings(model="llama3.2",)

vectorstore = InMemoryVectorStore(embedding=embeddings)
vectorstore.add_documents(all_docs)

# Separate vectorstores for each document type 
    
vectorstore_police = InMemoryVectorStore(embedding=embeddings)
if police_docs:
        vectorstore_police.add_documents(police_docs)
    
vectorstore_witness = InMemoryVectorStore(embedding=embeddings)
if txt_docs:
    vectorstore_witness.add_documents(txt_docs)
    
vectorstore_video = InMemoryVectorStore(embedding=embeddings)
if video_report_docs:
     vectorstore_video.add_documents(video_report_docs)
    
print("Vector stores created successfully!")
custom_prompt = PromptTemplate.from_template(
    """  You are an assistant analyzing police records, witness reports, and video footage logs. 
You may be asked to answer any question related to the data provided from these sources. You may analyze and cross-compile multiple files in order to identify matches, relationships, or patterns.

Always cite your sources for every piece of information you use. Do NOT give any general explanations or summaries — only factual matching vehicle data.


Question: {question}
Context: {context}

Answer:""")


model = OllamaLLM(model="llama3.2", temperature=0.5)

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str
    feedback: Optional[str]


def retrieve(state: State):
    print("--Retrieving Information--")
    question = state['question'].lower()

    # Match video_report files by name
    file_matches = re.findall(r"video_report\d+\.md", question)

    sources = {
        "video": any(keyword in question for keyword in ["video", "camera", "video_report"]),
        "witness": any(keyword in question for keyword in ["witness", "testimony"]),
        "police": any(keyword in question for keyword in ["police", "fine", "status", "stolen", "registration"])
    }

    # Start with an empty doc list
    docs = []

    # Filter by filenames if mentioned
    if file_matches:
        print(f"Filtering by specific files: {file_matches}")
        docs.extend([doc for doc in video_report_docs if doc.metadata.get("source", "") in file_matches])
    else:
        if sources["video"]:
            docs.extend([doc for doc, _ in vectorstore_video.similarity_search_with_score(question, k=10)])
        if sources["witness"]:
            docs.extend([doc for doc, _ in vectorstore_witness.similarity_search_with_score(question, k=10)])
        if sources["police"]:
            docs.extend([doc for doc, _ in vectorstore_police.similarity_search_with_score(question, k=10)])

    # If no specific source is triggered, search everything
    if not any(sources.values()) and not file_matches:
        print("No specific source found, searching across all.")
        docs.extend([doc for doc, _ in vectorstore_video.similarity_search_with_score(question, k=5)])
        docs.extend([doc for doc, _ in vectorstore_police.similarity_search_with_score(question, k=5)])
        docs.extend([doc for doc, _ in vectorstore_witness.similarity_search_with_score(question, k=5)])

    return {"context": docs, "feedback": None}


def generate(state: State):
    print("--Generating Response--")
    
    # FIXED: Use actual source filenames instead of generic "Document X"
    docs_contents = []
    for i, doc in enumerate(state["context"]):
      
        # Extract source filename from metadata
        source = doc.metadata.get('source', f'Unknown_Document_{i+1}')
     
        # Format with actual source name
        doc_content = f"Source: {source}\nContent: {doc.page_content}"
        docs_contents.append(doc_content)
    0
    # Join all documents with clear separators
    formatted_context = "\n\n" + "="*50 + "\n\n".join(docs_contents)
    
    # FIXED: Properly format the prompt invocation
    prompt_input = {
        'question': state['question'], 
        'context': formatted_context, 
        'feedback': state.get('feedback', 'None')
    }
    
    messages = custom_prompt.format(**prompt_input)
    response = model.invoke(messages)
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
    print("\nInteractive System. Type 'exit' to quit.")
    
    while True:
        question = input("\nAsk a question: ")
        if question.lower() == "exit":
            break

        # Create the initial state with the user's question
        state = {'question': question}
        
        # Stream responses from the graph
        for event in graph.stream(state, stream_mode='values'):
            answer = event.get('answer', '')
            if answer:
                print("\nAnswer: ")
                print(answer) 
                #answer.pretty_print()
        
            

        print("\n--- End of response ---")
        
if __name__ == "__main__":

    interactive()