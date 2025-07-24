import asyncio
import aiohttp
from prompt_toolkit import PromptSession
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

async def download_markdown(url):
    print(f" Downloading markdown from: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch file: {resp.status}")
            return await resp.text()

async def main():
    print(" Starting Markdown Documentation Assistant...\n")

    session = PromptSession()
    url = await session.prompt_async("Enter the URL to your markdown file: ")
    print(f" Received markdown URL: {url}")

    print(" Downloading markdown...")
    markdown = await download_markdown(url)

    print(" Splitting markdown into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    docs = [Document(page_content=markdown, metadata={"source": url})]
    chunks = splitter.split_documents(docs)
    print(f" Created {len(chunks)} chunks")

    print(" Embedding and indexing...")
    embeddings = OllamaEmbeddings(
        model="granite3.3:2b",
        client=None,  # Use default client
        temperature=0.1,
    )

    vector_store = await InMemoryVectorStore.afrom_documents(chunks, embeddings)
    print(" Vector store created.")

    print(" Setting up LLM and prompt...")
    llm = ChatOllama(
        model="granite3.3:2b",
        temperature=0.1,
        client=None,  # Use default client
        
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert documentation assistant. Use the following context to answer questions about the documentation accurately and helpfully.
Context: {context}
Guidelines:
- Provide accurate information based only on the provided context
- Include relevant code examples when available
- Mention the source document when possible
- If information is not in the context, clearly state that"""),
        ("human", "{question}")
    ])

    print('\n Ready! Ask your questions about the document. Type "exit" to quit.')
    while True:
        try:
            question = await session.prompt_async("> ")
            if question.lower() in ["exit", "quit"]:
                print("👋 Exiting assistant. Goodbye!")
                break

            retriever = vector_store.as_retriever(k=5)
            relevant_docs = await retriever.aget_relevant_documents(question)
            context = "\n\n".join(doc.page_content for doc in relevant_docs)

            prompt = await prompt_template.ainvoke({
                "context": context,
                "question": question
            })

            response = await llm.ainvoke(prompt)
            print(f"\n Answer:\n{response.content}\n")

        except Exception as e:
            print(f" Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
