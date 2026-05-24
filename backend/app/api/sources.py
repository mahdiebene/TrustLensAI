"""Source reputation CRUD endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/sources")
async def list_sources():
    """List known sources and their reputation scores."""
    # TODO: Implement Neo4j source lookup
    return {"sources": [], "total": 0}
