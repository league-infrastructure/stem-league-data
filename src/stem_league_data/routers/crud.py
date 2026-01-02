"""Generic CRUD router factory for simple resources."""

from typing import Any, Callable, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db

# Type variables for generic CRUD operations
ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)
ResponseSchemaT = TypeVar("ResponseSchemaT", bound=BaseModel)


def create_crud_router(
    model: Type[ModelT],
    create_schema: Type[CreateSchemaT],
    update_schema: Type[UpdateSchemaT],
    response_schema: Type[ResponseSchemaT],
    prefix: str,
    tags: list[str],
    id_field: str = "id",
    id_type: Type = int,
) -> APIRouter:
    """Create a CRUD router for a model.
    
    Args:
        model: SQLAlchemy model class
        create_schema: Pydantic schema for create operations
        update_schema: Pydantic schema for update operations
        response_schema: Pydantic schema for responses
        prefix: URL prefix for the router
        tags: Tags for OpenAPI documentation
        id_field: Name of the ID field (default: "id")
        id_type: Type of the ID field (default: int)
        
    Returns:
        Configured APIRouter with CRUD endpoints
    """
    router = APIRouter(prefix=prefix, tags=tags)
    
    @router.get("", response_model=list[response_schema])
    def list_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: Session = Depends(get_db),
    ) -> list[Any]:
        """List all items with pagination."""
        items = db.query(model).offset(skip).limit(limit).all()
        return items
    
    @router.get("/count")
    def count_items(db: Session = Depends(get_db)) -> dict[str, int]:
        """Get total count of items."""
        count = db.query(func.count(getattr(model, id_field))).scalar()
        return {"count": count}
    
    if id_type == int:
        @router.get("/{item_id}", response_model=response_schema)
        def get_item(item_id: int, db: Session = Depends(get_db)) -> Any:
            """Get a single item by ID."""
            item = db.query(model).filter(getattr(model, id_field) == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            return item
        
        @router.post("", response_model=response_schema, status_code=201)
        def create_item(
            data: create_schema,  # type: ignore[valid-type]
            db: Session = Depends(get_db),
        ) -> Any:
            """Create a new item."""
            item = model(**data.model_dump(exclude_unset=True))
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        
        @router.put("/{item_id}", response_model=response_schema)
        def update_item(
            item_id: int,
            data: update_schema,  # type: ignore[valid-type]
            db: Session = Depends(get_db),
        ) -> Any:
            """Update an existing item."""
            item = db.query(model).filter(getattr(model, id_field) == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(item, field, value)
            
            db.commit()
            db.refresh(item)
            return item
        
        @router.delete("/{item_id}", status_code=204)
        def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
            """Delete an item."""
            item = db.query(model).filter(getattr(model, id_field) == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            
            db.delete(item)
            db.commit()
    else:
        # String ID version
        @router.get("/{item_id}", response_model=response_schema)
        def get_item_str(item_id: str, db: Session = Depends(get_db)) -> Any:
            """Get a single item by ID."""
            item = db.query(model).filter(getattr(model, id_field) == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            return item
        
        @router.post("", response_model=response_schema, status_code=201)
        def create_item_str(
            data: create_schema,  # type: ignore[valid-type]
            db: Session = Depends(get_db),
        ) -> Any:
            """Create a new item."""
            item = model(**data.model_dump(exclude_unset=True))
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        
        @router.put("/{item_id}", response_model=response_schema)
        def update_item_str(
            item_id: str,
            data: update_schema,  # type: ignore[valid-type]
            db: Session = Depends(get_db),
        ) -> Any:
            """Update an existing item."""
            item = db.query(model).filter(getattr(model, id_field) == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(item, field, value)
            
            db.commit()
            db.refresh(item)
            return item
        
        @router.delete("/{item_id}", status_code=204)
        def delete_item_str(item_id: str, db: Session = Depends(get_db)) -> None:
            """Delete an item."""
            item = db.query(model).filter(getattr(model, id_field) == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            
            db.delete(item)
            db.commit()
    
    return router
