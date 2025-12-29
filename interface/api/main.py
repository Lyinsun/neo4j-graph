#!/usr/bin/env python3
"""
FastAPI HTTP API for Vector Recall System
Provides RESTful endpoints for vector-based search with filtering capabilities
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from domain.service.vector_recall import VectorRecallSystem
from domain.service.vector_indexer import VectorIndexer
from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService

# Initialize FastAPI app
app = FastAPI(
    title="Vector Recall System API",
    description="RESTful API for vector-based search with filtering capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize services (will be created on first request)
_recall_system = None
_vector_indexer = None


def get_recall_system():
    """Get or initialize the recall system"""
    global _recall_system
    if _recall_system is None:
        try:
            neo4j_client = Neo4jClient()
            embedding_service = EmbeddingService()
            _recall_system = VectorRecallSystem(neo4j_client, embedding_service)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize services: {str(e)}")
    return _recall_system


def get_vector_indexer():
    """Get or initialize the vector indexer"""
    global _vector_indexer
    if _vector_indexer is None:
        try:
            neo4j_client = Neo4jClient()
            embedding_service = EmbeddingService()
            _vector_indexer = VectorIndexer(neo4j_client, embedding_service)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize vector indexer: {str(e)}")
    return _vector_indexer


# Request models
class RecallRequest(BaseModel):
    """Base request model for recall operations"""
    query_text: str
    top_k: int = 5
    node_label: str = "Ontology"
    filters: Optional[Dict[str, Any]] = None


class CreateIndexRequest(BaseModel):
    """
    Request model for creating a vector index
    """
    index_name: str
    node_label: str
    property_name: str


class CreateAllIndexesResponse(BaseModel):
    """
    Response model for create all indexes operation
    """
    results: Dict[str, bool]
    message: str


class SimilarPRDRequest(BaseModel):
    """Request model for similar PRD search"""
    query_text: str
    top_k: int = 5


class ReviewSuggestionRequest(BaseModel):
    """Request model for review suggestion search"""
    query_text: str
    department: Optional[str] = None
    top_k: int = 10


class RiskIdentificationRequest(BaseModel):
    """Request model for risk identification"""
    query_text: str
    top_k: int = 5


class KnowledgeBaseRequest(BaseModel):
    """
    Request model for knowledge base search
    """
    query_text: str
    top_k: int = 8
    node_label: str = "Ontology"
    filters: Optional[Dict[str, Any]] = None


class HybridSearchRequest(BaseModel):
    """
    Request model for hybrid search
    """
    query_text: str
    node_label: str = "PRD"
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 10


class EmbeddingRequest(BaseModel):
    """
    Request model for single text embedding
    """
    text: str
    field: str = "description"  # 默认是description字段


class BatchEmbeddingRequest(BaseModel):
    """
    Request model for batch text embedding
    """
    texts: List[str]
    field: str = "description"  # 默认是description字段
    batch_size: int = 20


# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy", "message": "Vector Recall System API is running"}


# Recall endpoints
@app.post("/recall/knowledge-base", response_model=List[Dict[str, Any]], tags=["recall"])
async def knowledge_base_recall(request: KnowledgeBaseRequest):
    """
    Search knowledge base with filtering capabilities
    
    Args:
        request: Knowledge base search request parameters
    
    Returns:
        List of relevant nodes with similarity scores
    """
    try:
        recall_system = get_recall_system()
        results = recall_system.search_knowledge_base(
            query_text=request.query_text,
            top_k=request.top_k,
            node_label=request.node_label,
            filters=request.filters
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge base search failed: {str(e)}")


@app.post("/recall/similar-prds", response_model=List[Dict[str, Any]], tags=["recall"])
async def similar_prds_recall(request: SimilarPRDRequest):
    """
    Find similar PRDs based on description
    
    Args:
        request: Similar PRD search request parameters
    
    Returns:
        List of similar PRDs with similarity scores and decision outcomes
    """
    try:
        recall_system = get_recall_system()
        results = recall_system.find_similar_prds(
            query_text=request.query_text,
            top_k=request.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar PRD search failed: {str(e)}")


@app.post("/recall/review-suggestions", response_model=List[Dict[str, Any]], tags=["recall"])
async def review_suggestions_recall(request: ReviewSuggestionRequest):
    """
    Get intelligent review suggestions based on similar historical reviews
    
    Args:
        request: Review suggestion search request parameters
    
    Returns:
        List of historical review suggestions grouped by department
    """
    try:
        recall_system = get_recall_system()
        results = recall_system.get_intelligent_review_suggestions(
            query_text=request.query_text,
            department=request.department,
            top_k=request.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review suggestion search failed: {str(e)}")


@app.post("/recall/risk-identification", response_model=List[Dict[str, Any]], tags=["recall"])
async def risk_identification_recall(request: RiskIdentificationRequest):
    """
    Identify potential risks by finding similar historical risks
    
    Args:
        request: Risk identification request parameters
    
    Returns:
        List of historical risk assessments from similar projects
    """
    try:
        recall_system = get_recall_system()
        results = recall_system.identify_potential_risks(
            query_text=request.query_text,
            top_k=request.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk identification failed: {str(e)}")


@app.post("/recall/hybrid", response_model=List[Dict[str, Any]], tags=["recall"])
async def hybrid_search_recall(request: HybridSearchRequest):
    """
    Advanced hybrid search combining vector similarity and filters
    
    Args:
        request: Hybrid search request parameters
    
    Returns:
        List of search results
    """
    try:
        recall_system = get_recall_system()
        results = recall_system.hybrid_search(
            query_text=request.query_text,
            node_label=request.node_label,
            filters=request.filters,
            top_k=request.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


# Embedding endpoints
@app.post("/embedding/generate", response_model=Dict[str, Any], tags=["embedding"])
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate embedding for a single text
    
    Args:
        request: Embedding request parameters with text and field
    
    Returns:
        Embedding vector and metadata
    """
    try:
        recall_system = get_recall_system()
        # Directly use the embedding service from recall system
        embedding = recall_system.embedding_service.generate_embedding(request.text)
        return {
            "text": request.text,
            "field": request.field,
            "embedding": embedding,
            "dimension": len(embedding),
            "model": recall_system.embedding_service.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/embedding/batch", response_model=Dict[str, Any], tags=["embedding"])
async def generate_batch_embeddings(request: BatchEmbeddingRequest):
    """
    Generate embeddings for multiple texts in batch
    
    Args:
        request: Batch embedding request parameters
    
    Returns:
        List of embeddings and metadata
    """
    try:
        recall_system = get_recall_system()
        # Directly use the embedding service from recall system
        embeddings = recall_system.embedding_service.generate_embeddings_batch(
            request.texts, 
            batch_size=request.batch_size
        )
        return {
            "count": len(embeddings),
            "field": request.field,
            "batch_size": request.batch_size,
            "embeddings": embeddings,
            "model": recall_system.embedding_service.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")


# Vector Index Management endpoints
@app.post("/index/create", response_model=Dict[str, Any], tags=["vector-index"])
async def create_vector_index(request: CreateIndexRequest):
    """
    Create a vector index for Neo4j nodes
    
    Args:
        request: Create index request parameters
    
    Returns:
        Success status and message
    """
    try:
        indexer = get_vector_indexer()
        success = indexer.create_vector_index(
            index_name=request.index_name,
            node_label=request.node_label,
            property_name=request.property_name
        )
        if success:
            return {
                "success": True,
                "message": f"Vector index '{request.index_name}' created successfully",
                "index_name": request.index_name
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to create vector index '{request.index_name}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector index creation failed: {str(e)}")


@app.post("/index/create-all", response_model=CreateAllIndexesResponse, tags=["vector-index"])
async def create_all_vector_indexes():
    """
    Create all required vector indexes for the system
    
    Returns:
        Dictionary of index creation results
    """
    try:
        indexer = get_vector_indexer()
        results = indexer.create_all_indexes()
        return CreateAllIndexesResponse(
            results=results,
            message="Vector index creation completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vector indexes: {str(e)}")


@app.delete("/index/{index_name}", response_model=Dict[str, Any], tags=["vector-index"])
async def drop_vector_index(index_name: str):
    """
    Drop a vector index
    
    Args:
        index_name: Name of the vector index to drop
    
    Returns:
        Success status and message
    """
    try:
        indexer = get_vector_indexer()
        success = indexer.drop_vector_index(index_name)
        if success:
            return {
                "success": True,
                "message": f"Vector index '{index_name}' dropped successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to drop vector index '{index_name}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector index drop failed: {str(e)}")


@app.get("/index/list", response_model=List[Dict[str, Any]], tags=["vector-index"])
async def list_vector_indexes():
    """
    List all vector indexes in the database
    
    Returns:
        List of vector indexes with their details
    """
    try:
        indexer = get_vector_indexer()
        indexes = indexer.list_vector_indexes()
        return indexes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list vector indexes: {str(e)}")


# Main entry point for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "interface.api.main:app",
        host="0.0.0.0",
        port=8010,
        reload=True,
        log_level="info"
    )
