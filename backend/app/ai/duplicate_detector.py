import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.grievance_embedding import GrievanceEmbedding
from app.models.grievance import Grievance
from app.ai.base import DuplicateMatch
from app.core.config import settings

class VectorDuplicateDetector:
    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.DUPLICATE_SIMILARITY_THRESHOLD

    async def find_duplicates(
        self,
        db: AsyncSession,
        grievance_id: uuid.UUID,
        embedding: List[float]
    ) -> DuplicateMatch:
        """
        Performs semantic vector search across existing grievance embeddings using pgvector.
        Returns advisory duplicate signals without merging or closing grievances.
        """
        if not embedding or len(embedding) != 384:
            return DuplicateMatch(possible_duplicate=False, similarity=0.0)

        # Use pgvector.sqlalchemy built-in cosine_distance method
        query = (
            select(
                GrievanceEmbedding.grievance_id,
                (1 - GrievanceEmbedding.embedding.cosine_distance(embedding)).label("similarity"),
                Grievance.title
            )
            .join(Grievance, GrievanceEmbedding.grievance_id == Grievance.id)
            .where(GrievanceEmbedding.grievance_id != grievance_id)
            .order_by(GrievanceEmbedding.embedding.cosine_distance(embedding))
            .limit(1)
        )
        
        result = await db.execute(query)
        row = result.first()
        
        if row:
            matched_gid, raw_sim, matched_title = row
            similarity = round(float(raw_sim), 3) if raw_sim is not None else 0.0
            matched_id = str(matched_gid)
            
            if similarity >= self.threshold:
                return DuplicateMatch(
                    possible_duplicate=True,
                    similarity=similarity,
                    matched_grievance_id=matched_id,
                    reason=f"High semantic similarity ({similarity * 100:.1f}%) with grievance '{matched_title}' ({matched_id})"
                )
            else:
                return DuplicateMatch(
                    possible_duplicate=False,
                    similarity=similarity,
                    matched_grievance_id=matched_id,
                    reason=f"Sub-threshold similarity ({similarity * 100:.1f}%) with grievance '{matched_title}'"
                )

        return DuplicateMatch(
            possible_duplicate=False,
            similarity=0.0,
            reason="No existing grievance vectors found for comparison"
        )
