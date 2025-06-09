from pinecone_dataload import get_embedding, index, EMBEDDING_MODEL_ID
# --- Retrieval Part (Uncommented and Ready for Use) ---
print("\n--- Testing Retrieval (Example Search) ---")
query_text = "Can you share JPMC Tax Planning Guide?"
query_embedding = get_embedding(query_text) # Use the same function for query embeddings

if query_embedding is None:
    print("Could not generate embedding for query, cannot perform search.")
else:
    try:
        search_results = index.query(
            vector=query_embedding,
            top_k=3, # Retrieve top 3 most relevant documents
            include_metadata=True # Include original metadata with results
        )
        print(f"\nTop {len(search_results.matches)} search results for query: '{query_text}'")
        for i, match in enumerate(search_results.matches):
            print(f"\n--- Result {i+1} (ID: {match.id}, Score: {match.score:.4f}) ---")
            print(f"  Source: {match.metadata.get('source', 'N/A')}")
            if 'headline' in match.metadata:
                print(f"  Headline: {match.metadata['headline']}")
            if 'subject' in match.metadata:
                print(f"  Subject: {match.metadata['subject']}")
            print(f"  Date: {match.metadata.get('date', 'N/A')}")
            print(f"  Content Excerpt: {match.metadata.get('original_content', 'N/A')[:500]}...") # Show first 500 chars
            print(f"  Metadata: {match.metadata}")
            print("-" * 30)
    except Exception as e:
        print(f"Error during example search: {e}")