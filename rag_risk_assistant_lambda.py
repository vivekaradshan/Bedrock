import os
import json
import boto3
from pinecone import Pinecone
from langchain_pinecone import Pinecone as LangchainPineconeVectorstore
from langchain_community.embeddings import BedrockEmbeddings
from langchain_aws.chat_models import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import re
# Removed: from dotenv import load_dotenv (environment variables will be set in Lambda)
from langchain_core.documents import Document
from typing import Union, Tuple

# --- Configuration (from Environment Variables) ---
# These variables will be set directly in the AWS Lambda environment.
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("INDEX_NAME")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")
AWS_REGION_1 = os.getenv("AWS_REGION_1")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
GENERATION_MODEL_ID = os.getenv("GENERATION_MODEL_ID")

# --- Neo4j Configuration ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Global variables for initialized clients and chain
# These will be initialized once per Lambda execution environment (warm start)
pc_client = None
bedrock_runtime_client = None
rag_chain = None
embeddings_instance = None
vectorstore_instance = None
llm_instance = None
neo4j_driver = None

def initialize_components():
    """
    Initializes all necessary clients and LangChain components.
    This function should be called only once per Lambda container lifecycle.
    """
    global pc_client, bedrock_runtime_client, rag_chain, embeddings_instance, vectorstore_instance, llm_instance, neo4j_driver

    # --- Initialize Pinecone Client ---
    if pc_client is None:
        if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
            raise ValueError("PINECONE_API_KEY or PINECONE_ENVIRONMENT not set as Lambda environment variables.")
        try:
            pc_client = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            print("Successfully initialized Pinecone client.")
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise

    # --- Initialize AWS Bedrock Runtime Client ---
    if bedrock_runtime_client is None:
        if not AWS_REGION_1:
            raise ValueError("AWS_REGION_1 not set as a Lambda environment variable.")
        try:
            bedrock_runtime_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=AWS_REGION_1
            )
            print(f"Successfully initialized AWS Bedrock client in region {AWS_REGION_1}.")
        except Exception as e:
            print(f"Error initializing AWS Bedrock client: {e}")
            raise

    # --- Initialize LangChain Embeddings ---
    if embeddings_instance is None:
        print(f"Initializing embedding model {EMBEDDING_MODEL_ID} for LangChain...")
        embeddings_instance = BedrockEmbeddings(
            model_id=EMBEDDING_MODEL_ID,
            client=bedrock_runtime_client
        )

    # --- Initialize LangChain Pinecone Vectorstore ---
    if vectorstore_instance is None:
        if not INDEX_NAME:
            raise ValueError("INDEX_NAME not set as a Lambda environment variable.")
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

    # --- Initialize Neo4j Driver ---
    if neo4j_driver is None:
        if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
            print("Neo4j credentials not fully set. Skipping Neo4j driver initialization.")
            # Do not raise error, allow RAG to proceed without KG if credentials are not set
        else:
            try:
                neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
                neo4j_driver.verify_connectivity() # Test connection
                print("Successfully initialized Neo4j driver.")
            except ServiceUnavailable as e:
                print(f"Neo4j Service Unavailable: {e}. Check Neo4j instance or URI.")
                neo4j_driver = None # Set to None to prevent further errors
            except Exception as e:
                print(f"Error initializing Neo4j driver: {e}")
                neo4j_driver = None # Set to None

    # --- Initialize LLM for generation ---
    if llm_instance is None:
        if not GENERATION_MODEL_ID:
            raise ValueError("GENERATION_MODEL_ID not set as an environment variable.")

        print(f"Initializing generation model {GENERATION_MODEL_ID} for LangChain...")
        claude_model_kwargs = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "top_k": 250,
            "stop_sequences": [],
            "temperature": 1,
            "top_p": 0.999
        }
        llm_instance = ChatBedrock(
            model_id=GENERATION_MODEL_ID,
            client=bedrock_runtime_client,
            model_kwargs=claude_model_kwargs
        )

    # --- Build the RAG chain ---
    if rag_chain is None:
        retriever = vectorstore_instance.as_retriever(search_kwargs={"k": 3})
        print("Retriever initialized with top-k search set to 3.")

        def format_docs(docs: list[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a helpful senior risk analyst for JPMorgan Chase.
                    Based on the following context and the detailed user profile information (if provided),
                    please answer the question accurately and concisely.

                    Pay close attention to any user-specific identifiers (like user ID) and any 'Unstructured Data'
                    notes in the user profile, as these often contain critical insights.

                    If the answer is not available in the provided information, state that you cannot answer.
                    Summarize her profile information and any relevant context to provide a comprehensive answer.
                    Do not make up information. Focus on providing relevant details from the context and user profile.

                    User Profile from Knowledge Graph:
                    {user_profile_info}
                    """
                ),
                ("user", "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"),
            ]
        )
        print("Prompt template initialized.")
        rag_chain = (
            RunnablePassthrough.assign(
                context=lambda x: retriever.invoke(x["question"])
            )
            | RunnablePassthrough.assign(
                context=lambda x: format_docs(x["context"])
            )
            | prompt_template
            | llm_instance
            | StrOutputParser()
        )
        print("RAG chain initialized.")


# Helper to convert Neo4j Integer (internal representation) to Python int
def convert_neo4j_int(neo4j_int):
    # Neo4j's internal Integer type
    if isinstance(neo4j_int, (int, float)):
        return neo4j_int
    if hasattr(neo4j_int, 'low') and hasattr(neo4j_int, 'high'):
        # Reconstruct the 64-bit integer
        return neo4j_int.high * (2**32) + neo4j_int.low
    return neo4j_int

# Helper to format properties into a table row
def format_property(key, value, max_key_len, max_value_len):
    formatted_key = key.replace('_', ' ').title()
    if isinstance(value, list):
        formatted_value = ", ".join(map(str, value))
    else:
        formatted_value = str(convert_neo4j_int(value))
    return f"| {formatted_key:<{max_key_len}} | {formatted_value:<{max_value_len}} |"

# --- Neo4j Query Function (Modified for Table Output and Node.items fix) ---
def query_neo4j_profile(user_id: str = None, user_name: str = None) -> str:
    """
    Queries Neo4j for a user profile based on ID or Name,
    capturing maximum information about the customer, relationships,
    and connected nodes. Returns a comprehensive formatted string in a table format.
    """
    if not neo4j_driver:
        print("Neo4j driver not initialized, cannot query knowledge graph.")
        return "No user profile available from knowledge graph (Neo4j not connected or credentials missing)."

    query_filter = ""
    if user_id:
        query_filter = f"{{id: '{user_id}'}}"
    elif user_name:
        query_filter = f"{{name: '{user_name}'}}"
    else:
        return "No user ID or name provided for Knowledge Graph query."

    query = f"MATCH (c:Customer {query_filter})-[r]-(connectedNode) RETURN c, r, connectedNode"

    profile_sections = []

    try:
        with neo4j_driver.session() as session:
            result = session.run(query)
            records = list(result)

            if not records:
                return f"No profile found in Knowledge Graph for identifier: {user_id if user_id else user_name}."

            # Process customer details once from the first record
            customer = records[0]["c"]
            customer_props = {k: v for k, v in customer.items()}
            customer_props['Labels'] = ", ".join(customer.labels)

            max_key_len = max(len(str(k).replace('_', ' ').title()) for k in customer_props.keys()) if customer_props else 0
            max_value_len = max(len(str(convert_neo4j_int(v))) for v in customer_props.values()) if customer_props else 0

            customer_section_lines = ["--- Customer Profile ---"]
            header = f"| {'Property':<{max_key_len}} | {'Value':<{max_value_len}} |"
            separator = f"| {'-' * max_key_len} | {'-' * max_value_len} |"
            customer_section_lines.extend([header, separator])

            for prop_name, prop_value in customer_props.items():
                customer_section_lines.append(format_property(prop_name, prop_value, max_key_len, max_value_len))

            profile_sections.append("\n".join(customer_section_lines))

            # Now iterate through all records to get connected nodes and relationships
            for record in records:
                relationship = record["r"]
                connected_node = record["connectedNode"]

                connected_node_type_str = ', '.join(connected_node.labels) if connected_node.labels else 'N/A'
                connected_node_name_id = connected_node.get('name', connected_node.get('type', 'N/A'))
                if connected_node.get('id'):
                     connected_node_name_id += f" (ID: {connected_node.get('id')})"
                relationship_type = relationship.type if relationship else "UNKNOWN_RELATIONSHIP"

                connected_entity_props = {
                    "Relationship": relationship_type,
                    "Entity Type": connected_node_type_str,
                    "Entity Name/ID": connected_node_name_id
                }
                for prop_name, prop_value in connected_node.items():
                    if prop_name not in ['name', 'id', 'type']:
                        connected_entity_props[prop_name] = prop_value

                max_key_len_entity = max(len(str(k).replace('_', ' ').title()) for k in connected_entity_props.keys()) if connected_entity_props else 0
                max_value_len_entity = max(len(str(convert_neo4j_int(v))) for v in connected_entity_props.values()) if connected_entity_props else 0

                connected_entity_section_lines = [f"\n--- Connected Entity: {connected_node_type_str} ---"]
                header_entity = f"| {'Property':<{max_key_len_entity}} | {'Value':<{max_value_len_entity}} |"
                separator_entity = f"| {'-' * max_key_len_entity} | {'-' * max_value_len_entity} |"
                connected_entity_section_lines.extend([header_entity, separator_entity])

                for prop_name, prop_value in connected_entity_props.items():
                    connected_entity_section_lines.append(format_property(prop_name, prop_value, max_key_len_entity, max_value_len_entity))

                profile_sections.append("\n".join(connected_entity_section_lines))

            return "\n".join(profile_sections)

    except ServiceUnavailable as e:
        print(f"Neo4j connection lost during query: {e}")
        return "Knowledge Graph temporarily unavailable."
    except Exception as e:
        print(f"Error querying Neo4j: {e}")
        return f"Error fetching profile from Knowledge Graph: {e}"


# --- Helper to extract user name and ID from the query with new format ---
def extract_user_info_and_clean_query(full_query: str) -> Tuple[Union[str, None], Union[str, None], str]: # <--- FIXED LINE
    """
    Extracts user name and ID from the beginning of the query if in 'Name (ID) : Query' format.
    Returns (user_name, user_id, cleaned_query).
    """
    match = re.match(r'^\s*([A-Za-z\s]+)\s*\((P\d{3,})\)\s*:\s*(.*)', full_query, re.IGNORECASE)
    if match:
        user_name = match.group(1).strip()
        user_id = match.group(2).strip().upper()
        cleaned_query = match.group(3).strip()
        print(f"Extracted User Name: {user_name}, ID: {user_id}, Cleaned Query: {cleaned_query}")
        return user_name, user_id, cleaned_query

    id_match = re.search(r'\b([PC]\d{3,})\b', full_query, re.IGNORECASE)
    if id_match:
        user_id = id_match.group(1).upper()
        print(f"Extracted User ID (fallback): {user_id}")
        return None, user_id, full_query

    name_match = re.search(r'(?:user\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', full_query)
    if name_match:
        potential_name = name_match.group(1)
        if potential_name.lower() not in ["context", "question", "answer", "jpmorgan chase", "bedrock", "model"]:
            print(f"Extracted User Name (fallback): {potential_name}")
            return potential_name, None, full_query

    return None, None, full_query

# Call initialize_components once when the Lambda execution environment is spun up.
initialize_components()

def lambda_handler(event, context):
    """
    Main handler function for the AWS Lambda.
    """
    try:
        print(f"Received event for RAG: {json.dumps(event)}")

        raw_user_query = ""
        # Handle various input formats from API Gateway or direct invocation
        if 'requestBody' in event and 'content' in event['requestBody'] and 'application/json' in event['requestBody']['content']:
            # For API Gateway with custom Authorizer and Content-Type header setup
            body_str_or_dict = event['requestBody']['content']['application/json']['properties'].get('query')
            if isinstance(body_str_or_dict, dict):
                raw_user_query = body_str_or_dict.get('S', '') # If 'query' is a DynamoDB-like string attribute
            elif isinstance(body_str_or_dict, str):
                try:
                    # Attempt to parse if the string itself is JSON
                    parsed_body = json.loads(body_str_or_dict)
                    raw_user_query = parsed_body.get('query', body_str_or_dict)
                except json.JSONDecodeError:
                    raw_user_query = body_str_or_dict
            else:
                raw_user_query = str(body_str_or_dict) # Fallback to string conversion
        elif 'inputText' in event: # For direct Lambda invocation with 'inputText' key
            raw_user_query = event['inputText']
        elif 'body' in event: # For API Gateway proxy integration (common)
            body = json.loads(event['body'])
            raw_user_query = body.get('query', '')
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('No input query found in expected formats (e.g., "inputText" or "body.query").')
            }

        if not raw_user_query:
            return {
                'statusCode': 400,
                'body': json.dumps('Input query is empty.')
            }

        print(f"Raw User Query: \"{raw_user_query}\"")

        # Extract user info and get cleaned query
        user_name, user_id, cleaned_query = extract_user_info_and_clean_query(raw_user_query)

        user_profile_info = ""
        if user_id: # Prioritize ID for KG lookup
            print(f"Attempting to fetch user profile for ID: {user_id}")
            user_profile_info = query_neo4j_profile(user_id=user_id)
        elif user_name: # Fallback to name if ID not found
            print(f"Attempting to fetch user profile for Name: {user_name}")
            user_profile_info = query_neo4j_profile(user_name=user_name)
        else:
            user_profile_info = "No specific user identifier found in query to fetch profile."

        # Ensure user_profile_info is always a string.
        if not isinstance(user_profile_info, str):
            user_profile_info = str(user_profile_info)

        print(f"User Profile Info from KG:\n{user_profile_info}")
        print(f"Cleaned Query for RAG: \"{cleaned_query}\"")

        # Prepare the input for the RAG chain
        chain_input = {
            "question": cleaned_query,
            "user_profile_info": user_profile_info
        }
        print(f"\nChain Input for RAG:\n{json.dumps(chain_input, indent=2)}")

        final_response = rag_chain.invoke(chain_input)
        print(f"\nRAG Response:\n{final_response}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': final_response
            })
        }
    except Exception as e:
        print(f"Error in RAG Lambda handler: {e}")
        # Return a 500 Internal Server Error response
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal Server Error in RAG: {str(e)}')
        }