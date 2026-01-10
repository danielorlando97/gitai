"""Abstract repository pattern for data persistence."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class AbstractRepository(ABC):
    """Abstract base class for repositories."""

    @abstractmethod
    def create(self, entity: Any) -> bool:
        """Create a new entity."""
        pass

    @abstractmethod
    def read(self, entity_id: Any) -> Optional[Any]:
        """Read an entity by ID."""
        pass

    @abstractmethod
    def update(self, entity_id: Any, entity: Any) -> bool:
        """Update an entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete an entity."""
        pass

    @abstractmethod
    def list_all(self, filters: Optional[Dict] = None) -> List[Any]:
        """List all entities with optional filters."""
        pass
