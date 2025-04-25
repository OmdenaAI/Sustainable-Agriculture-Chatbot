from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, UploadFile, File, Form, Path, Query
from typing import List, Dict, Any, Optional
import logging
import uuid
import json
import time
from datetime import datetime
from app.models.schemas import User, DocumentIngestionRequest, DocumentIngestionResponse, DocumentResponse
from app.api.routes.auth import get_current_user
from app.services.rag import RAGService
#
from app.core.exceptions import DatabaseError, ResourceNotFoundError

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
rag_service = RAGService()

def prepare_document(text, metadata=None, chunk_size=1000, chunk_overlap=200):
    """
    Prepare a document for ingestion by chunking it into smaller pieces
    """
    if metadata is None:
        metadata = {}
    
    # Simple chunking by splitting on newlines and then combining
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) <= chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": metadata
                })
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append({
            "content": current_chunk.strip(),
            "metadata": metadata
        })
    
    return chunks

@router.post("/ingest", response_model=DocumentIngestionResponse)
async def ingest_document(
    request: Request,
    document_request: DocumentIngestionRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a document into the RAG system
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        logger.info(f"Document ingestion request from user: {current_user.id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "document_title": document_request.title,
            "content_length": len(document_request.content)
        })
        
        # Prepare metadata
        metadata = {
            "title": document_request.title,
            "source": document_request.source,
            "author": document_request.author,
            "user_id": current_user.id,
            "ingestion_date": datetime.utcnow().isoformat(),
            **document_request.metadata
        }
        
        # Prepare document chunks
        documents = prepare_document(
            document_request.content,
            metadata=metadata,
            chunk_size=document_request.chunk_size or 1000
        )
        
        logger.info(f"Created {len(documents)} document chunks", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "chunk_count": len(documents)
        })
        
        # Add documents to RAG system
        count = await rag_service.add_documents(documents)
        
        process_time = time.time() - start_time
        logger.info(f"Ingested {count} document chunks in {process_time:.3f}s", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "document_title": document_request.title,
            "chunk_count": count,
            "process_time": process_time
        })
        
        # Generate a document ID
        document_id = str(uuid.uuid4())
        
        return DocumentIngestionResponse(
            success=True,
            message=f"Successfully ingested {count} document chunks",
            document_id=document_id,
            chunk_count=count
        )
    
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting document: {str(e)}"
        )

@router.post("/ingest-file", response_model=DocumentIngestionResponse)
async def ingest_file(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    source: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    chunk_size: Optional[int] = Form(1000),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a file into the RAG system
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        logger.info(f"File ingestion request from user: {current_user.id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "file_name": file.filename,
            "title": title,
            "content_type": file.content_type
        })
        
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.content_type == "application/pdf":
            # For a real implementation, you would use a PDF parser here
            # For simplicity, we'll just decode as UTF-8 and hope for the best
            try:
                content_text = content.decode("utf-8")
            except UnicodeDecodeError:
                logger.error(f"Failed to decode PDF as UTF-8", extra={
                    "request_id": request_id,
                    "user_id": current_user.id,
                    "file_name": file.filename
                })
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF parsing not implemented in this example. Please submit text content."
                )
        else:
            # Assume it's a text file
            try:
                content_text = content.decode("utf-8")
            except UnicodeDecodeError:
                logger.error(f"Failed to decode file as UTF-8", extra={
                    "request_id": request_id,
                    "user_id": current_user.id,
                    "file_name": file.filename
                })
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not decode file as text. Please submit a valid text file."
                )
        
        # Parse metadata
        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except json.JSONDecodeError:
                meta_dict = {"raw_metadata": metadata}
        
        # Prepare metadata
        full_metadata = {
            "title": title,
            "source": source or file.filename,
            "author": author,
            "file_name": file.filename,
            "content_type": file.content_type,
            "user_id": current_user.id,
            "ingestion_date": datetime.utcnow().isoformat(),
            **meta_dict
        }
        
        # Prepare document chunks
        documents = prepare_document(
            content_text,
            metadata=full_metadata,
            chunk_size=chunk_size
        )
        
        logger.info(f"Created {len(documents)} document chunks from file", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "file_name": file.filename,
            "chunk_count": len(documents)
        })
        
        # Add documents to RAG system
        count = await rag_service.add_documents(documents)
        
        process_time = time.time() - start_time
        logger.info(f"Ingested {count} document chunks from file in {process_time:.3f}s", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "file_name": file.filename,
            "chunk_count": count,
            "process_time": process_time
        })
        
        # Generate a document ID
        document_id = str(uuid.uuid4())
        
        return DocumentIngestionResponse(
            success=True,
            message=f"Successfully ingested {count} document chunks from file {file.filename}",
            document_id=document_id,
            chunk_count=count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "file_name": file.filename if file else "unknown"
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting file: {str(e)}"
        )

@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(
    request: Request,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Search for documents using the RAG system
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        logger.info(f"Document search request from user: {current_user.id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "query": query,
            "limit": limit
        })
        
        # Search for documents
        results = await rag_service.retrieve(query, limit=limit)
        
        process_time = time.time() - start_time
        logger.info(f"Found {len(results)} documents in {process_time:.3f}s", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "result_count": len(results),
            "process_time": process_time
        })
        
        # Format results
        formatted_results = []
        for result in results:
            metadata = result.get("metadata", {})
            formatted_results.append(
                DocumentResponse(
                    id=result.get("doc_id", str(uuid.uuid4())),
                    text=result.get("text", ""),
                    title=metadata.get("title", "Untitled"),
                    source=metadata.get("source", "Unknown"),
                    author=metadata.get("author", None),
                    score=result.get("score", 0.0),
                    metadata=metadata
                )
            )
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "query": query
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )

@router.post("/bulk-ingest", response_model=DocumentIngestionResponse)
async def bulk_ingest_documents(
    request: Request,
    documents: List[DocumentIngestionRequest] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk ingest multiple documents into the RAG system
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        logger.info(f"Bulk document ingestion request from user: {current_user.id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "document_count": len(documents)
        })
        
        total_chunks = 0
        all_chunks = []
        
        # Process each document
        for doc in documents:
            # Prepare metadata
            metadata = {
                "title": doc.title,
                "source": doc.source,
                "author": doc.author,
                "user_id": current_user.id,
                "ingestion_date": datetime.utcnow().isoformat(),
                **doc.metadata
            }
            
            # Prepare document chunks
            chunks = prepare_document(
                doc.content,
                metadata=metadata,
                chunk_size=doc.chunk_size or 1000
            )
            
            all_chunks.extend(chunks)
            total_chunks += len(chunks)
        
        logger.info(f"Created {total_chunks} document chunks from {len(documents)} documents", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "document_count": len(documents),
            "chunk_count": total_chunks
        })
        
        # Add all chunks to RAG system
        count = await rag_service.add_documents(all_chunks)
        
        process_time = time.time() - start_time
        logger.info(f"Ingested {count} document chunks in {process_time:.3f}s", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "document_count": len(documents),
            "chunk_count": count,
            "process_time": process_time
        })
        
        # Generate a batch ID
        batch_id = str(uuid.uuid4())
        
        return DocumentIngestionResponse(
            success=True,
            message=f"Successfully ingested {count} document chunks from {len(documents)} documents",
            document_id=batch_id,
            chunk_count=count
        )
    
    except Exception as e:
        logger.error(f"Error in bulk document ingestion: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "document_count": len(documents) if documents else 0
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk document ingestion: {str(e)}"
        )