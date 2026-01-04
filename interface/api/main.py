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


class GenerateAndStoreEmbeddingRequest(BaseModel):
    """
    Request model for generating embeddings and storing them in the database
    Supports both nodes and relationships
    """
    element_type: str = "node"  # "node" 或 "relationship"
    node_label: Optional[str] = None  # 节点标签，如 "OntologyClass" (element_type="node" 时必需)
    relationship_type: Optional[str] = None  # 关系类型，如 "INHERITANCE", "LINK" (element_type="relationship" 时必需)
    source_property: str = "description"  # 源文本字段
    target_property: str = "description_embedding"  # 目标embedding字段
    batch_size: int = 20  # 批处理大小
    filters: Optional[Dict[str, Any]] = None  # 可选的过滤条件


class GenerateAndStoreEmbeddingResponse(BaseModel):
    """
    Response model for generate and store embedding operation
    """
    success: bool
    message: str
    total_nodes: int
    processed_nodes: int
    failed_nodes: int
    embedding_dimension: int


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


@app.post("/embedding/generate-and-store", response_model=GenerateAndStoreEmbeddingResponse, tags=["embedding"])
async def generate_and_store_embeddings(request: GenerateAndStoreEmbeddingRequest):
    """
    Generate embeddings for nodes or relationships and store them in the database

    This endpoint supports both nodes and relationships:
    - For nodes: specify element_type="node" and node_label
    - For relationships: specify element_type="relationship" and relationship_type

    Steps:
    1. Query elements by type and optional filters
    2. Extract the source property (e.g., "description")
    3. Generate embeddings in batches
    4. Update elements with the embeddings in the target property

    Args:
        request: Generate and store embedding request parameters

    Returns:
        Statistics about the embedding generation and storage process
    """
    try:
        recall_system = get_recall_system()
        neo4j_client = recall_system.client
        embedding_service = recall_system.embedding_service

        # 1. Build query based on element type
        if request.element_type == "node":
            # Node query
            conditions = [f"e.{request.source_property} IS NOT NULL"]
            if request.filters:
                filter_conditions = [f"e.{key} = ${key}" for key in request.filters.keys()]
                conditions.extend(filter_conditions)

            where_clause = "WHERE " + " AND ".join(conditions)

            # 如果提供了 node_label，使用标签过滤；否则匹配所有节点
            if request.node_label:
                query = f"""
                MATCH (e:{request.node_label})
                {where_clause}
                RETURN id(e) as element_id, e.{request.source_property} as text, labels(e) as labels
                """
                element_name = request.node_label
            else:
                query = f"""
                MATCH (e)
                {where_clause}
                RETURN id(e) as element_id, e.{request.source_property} as text, labels(e) as labels
                """
                element_name = "all nodes"
        else:
            # Relationship query
            conditions = [f"e.{request.source_property} IS NOT NULL"]
            if request.filters:
                filter_conditions = [f"e.{key} = ${key}" for key in request.filters.keys()]
                conditions.extend(filter_conditions)

            where_clause = "WHERE " + " AND ".join(conditions)

            # 如果提供了 relationship_type，使用类型过滤；否则匹配所有关系
            if request.relationship_type:
                query = f"""
                MATCH ()-[e:{request.relationship_type}]->()
                {where_clause}
                RETURN id(e) as element_id, e.{request.source_property} as text, type(e) as rel_type
                """
                element_name = request.relationship_type
            else:
                query = f"""
                MATCH ()-[e]->()
                {where_clause}
                RETURN id(e) as element_id, e.{request.source_property} as text, type(e) as rel_type
                """
                element_name = "all relationships"

        # Execute query with filters as parameters
        results = neo4j_client.execute_query(query, request.filters or {})

        if not results:
            return GenerateAndStoreEmbeddingResponse(
                success=True,
                message=f"No {element_name} {request.element_type}s found with {request.source_property} property",
                total_nodes=0,
                processed_nodes=0,
                failed_nodes=0,
                embedding_dimension=0
            )

        total_elements = len(results)

        # 2. Extract texts and element IDs
        texts = [result['text'] for result in results]
        element_ids = [result['element_id'] for result in results]

        # 3. Generate embeddings in batches
        embeddings = embedding_service.generate_embeddings_batch(
            texts,
            batch_size=request.batch_size
        )

        if not embeddings:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate embeddings"
            )

        # 4. Update elements with embeddings
        if request.element_type == "node":
            if request.node_label:
                update_query = f"""
                UNWIND $data AS item
                MATCH (e:{request.node_label})
                WHERE id(e) = item.element_id
                SET e.{request.target_property} = item.embedding
                RETURN count(e) as updated_count
                """
            else:
                update_query = f"""
                UNWIND $data AS item
                MATCH (e)
                WHERE id(e) = item.element_id
                SET e.{request.target_property} = item.embedding
                RETURN count(e) as updated_count
                """
        else:
            if request.relationship_type:
                update_query = f"""
                UNWIND $data AS item
                MATCH ()-[e:{request.relationship_type}]->()
                WHERE id(e) = item.element_id
                SET e.{request.target_property} = item.embedding
                RETURN count(e) as updated_count
                """
            else:
                update_query = f"""
                UNWIND $data AS item
                MATCH ()-[e]->()
                WHERE id(e) = item.element_id
                SET e.{request.target_property} = item.embedding
                RETURN count(e) as updated_count
                """

        data = [
            {"element_id": element_id, "embedding": embedding}
            for element_id, embedding in zip(element_ids, embeddings)
        ]

        update_result = neo4j_client.execute_query(update_query, {"data": data})
        processed_elements = update_result[0]['updated_count'] if update_result else 0
        failed_elements = total_elements - processed_elements

        # 5. Return results
        return GenerateAndStoreEmbeddingResponse(
            success=True,
            message=f"Successfully generated and stored embeddings for {processed_elements}/{total_elements} {element_name} {request.element_type}s",
            total_nodes=total_elements,
            processed_nodes=processed_elements,
            failed_nodes=failed_elements,
            embedding_dimension=len(embeddings[0]) if embeddings else 0
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate and store embeddings: {str(e)}"
        )


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
        port=8001,
        reload=True,
        log_level="info"
    )
