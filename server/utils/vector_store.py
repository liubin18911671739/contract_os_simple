"""
Faiss Vector Store wrapper
Handles vector indexing and search for knowledge base chunks
"""

import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np


class FaissVectorStore:
    """Faiss-based vector store for KB chunks"""

    def __init__(
        self,
        collection_id: str,
        embedding_dim: int = 2048,  # ZhipuAI embedding-3 dimension (2048)
    ):
        """
        Initialize Faiss vector store

        Args:
            collection_id: KB collection ID
            embedding_dim: Embedding vector dimension
        """
        self.collection_id = collection_id
        self.embedding_dim = embedding_dim

        # Path for index and metadata
        self.index_dir = Path("./data/faiss_indexes") / collection_id
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.index_dir / "index.faiss"
        self.metadata_path = self.index_dir / "metadata.pkl"

        # Load existing or create new
        self.index: Optional[faiss.Index] = None
        self.chunk_ids: List[str] = []

        self._load_or_create()

    def _load_or_create(self):
        """Load existing index or create new one"""
        if self.index_path.exists() and self.metadata_path.exists():
            # Load existing index
            self.index = faiss.read_index(str(self.index_path))

            with open(self.metadata_path, "rb") as f:
                metadata = pickle.load(f)
                # Validate metadata structure to prevent security issues
                if not isinstance(metadata, dict):
                    raise ValueError(f"Invalid metadata format for collection {self.collection_id}")
                if "chunk_ids" not in metadata:
                    raise ValueError(f"Missing chunk_ids in metadata for collection {self.collection_id}")
                if not isinstance(metadata["chunk_ids"], list):
                    raise ValueError(f"chunk_ids must be a list for collection {self.collection_id}")
                # Validate all chunk_ids are strings
                if not all(isinstance(cid, str) for cid in metadata["chunk_ids"]):
                    raise ValueError(f"All chunk_ids must be strings for collection {self.collection_id}")
                self.chunk_ids = metadata["chunk_ids"]

            print(
                f"Loaded existing Faiss index for {self.collection_id} "
                f"with {self.index.ntotal} vectors"
            )
        else:
            # Create new index
            # Use IndexFlatIP (inner product) for cosine similarity
            # (assuming vectors are normalized)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.chunk_ids = []
            print(f"Created new Faiss index for {self.collection_id}")

    def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str]):
        """
        Add vectors to index

        Args:
            vectors: List of embedding vectors
            chunk_ids: List of chunk IDs corresponding to vectors
        """
        if len(vectors) != len(chunk_ids):
            raise ValueError(
                "Number of vectors must match number of chunk IDs"
            )

        # Convert to numpy array
        vectors_array = np.array(vectors, dtype=np.float32)

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors_array)

        # Add to index
        if self.index is not None:
            self.index.add(vectors_array)

        # Track chunk IDs
        self.chunk_ids.extend(chunk_ids)

    def search(
        self, query_vector: List[float], top_k: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of (chunk_id, score) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Convert and normalize query
        query_array = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query_array)

        # Search
        scores, indices = self.index.search(
            query_array, min(top_k, self.index.ntotal)
        )

        # Convert results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.chunk_ids):
                chunk_id = self.chunk_ids[idx]
                results.append((chunk_id, float(score)))

        return results

    def save(self):
        """Persist index and metadata to disk"""
        # Save index
        faiss.write_index(self.index, str(self.index_path))

        # Save metadata
        metadata = {"chunk_ids": self.chunk_ids}
        with open(self.metadata_path, "wb") as f:
            pickle.dump(metadata, f)

    def delete(self):
        """Delete index files"""
        if self.index_path.exists():
            self.index_path.unlink()
        if self.metadata_path.exists():
            self.metadata_path.unlink()

    @property
    def size(self) -> int:
        """Return number of vectors in index"""
        return self.index.ntotal if self.index else 0


# Global store for collection indexes
_vector_stores: dict[str, FaissVectorStore] = {}
_MAX_CACHED_STORES = 20  # Maximum number of vector stores to keep in memory


def get_vector_store(collection_id: str) -> FaissVectorStore:
    """Get or create vector store for a collection"""
    if collection_id not in _vector_stores:
        # If we have too many cached stores, remove the oldest ones
        if len(_vector_stores) >= _MAX_CACHED_STORES:
            # Remove oldest entries (first half)
            items_to_remove = list(_vector_stores.keys())[:_MAX_CACHED_STORES // 2]
            for key in items_to_remove:
                # Save before removing
                try:
                    _vector_stores[key].save()
                except Exception:
                    pass
                del _vector_stores[key]
        _vector_stores[collection_id] = FaissVectorStore(collection_id)
    return _vector_stores[collection_id]


def release_vector_store(collection_id: str):
    """Release a vector store from memory (saves before releasing)"""
    if collection_id in _vector_stores:
        try:
            _vector_stores[collection_id].save()
        except Exception:
            pass
        del _vector_stores[collection_id]


def save_all_vector_stores():
    """Save all vector stores to disk"""
    for store in _vector_stores.values():
        try:
            store.save()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to save vector store: {e}")
