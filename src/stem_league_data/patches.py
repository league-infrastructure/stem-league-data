"""Monkey patches for third-party library compatibility with Pydantic V2."""

from typing import Any, Type


def patch_fastapi_crudrouter_pydantic_v2() -> None:
    """
    Patch fastapi_crudrouter to work with Pydantic V2.
    
    The library uses deprecated Pydantic V1 APIs that need to be patched.
    """
    try:
        import fastapi_crudrouter.core._utils as utils
        
        # Patch get_pk_type to work with Pydantic V2
        original_get_pk_type = utils.get_pk_type
        
        def get_pk_type_v2(schema: Type[Any], pk_field: str) -> Any:
            """Get primary key type - Pydantic V2 compatible."""
            try:
                if hasattr(schema, 'model_fields'):
                    return schema.__annotations__.get(pk_field, int)
                else:
                    return schema.__fields__[pk_field].type_
            except (KeyError, AttributeError):
                return int
        
        utils.get_pk_type = get_pk_type_v2
        
        # Patch schema_factory to work with Pydantic V2
        def schema_factory_v2(schema_cls: Type[Any], pk_field_name: str = "id", name: str = "Create") -> Type[Any]:
            """Create a schema without pk field - Pydantic V2 compatible."""
            from pydantic import create_model
            
            if hasattr(schema_cls, 'model_fields'):
                fields = {
                    f_name: (schema_cls.__annotations__.get(f_name, str), ...)
                    for f_name in schema_cls.model_fields
                    if f_name != pk_field_name
                }
            else:
                fields = {
                    f.name: (f.type_, ...)
                    for f in schema_cls.__fields__.values()
                    if f.name != pk_field_name
                }
            
            model_name = schema_cls.__name__ + name
            schema: Type[Any] = create_model(__model_name=model_name, **fields)  # type: ignore
            return schema
        
        utils.schema_factory = schema_factory_v2
        
        # Patch BaseModel.dict() calls in sqlalchemy module to use model_dump()
        import fastapi_crudrouter.core.sqlalchemy as sqlalchemy_module
        
        # Store original methods
        orig_create = sqlalchemy_module.SQLAlchemyCRUDRouter._create
        orig_update = sqlalchemy_module.SQLAlchemyCRUDRouter._update
        
        # Create wrapper for _create that patches dict() usage
        def create_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            route = orig_create(self, *args, **kwargs)
            
            # Get the route function code and replace dict() with model_dump()
            import functools
            @functools.wraps(route)
            def wrapped_route(model: Any, db: Any) -> Any:
                try:
                    # Use model_dump() if available, else fallback to dict()
                    if hasattr(model, 'model_dump'):
                        db_model = self.db_model(**model.model_dump())
                    else:
                        db_model = self.db_model(**model.dict())
                    
                    db.add(db_model)
                    db.commit()
                    db.refresh(db_model)
                    return db_model
                except Exception as e:
                    db.rollback()
                    if "IntegrityError" in str(type(e).__name__):
                        from fastapi import HTTPException
                        raise HTTPException(422, "Key already exists") from None
                    raise
            
            return wrapped_route
        
        # Create wrapper for _update that patches dict() usage
        def update_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            route = orig_update(self, *args, **kwargs)
            
            import functools
            @functools.wraps(route)
            def wrapped_route(item_id: Any, model: Any, db: Any) -> Any:
                try:
                    db_model = db.query(self.db_model).get(item_id)
                    if not db_model:
                        from fastapi_crudrouter.core import NOT_FOUND
                        raise NOT_FOUND from None
                    
                    # Use model_dump() if available, else fallback to dict()
                    if hasattr(model, 'model_dump'):
                        update_data = model.model_dump(exclude={self._pk})
                    else:
                        update_data = model.dict(exclude={self._pk})
                    
                    for key, value in update_data.items():
                        if hasattr(db_model, key):
                            setattr(db_model, key, value)
                    
                    db.commit()
                    db.refresh(db_model)
                    return db_model
                except Exception as e:
                    db.rollback()
                    if "IntegrityError" in str(type(e).__name__):
                        from fastapi import HTTPException
                        raise HTTPException(422, "Key already exists") from None
                    raise
            
            return wrapped_route
        
        # Apply patches
        sqlalchemy_module.SQLAlchemyCRUDRouter._create = create_wrapper
        sqlalchemy_module.SQLAlchemyCRUDRouter._update = update_wrapper
        
    except ImportError:
        pass
