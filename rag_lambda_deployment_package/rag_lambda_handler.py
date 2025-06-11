import os
import json
import boto3
from pinecone import Pinecone
from langchain_pinecone import Pinecone as LangchainPineconeVectorstore
from langchain_community.embeddings import BedrockEmbeddings
from langchain_aws.chat_models import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- Configuration (will be set via Environment Variables in Lambda) ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("INDEX_NAME")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST") # Ensure this is set
AWS_REGION = os.getenv("AWS_REGION_1")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
# UPDATED: Changed default GENERATION_MODEL_ID to Claude 3 Sonnet
GENERATION_MODEL_ID = os.getenv("GENERATION_MODEL_ID", 'anthropic.claude-3-sonnet-20240229-v1:0')

# Global variables for initialized clients and chain
pc_client = None
bedrock_runtime_client = None
rag_chain = None
embeddings_instance = None
vectorstore_instance = None
llm_instance = None

def initialize_components():
    global pc_client, bedrock_runtime_client, rag_chain, embeddings_instance, vectorstore_instance, llm_instance

    # Initialize Pinecone client once
    if pc_client is None:
        if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
            raise ValueError("PINECONE_API_KEY or PINECONE_ENVIRONMENT not set.")
        try:
            pc_client = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            print("Successfully initialized Pinecone client.")
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise

    # Initialize Bedrock runtime client once
    if bedrock_runtime_client is None:
        if not AWS_REGION:
            raise ValueError("AWS_REGION not set.")
        try:
            bedrock_runtime_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=AWS_REGION
            )
            print(f"Successfully initialized AWS Bedrock client in region {AWS_REGION}.")
        except Exception as e:
            print(f"Error initializing AWS Bedrock client: {e}")
            raise

    # Initialize LangChain Embeddings once
    if embeddings_instance is None:
        print(f"Initializing embedding model {EMBEDDING_MODEL_ID} for LangChain...")
        embeddings_instance = BedrockEmbeddings(
            model_id=EMBEDDING_MODEL_ID,
            client=bedrock_runtime_client
        )

    # Initialize LangChain Pinecone Vectorstore once
    if vectorstore_instance is None:
        if not INDEX_NAME:
            raise ValueError("INDEX_NAME not set.")
        print(f"Initializing LangChain Pinecone Vectorstore using index '{INDEX_NAME}'...")
        try:
            vectorstore_instance = LangchainPineconeVectorstore.from_existing_index(
                index_name=INDEX_NAME,
                embedding=embeddings_instance,
                text_key="original_content" # Ensure this matches your Pinecone schema
            )
            print("LangChain Pinecone vector store initialized from existing index.")
        except Exception as e:
            print(f"Error initializing LangChain Pinecone Vectorstore: {e}")
            raise

    # Initialize LLM for generation once
    if llm_instance is None:
        print(f"Initializing generation model {GENERATION_MODEL_ID} for LangChain...")
        llm_instance = ChatBedrock(
            model_id=GENERATION_MODEL_ID,
            client=bedrock_runtime_client,
            # Claude 3 Sonnet often performs well with default parameters, or you can tune:
            model_kwargs={
                "temperature": 0.5,
                "top_p": 0.9,
                "max_tokens": 1024 # Increased max_tokens for potentially longer Claude responses
            }
        )

    # Build the RAG chain once
    if rag_chain is None:
        retriever = vectorstore_instance.as_retriever(search_kwargs={"k": 3})

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
        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt_template
            | llm_instance
            | StrOutputParser()
        )
        print("RAG chain initialized.")

def lambda_handler(event, context):
    try:
        # Initialize components on the first invocation (or if they are reset)
        initialize_components()

        print(f"Received event for RAG: {json.dumps(event)}")
        
        # Extract the query from the orchestrator agent's tool call format
        user_query = ""
        if 'requestBody' in event and 'content' in event['requestBody'] and 'application/json' in event['requestBody']['content']:
            body_str = event['requestBody']['content']['application/json']['properties']['query']
            try:
                body_data = json.loads(body_str) # The query might be a JSON string itself from the agent
                user_query = body_data.get('query', body_str)
            except json.JSONDecodeError:
                user_query = body_str # It's a plain string
        elif 'inputText' in event: # For direct Bedrock Agent invoke (e.g., from InvokeLambda)
            user_query = event['inputText']
        elif 'body' in event: # For direct Lambda invocation testing
            body = json.loads(event['body'])
            user_query = body.get('query', '')
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('No input query found in expected formats.')
            }

        if not user_query:
            return {
                'statusCode': 400,
                'body': json.dumps('Input query is empty.')
            }

        print(f"Processing RAG query: \"{user_query}\"")
        final_response = rag_chain.invoke(user_query)
        print(f"RAG Response: {final_response}")

        # Bedrock Agents expect a specific format for the response from action groups
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': final_response
            })
        }
    except Exception as e:
        print(f"Error in RAG Lambda handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal Server Error in RAG: {str(e)}')
        }