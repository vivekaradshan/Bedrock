import boto3
import json
import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity # No longer needed with FAISS

# --- Install necessary libraries if you haven't already ---
# pip install faiss-cpu  # For CPU version of FAISS
# pip install langchain-community
# pip install langchain-aws
# pip install langchain-core

# --- LangChain and FAISS Imports ---
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from langchain_aws.chat_models import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser


# --- Configuration ---
REGION_NAME = 'us-east-1'
EMBEDDING_MODEL_ID = 'amazon.titan-embed-text-v2:0'
GENERATION_MODEL_ID = 'mistral.mistral-7b-instruct-v0:2' # Using a Mistral model for generation

# --- Initialize Bedrock client (now mainly used by LangChain components) ---
# Ensure your AWS credentials are configured (e.g., via AWS CLI, environment variables, or IAM role)
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=REGION_NAME
)

# --- 1. Ingest/Index Knowledge Base with FAISS ---
# In a real application, this would involve a persistent vector database.
# For this example, FAISS will create an in-memory index.

sample_documents = [
    "Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data.",
    "The Amazon Rainforest is the largest rainforest in the world, known for its incredible biodiversity and role in global climate regulation.",
    "Deep learning is a specialized field of machine learning that uses neural networks with many layers to learn complex patterns.",
    "Photosynthesis is the process used by plants, algae, and cyanobacteria to convert light energy into chemical energy, creating glucose and oxygen.",
    "Supervised learning, unsupervised learning, and reinforcement learning are the three main types of machine learning.",
    "Biodiversity refers to the variety of life on Earth, from genes to ecosystems, and is crucial for healthy planet functions.",
    "Neural networks are computational models inspired by the human brain, forming the backbone of deep learning algorithms.",
    "Climate change refers to long-term shifts in temperatures and weather patterns, largely driven by human activities like burning fossil fuels.",
    "Natural language processing (NLP) is a branch of AI that deals with the interaction between computers and human language."
]

print(f"Initializing embedding model {EMBEDDING_MODEL_ID} for LangChain...")
# Initialize Bedrock Embeddings for LangChain
embeddings = BedrockEmbeddings(
    model_id=EMBEDDING_MODEL_ID,
    client=bedrock_runtime # Pass the boto3 client directly
)

print(f"Creating FAISS vector store from {len(sample_documents)} documents...")
# Create a FAISS vector store from the documents and their embeddings
vectorstore = FAISS.from_texts(sample_documents, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2}) # Configure retriever for top_k=2

print("FAISS vector store created.\n")

# --- 2. Define the RAG Chain with LangChain ---
# This chain defines the flow:
# 1. User query comes in.
# 2. Retriever fetches relevant documents.
# 3. Documents and query are formatted into a prompt.
# 4. Prompt is sent to the LLM.
# 5. LLM's response is parsed.

# Initialize the LLM for generation
llm = ChatBedrock(
    model_id=GENERATION_MODEL_ID,
    client=bedrock_runtime, # Pass the boto3 client directly
    model_kwargs={
        "temperature": 0.5,
        "top_p": 0.9,
        "top_k": 50,
        "max_tokens": 512 # Mistral uses 'max_tokens'
    }
)

# Define the prompt template for the LLM
# This template will dynamically insert the context and question
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful assistant. Based on the following context, please answer the question.
If the answer is not available in the context, state that you cannot answer from the provided information."""
        ),
        ("user", "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"),
    ]
)

# Build the RAG chain using LangChain Expression Language (LCEL)
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt_template
    | llm
    | StrOutputParser()
)

# --- Main RAG Application Flow ---
def run_rag_application(user_query: str):
    print(f"User Query: \"{user_query}\"\n")

    # 1. & 2. Retrieval is now handled by the retriever in the RAG chain
    print("Retrieving relevant documents and generating response using LLM with context (via LangChain)...")
    final_response = rag_chain.invoke(user_query) # Invoke the entire RAG chain

    print("--- RAG Answer ---")
    print(final_response)
    print("------------------\n")


# --- Test the RAG application with some queries ---
if __name__ == "__main__":
    queries = [
        "What is machine learning and its types?",
        "Tell me about the biggest rainforest.",
        "How do plants make food?",
        "What is deep learning?",
        "What causes climate change?",
        "Tell me about neural networks and their connection to deep learning.",
        "What is NLP?",
        "How is the weather today?"
    ]

    for q in queries:
        run_rag_application(q)
        print("-" * 50 + "\n")
