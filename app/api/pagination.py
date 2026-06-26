from typing import Any, List, Dict, Optional
from fastapi import Query
from pydantic import BaseModel

class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=10, ge=1, le=100, alias="page_size", description="Number of items per page"),
        limit: Optional[int] = Query(default=None, ge=1, description="Limit count (overrides page/page_size if set)"),
        offset: Optional[int] = Query(default=None, ge=0, description="Offset count (overrides page/page_size if set)"),
        sorting: Optional[str] = Query(default=None, description="Sort field. Use +/- prefix, e.g. +name or -score")
    ):
        self.page = page
        self.page_size = page_size
        self.limit = limit
        self.offset = offset
        self.sorting = sorting

def paginate_list(
    items: List[Any],
    params: PaginationParams,
    default_sort_key: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to sort and paginate a list of items based on PaginationParams."""
    # 1. Apply Sorting
    sort_field = params.sorting or default_sort_key
    if sort_field and items:
        reverse = False
        if sort_field.startswith("-"):
            reverse = True
            sort_field = sort_field[1:]
        elif sort_field.startswith("+"):
            sort_field = sort_field[1:]
        
        # Sort items safely
        try:
            items = sorted(
                items,
                key=lambda x: getattr(x, sort_field, x.get(sort_field) if isinstance(x, dict) else None) or "",
                reverse=reverse
            )
        except Exception:
            pass  # Fail-safe if sorting field doesn't exist

    total_count = len(items)

    # 2. Slice items
    if params.limit is not None or params.offset is not None:
        start = params.offset or 0
        end = start + (params.limit or total_count)
        sliced_items = items[start:end]
        page = (start // params.page_size) + 1 if params.page_size else 1
        page_size = params.page_size
    else:
        start = (params.page - 1) * params.page_size
        end = start + params.page_size
        sliced_items = items[start:end]
        page = params.page
        page_size = params.page_size

    total_pages = (total_count + page_size - 1) // page_size if page_size else 1

    metadata = {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

    return {
        "items": sliced_items,
        "pagination": metadata
    }
