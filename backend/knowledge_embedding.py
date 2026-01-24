from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import re
import os
from typing import List, Dict, Any
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pinecone
pinecone_api_key = os.getenv("PINECONE_KEY")
index_name = "myself"

# Initialize Pinecone client
pc = Pinecone(api_key=pinecone_api_key)

# Initialize embeddings model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Create index if it doesn't exist
if index_name not in pc.list_indexes().names():
    logger.info(f"Creating Pinecone index: {index_name}")
    pc.create_index(
        name=index_name,
        dimension=384,  # all-MiniLM-L6-v2 dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    logger.info(f"Index '{index_name}' created successfully")
else:
    logger.info(f"Index '{index_name}' already exists")

# Get index
index = pc.Index(index_name)

# Initialize vector store
vector_store = PineconeVectorStore(index=index, embedding=embeddings)

# Initialize sentence transformer for semantic chunking
sentence_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def semantic_chunk_text(text: str, similarity_threshold: float = 0.5, max_chunk_size: int = 1000) -> List[str]:
    """
    Custom semantic chunking using sentence-transformers

    Args:
        text: Text to chunk
        similarity_threshold: Threshold for semantic similarity (0-1). Lower = more chunks
        max_chunk_size: Maximum characters per chunk

    Returns:
        List of semantically coherent text chunks
    """
    # Split into sentences using regex
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= 1:
        return [text]

    # Calculate embeddings for all sentences
    embeddings_array = sentence_model.encode(sentences, convert_to_numpy=True)

    # Calculate cosine similarities between consecutive sentences
    similarities = []
    for i in range(len(embeddings_array) - 1):
        # Cosine similarity = dot product of normalized vectors
        similarity = np.dot(embeddings_array[i], embeddings_array[i + 1])
        similarities.append(similarity)

    # Find breakpoints where similarity drops below threshold
    chunks = []
    current_chunk = [sentences[0]]
    current_size = len(sentences[0])

    for i, similarity in enumerate(similarities):
        next_sentence = sentences[i + 1]
        next_size = len(next_sentence)

        # Create new chunk if similarity is low OR chunk is getting too large
        if similarity < similarity_threshold or (current_size + next_size) > max_chunk_size:
            # Save current chunk
            chunks.append(' '.join(current_chunk))
            # Start new chunk
            current_chunk = [next_sentence]
            current_size = next_size
        else:
            # Add to current chunk
            current_chunk.append(next_sentence)
            current_size += next_size + 1  # +1 for space

    # Add the last chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def load_knowledge_base():
    """
    Load all knowledge base files from knowledge_base folder and index them into Pinecone
    Uses custom semantic chunking with sentence-transformers for intelligent text splitting
    """
    try:
        knowledge_base_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")

        if not os.path.exists(knowledge_base_dir):
            logger.error(f"Knowledge base directory not found: {knowledge_base_dir}")
            return

        all_documents = []

        # Read all .txt and .md files from knowledge_base folder
        for filename in os.listdir(knowledge_base_dir):
            if filename.endswith(".txt") or filename.endswith(".md"):
                file_path = os.path.join(knowledge_base_dir, filename)

                logger.info(f"Processing file: {filename}")

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Use custom semantic chunking
                # Lower threshold = more chunks (better for specific questions)
                # Higher threshold = fewer chunks (better for context)
                chunk_texts = semantic_chunk_text(
                    content,
                    similarity_threshold=0.4,  # Lower threshold for more focused chunks
                    max_chunk_size=800  # Smaller chunks for better precision
                )

                # Create Document objects with metadata
                for i, chunk_text in enumerate(chunk_texts):
                    doc = Document(
                        page_content=chunk_text,
                        metadata={
                            "source": filename,
                            "chunk_id": i,
                            "total_chunks": len(chunk_texts),
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    all_documents.append(doc)

                logger.info(f"Created {len(chunk_texts)} semantic chunks from {filename}")

        logger.info(f"Total documents to index: {len(all_documents)}")

        # Index all documents into Pinecone
        if all_documents:
            vector_store.add_documents(all_documents)
            logger.info(f"✅ Successfully indexed {len(all_documents)} documents into Pinecone index '{index_name}'")
        else:
            logger.warning("⚠️ No documents found to index")

    except Exception as e:
        logger.error(f"❌ Error loading knowledge base: {str(e)}")
        raise


def query_knowledge_base(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Query the knowledge base and return relevant results

    Args:
        query: Search query
        top_k: Number of results to return

    Returns:
        List of relevant documents with content and metadata
    """
    try:
        # Search vector store
        results = vector_store.similarity_search_with_score(query, k=top_k)

        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "chunk_id": doc.metadata.get("chunk_id", 0),
                "score": float(score)
            })

        return formatted_results

    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise


if __name__ == "__main__":
    # Run the knowledge base loader
    logger.info("🚀 Starting knowledge base indexing...")
    load_knowledge_base()
    logger.info("✨ Knowledge base indexing complete!")

    # Test query
    print("\n" + "="*50)
    print("Testing query...")
    print("="*50)
    results = query_knowledge_base("What projects has Rayansh worked on?", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Source: {result['source']}")
        print(f"Score: {result['score']:.4f}")
        print(f"Content: {result['content'][:200]}...")
    print("\n" + "="*50)
