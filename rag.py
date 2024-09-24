import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import os
import pickle
from tqdm import tqdm

# Load Embedding model
print("Loading Embed Model...")
EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

def chunk_text(text, max_length=512):
    words = text.split()
    chunks = [' '.join(words[i:i + max_length]) for i in range(0, len(words), max_length)]
    return chunks

def db_builder(csv_path='data_profiles.csv', 
               index_path='data/vector_index.faiss', metadata_path='data/vector_metadata.pkl'):
    okc_pd = pd.read_csv("data/okcupid.csv")
    okc_pd["p_id"]=okc_pd.index

    cols = ["p_id"]
    essay_cols = ["essay"+str(i) for i in range(10)]
    okc_text = okc_pd[cols+essay_cols]

    """
    essay0- My self summary
    essay1- What I’m doing with my life
    essay2- I’m really good at
    essay3- The first thing people usually notice about me
    essay4- Favorite books, movies, show, music, and food
    essay5- The six things I could never do without
    essay6- I spend a lot of time thinking about
    essay7- On a typical Friday night I am
    essay8- The most private thing I am willing to admit
    essay9- You should message me if...
    """

    okc_text['document_str'] = okc_text[essay_cols].apply(lambda x: '\n'.join(x.astype(str)), axis=1)
    okc_doc = okc_text[['p_id', 'document_str']]
    
    # List to hold chunk embeddings, p_ids, and chunks
    all_chunk_embeddings = []
    all_p_ids = []
    all_chunks = []

    # Iterate through documents, chunk them, and embed them
    print("\t...chunking & embedding...")
    i = 0
    for index, row in tqdm(okc_doc.iterrows(), total=len(okc_doc), desc="Chunking and Embedding"):
        p_id = row['p_id']
        p_id = row['p_id']
        document = row['document_str']
        
        # Chunk the document
        chunks = chunk_text(document, max_length=512)
        
        # Embed each chunk and store the embeddings
        chunk_embeddings = EMBED_MODEL.encode(chunks, convert_to_tensor=False)
        all_chunk_embeddings.extend(chunk_embeddings)

        # Store the p_id and chunk metadata
        all_p_ids.extend([p_id] * len(chunk_embeddings))
        all_chunks.extend(chunks)

        i+=1


        if i > 5000:
            break

    # Convert embeddings to numpy array
    all_chunk_embeddings = np.array(all_chunk_embeddings)

    # Build FAISS index
    print("\t...building FAISS index...")
    dimension = all_chunk_embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)

    # Normalize embeddings and add to the FAISS index
    faiss.normalize_L2(all_chunk_embeddings)
    index.add(all_chunk_embeddings)

    # Save the FAISS index to disk
    print("\t...writing index...")
    faiss.write_index(index, index_path)
    
    # Save the metadata (p_ids and chunks) using pickle
    print("\t...writing metadata...")
    metadata = {'p_ids': all_p_ids, 'chunks': all_chunks}
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)

    print(f"Vector store and metadata saved at {index_path} and {metadata_path}")

# Function to retrieve the top K most similar elements based on query
def retrieve(query, k=5, 
             index_path='data/vector_index.faiss', metadata_path='data/vector_metadata.pkl'):
    # Load FAISS index
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file {index_path} not found. Please run db_builder() first.")
        
    index = faiss.read_index(index_path)
    
    # Embed the query
    query_embedding = EMBED_MODEL.encode([query], convert_to_tensor=False)
    faiss.normalize_L2(query_embedding)
    
    # Search the FAISS index
    D, I = index.search(np.array(query_embedding), k=k)
    
    # Load metadata (p_ids and chunks)
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    p_ids = metadata['p_ids']
    chunks = metadata['chunks']
    
    # Retrieve the top K p_ids and chunks
    result_p_ids = [p_ids[i] for i in I[0]]
    result_chunks = [chunks[i] for i in I[0]]
    distances = D[0]

    return result_p_ids, result_chunks, distances

# Example usage
if __name__ == "__main__":
    print("Building DB...")
    db_builder()
    query = "imagining random shit. laughing at aforementioned random shit. being goofy. articulating what i think and feel. convincing people i'm right. admitting when i'm wrong.  i'm also pretty good at helping people think through problems; my friends say i give good advice. and when i don't have a clue how to help, i will say: i give pretty good hug."
    top_p_ids, top_chunks, similarity_scores = retrieve(query)
    for i in range(len(top_p_ids)):
        print(f"p_id: {top_p_ids[i]}, Chunk: {top_chunks[i]}, Similarity score: {similarity_scores[i]}")