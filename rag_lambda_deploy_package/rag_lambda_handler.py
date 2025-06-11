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
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")
# UPDATED: AWS_REGION is now AWS_REGION_1
AWS_REGION_1 = os.getenv("AWS_REGION_1")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
# UPDATED: GENERATION_MODEL_ID now only from os.getenv, no default hardcoded value
GENERATION_MODEL_ID = os.getenv("GENERATION_MODEL_ID")
# OPTIONAL: If you provision throughput, you might need an environment variable for the ARN
# PROVISIONED_THROUGHPUT_ARN = os.getenv("PROVISIONED_THROUGHPUT_ARN")

# Global variables for initialized clients and chain
pc_client = None
bedrock_runtime_client = None
rag_chain = None
embeddings_instance = None
vectorstore_instance = None
llm_instance = None

def initialize_components():
    global pc_client, bedrock_runtime_client, rag_chain, embeddings_instance, vectorstore_instance, llm_instance

    if pc_client is None:
        if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
            raise ValueError("PINECONE_API_KEY or PINECONE_ENVIRONMENT not set.")
        try:
            pc_client = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            print("Successfully initialized Pinecone client.")
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise

    if bedrock_runtime_client is None:
        # UPDATED: Use AWS_REGION_1
        if not AWS_REGION_1:
            raise ValueError("AWS_REGION_1 not set.")
        try:
            bedrock_runtime_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=AWS_REGION_1
            )
            print(f"Successfully initialized AWS Bedrock client in region {AWS_REGION_1}.")
        except Exception as e:
            print(f"Error initializing AWS Bedrock client: {e}")
            raise

    if embeddings_instance is None:
        print(f"Initializing embedding model {EMBEDDING_MODEL_ID} for LangChain...")
        embeddings_instance = BedrockEmbeddings(
            model_id=EMBEDDING_MODEL_ID,
            client=bedrock_runtime_client
        )

    if vectorstore_instance is None:
        if not INDEX_NAME:
            raise ValueError("INDEX_NAME not set.")
        print(f"Initializing LangChain Pinecone Vectorstore using index '{INDEX_NAME}'...")
        try:
            vectorstore_instance = LangchainPineconeVectorstore.from_existing_index(
                index_name=INDEX_NAME,
                embedding=embeddings_instance,
                text_key="original_content"
            )
            print("LangChain Pinecone vector store initialized from existing index.")
        except Exception as e:
            print(f"Error initializing LangChain Pinecone Vectorstore: {e}")
            raise

    if llm_instance is None:
        if not GENERATION_MODEL_ID:
            raise ValueError("GENERATION_MODEL_ID not set as an environment variable.")

        print(f"Initializing generation model {GENERATION_MODEL_ID} for LangChain...")

        # UPDATED: Use the provided Claude template for model_kwargs
        # Note: LangChain's ChatBedrock handles the 'messages' array directly,
        # so we pass the other parameters as model_kwargs.
        claude_model_kwargs = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200, # Max tokens to generate
            "top_k": 250,      # Top-k sampling
            "stop_sequences": [], # No specific stop sequences needed usually
            "temperature": 1,
            "top_p": 0.999
        }

        # If using provisioned throughput for Claude 3.5 Sonnet, you'd add endpoint_name
        # if GENERATION_MODEL_ID == "anthropic.claude-3-5-sonnet-20241022-v2:0" and PROVISIONED_THROUGHPUT_ARN:
        #     llm_instance = ChatBedrock(
        #         model_id=GENERATION_MODEL_ID, # Still specify model ID
        #         client=bedrock_runtime_client,
        #         model_kwargs=claude_model_kwargs,
        #         endpoint_name=PROVISIONED_THROUGHPUT_ARN # Pass the provisioned throughput ARN here
        #     )
        # else:
        llm_instance = ChatBedrock(
            model_id=GENERATION_MODEL_ID,
            client=bedrock_runtime_client,
            model_kwargs=claude_model_kwargs
        )

    if rag_chain is None:
        retriever = vectorstore_instance.as_retriever(search_kwargs={"k": 3})

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a helpful Senior Risk banking assistant for JPMorgan Chase.
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
        initialize_components()

        print(f"Received event for RAG: {json.dumps(event)}")
        
        user_query = ""
        if 'requestBody' in event and 'content' in event['requestBody'] and 'application/json' in event['requestBody']['content']:
            body_str = event['requestBody']['content']['application/json']['properties']['query']
            try:
                body_data = json.loads(body_str)
                user_query = body_data.get('query', body_str)
            except json.JSONDecodeError:
                user_query = body_str
        elif 'inputText' in event:
            user_query = event['inputText']
        elif 'body' in event:
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