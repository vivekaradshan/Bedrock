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
from dotenv import load_dotenv
from langchain_core.documents import Document

# Load environment variables from .env file
load_dotenv()

# --- Configuration (from Environment Variables) ---
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
pc_client = None
bedrock_runtime_client = None
rag_chain = None
embeddings_instance = None
vectorstore_instance = None
llm_instance = None
neo4j_driver = None

def initialize_components():
    global pc_client, bedrock_runtime_client, rag_chain, embeddings_instance, vectorstore_instance, llm_instance, neo4j_driver

    # --- Initialize Pinecone Client ---
    if pc_client is None:
        if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
            raise ValueError("PINECONE_API_KEY or PINECONE_ENVIRONMENT not set.")
        try:
            pc_client = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            print("Successfully initialized Pinecone client.")
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise

    # --- Initialize AWS Bedrock Runtime Client ---
    if bedrock_runtime_client is None:
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
            "max_tokens": 500, # Increased max_tokens for potentially longer responses
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
        # Function to format documents
        def format_docs(docs: list[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        # MODIFIED PROMPT TEMPLATE
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
        print(f"*** Prompt template initialized. Printing prompt {prompt_template}")
        rag_chain = (
            # Extract only the 'question' for the retriever
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
    if isinstance(neo4j_int, (int, float)): # Already a standard int or float
        return neo4j_int
    if hasattr(neo4j_int, 'low') and hasattr(neo4j_int, 'high'):
        return neo4j_int.high * 2**32 + neo4j_int.low
    return neo4j_int # Return as is if not a recognized Neo4j int type

# Helper to format properties into a table row
def format_property(key, value, max_key_len, max_value_len):
    formatted_key = key.replace('_', ' ').title()
    # Ensure value is a string, handle lists and Neo4j specific types
    if isinstance(value, list):
        formatted_value = ", ".join(map(str, value))
    else:
        # Pass through convert_neo4j_int for robustness
        formatted_value = str(convert_neo4j_int(value))

    return f"| {formatted_key:<{max_key_len}} | {formatted_value:<{max_value_len}} |"

# --- Neo4j Query Function (Modified for Table Output and Node.items fix) ---
def query_neo4j_profile(user_id: str = None, user_name: str = None) -> str:
    """
    Queries Neo4j for a user profile based on ID or Name,
    capturing maximum information about the customer, relationships,
    and connected nodes. Returns a comprehensive formatted string in a table format.
    """
    if not neo4j_driver: # Using the correct global variable name
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
    customer_info_captured = False

    try:
        with neo4j_driver.session() as session:
            result = session.run(query)
            records = list(result)

            if not records:
                return f"No profile found in Knowledge Graph for identifier: {user_id if user_id else user_name}."

            # Process customer details once from the first record
            customer = records[0]["c"]
            customer_props = {k: v for k, v in customer.items()} # Direct access using .items()
            customer_props['Labels'] = ", ".join(customer.labels) # Add labels as a property (Title Case for consistency)

            # Determine max lengths for alignment in customer table
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
                # Add all other properties of the connected node
                for prop_name, prop_value in connected_node.items(): # Direct access using .items()
                    if prop_name not in ['name', 'id', 'type']: # Exclude 'type' as it's often the same as node label
                        connected_entity_props[prop_name] = prop_value

                # Determine max lengths for alignment in connected entity table
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
        # Return a string even on error
        return f"Error fetching profile from Knowledge Graph: {e}"


# --- Helper to extract user name and ID from the query with new format ---
def extract_user_info_and_clean_query(full_query: str) -> tuple[str | None, str | None, str]:
    """
    Extracts user name and ID from the beginning of the query if in 'Name (ID) : Query' format.
    Returns (user_name, user_id, cleaned_query).
    """
    match = re.match(r'^\s*([A-Za-z\s]+)\s*\((P\d{3,})\)\s*:\s*(.*)', full_query, re.IGNORECASE)
    if match:
        user_name = match.group(1).strip()
        user_id = match.group(2).strip().upper() # Ensure ID is uppercase
        cleaned_query = match.group(3).strip()
        print(f"Extracted User Name: {user_name}, ID: {user_id}, Cleaned Query: {cleaned_query}")
        return user_name, user_id, cleaned_query

    # Fallback to original extraction if the strict format isn't found, but prioritize ID
    id_match = re.search(r'\b([PC]\d{3,})\b', full_query, re.IGNORECASE)
    if id_match:
        user_id = id_match.group(1).upper()
        print(f"Extracted User ID (fallback): {user_id}")
        return None, user_id, full_query # Return None for name, original query as cleaned

    name_match = re.search(r'(?:user\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', full_query)
    if name_match:
        potential_name = name_match.group(1)
        if potential_name.lower() not in ["context", "question", "answer", "jpmorgan chase", "bedrock", "model"]:
            print(f"Extracted User Name (fallback): {potential_name}")
            return potential_name, None, full_query

    return None, None, full_query # No user info found, return original query as cleaned


# --- Main execution block for VS Code ---
if __name__ == "__main__":
    try:
        initialize_components()

        print("\n--- RAG System Ready ---")
        print("Enter your query. Use 'Name (ID) : Query' format for user profiles (e.g., 'Alice (P123) : What are her recent transactions?').")
        print("Type 'exit' to quit.")

        while True:
            raw_user_query = "Sarah Johnson (P001) : Can you assess her risk profile for granting home loan application APL02?"
            if raw_user_query.lower() == 'exit':
                break

            if not raw_user_query:
                print("Input query is empty. Please try again.")
                continue

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

            # Crucial: Ensure user_profile_info is always a string.
            if not isinstance(user_profile_info, str):
                user_profile_info = str(user_profile_info) # Convert any non-string to string

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

            break # Remove this line if you want to keep the loop running for multiple queries

    except ValueError as ve:
        print(f"Configuration Error: {ve}. Please check your .env file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if neo4j_driver:
            print("Closing Neo4j driver.")
            neo4j_driver.close()