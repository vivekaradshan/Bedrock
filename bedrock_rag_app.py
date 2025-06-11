import os
import pandas as pd
# Removed ServerlessSpec as it's not needed for just connecting to an existing index
from pinecone import Pinecone, Index
from tqdm import tqdm # Standard tqdm for console execution

import boto3
import json

# --- LangChain Imports ---
# FIX: Changed import to the dedicated langchain-pinecone package
from langchain_pinecone import Pinecone as LangchainPineconeVectorstore # Renamed to avoid confusion if pinecone package is also used
from langchain_community.embeddings import BedrockEmbeddings
from langchain_aws.chat_models import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# --- 1. Pinecone Configuration ---
# IMPORTANT: Replace with your actual Pinecone API Key and Environment
# You can get these from your Pinecone dashboard: app.pinecone.io
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") # Example: "YOUR_ABCDEFGHIJKLMN"
PINECONE_ENVIRONMENT = "us-east-1" # Example: "us-east-1" or "gcp-starter"
INDEX_NAME = "smart-saving-unstruct" # Matches the index name used for upserting
DIMENSION = 1024 # Dimension for 'amazon.titan-embed-text-v2:0'
METRIC = "cosine" # Similarity metric: 'cosine', 'euclidean', or 'dotproduct'
PINECONE_INDEX_HOST = "smart-saving-unstruct-3ithvk0.svc.aped-4627-b74a.pinecone.io" 

# --- 2. AWS Bedrock Configuration ---
# IMPORTANT: Configure your AWS credentials.
# boto3 will automatically look for credentials in environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# or in ~/.aws/credentials. Ensure your AWS region is also configured.
AWS_REGION = "us-east-1" # Or your desired AWS region where Bedrock is available
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
GENERATION_MODEL_ID = 'mistral.mistral-7b-instruct-v0:2' # Using a Mistral model for generation

# --- 2. AWS Bedrock Configuration ---
# IMPORTANT: Configure your AWS credentials.
# boto3 will automatically look for credentials in environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# or in ~/.aws/credentials. Ensure your AWS region is also configured.
AWS_REGION = "us-east-1" # Or your desired AWS region where Bedrock is available
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
GENERATION_MODEL_ID = 'mistral.mistral-7b-instruct-v0:2' # Using a Mistral model for generation

# --- 3. Initialize Pinecone Client (Global Configuration) ---
# This initialization makes the API key and environment available globally
# for LangChain's Pinecone integration to pick up automatically.
try:
    # Initialize Pinecone client with API key and environment (for list_indexes and other ops)
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    print(f"Successfully initialized Pinecone client.")
except Exception as e:
    print(f"Error initializing Pinecone: {e}")
    print("Please ensure your PINECONE_API_KEY and PINECONE_ENVIRONMENT are correct.")
    exit()

# --- 4. Initialize AWS Bedrock Client for LangChain ---
# This client is passed directly to BedrockEmbeddings and ChatBedrock
try:
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=AWS_REGION
    )
    print(f"Successfully initialized AWS Bedrock client in region {AWS_REGION}.")
except Exception as e:
    print(f"Error initializing AWS Bedrock client: {e}")
    print("Please ensure your AWS credentials and region are correctly configured.")
    exit()

# --- 5. Initialize LangChain Components (Pinecone Vectorstore and Embeddings) ---

print(f"Initializing embedding model {EMBEDDING_MODEL_ID} for LangChain...")
# Initialize Bedrock Embeddings for LangChain
embeddings = BedrockEmbeddings(
    model_id=EMBEDDING_MODEL_ID,
    client=bedrock_runtime # Pass the boto3 client directly
)

print(f"Initializing LangChain Pinecone Vectorstore using index '{INDEX_NAME}'...")
# FIX: Use from_existing_index and pass API key/environment directly
# This correctly initializes the Pinecone vector store with the new package
try:
    # Removed api_key and environment from here as they are picked from global client init
    vectorstore = LangchainPineconeVectorstore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings,
        text_key="original_content" # This tells LangChain where to find the original text in your metadata
    )
    print("LangChain Pinecone vector store initialized from existing index.\n")
except Exception as e:
    print(f"Error initializing LangChain Pinecone Vectorstore: {e}")
    print("Please ensure the index exists in Pinecone and your API key/environment are correct for LangChain's connection.")
    exit()

retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) # Configure retriever for top_k=3

# --- 6. Define the RAG Chain with LangChain ---

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
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful banking assistant for JPMorgan Chase.
            Based on the following context, please answer the question accurately and concisely.
            If the answer is not available in the context, state that you cannot answer from the provided information.
            Do not make up information. Focus on providing relevant details from the context.
            """
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

    print("Retrieving relevant documents and generating response using LLM with context (via LangChain)...")
    
    # Invoke the entire RAG chain
    final_response = rag_chain.invoke(user_query) 

    print("--- RAG Answer ---")
    print(final_response)
    print("------------------\n")


# --- Test the RAG application with relevant questions ---
if __name__ == "__main__":
    queries = [
        "What are the key risk factors JPMorgan Chase considers for new credit card applications, especially regarding debt consolidation?",
        "What strategies does J.P. Morgan Asset Management recommend for long-term saving in the US market given economic uncertainty, and what products are mentioned?",
        "Tell me about the challenges faced by the US restaurant supply chain and its impact on small business loans.",
        "What common fraud red flags should JPMC bankers be aware of during credit application review, according to internal policies?"
    ]

    for i, q in enumerate(queries):
        print(f"\nQUERY {i+1}:\n")
        run_rag_application(q)
        print("=" * 70 + "\n")
