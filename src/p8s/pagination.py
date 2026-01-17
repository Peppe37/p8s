"""
P8s Pagination - Django-style pagination for querysets and lists.

Provides:
- Paginator class
- Page class
- Pagination utilities
"""

import math
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class InvalidPage(Exception):
    """Exception for invalid page number."""

    pass


class PageNotAnInteger(InvalidPage):
    """Page is not an integer."""

    pass


class EmptyPage(InvalidPage):
    """Page is empty (no items)."""

    pass


class Paginator(Generic[T]):
    """
    Django-style paginator for sequences.

    Example:
        ```python
        from p8s.pagination import Paginator

        items = await session.execute(select(Product))
        paginator = Paginator(items.scalars().all(), per_page=10)

        page = paginator.page(1)
        for item in page:
            print(item.name)

        print(f"Page {page.number} of {paginator.num_pages}")
        ```
    """

    def __init__(
        self,
        object_list: Sequence[T],
        per_page: int = 10,
        orphans: int = 0,
        allow_empty_first_page: bool = True,
    ) -> None:
        """
        Initialize paginator.

        Args:
            object_list: List of objects to paginate.
            per_page: Maximum items per page.
            orphans: Minimum items for the last page (prevents tiny last pages).
            allow_empty_first_page: Allow page 1 even if no items.
        """
        self.object_list = list(object_list)
        self.per_page = per_page
        self.orphans = orphans
        self.allow_empty_first_page = allow_empty_first_page

    @property
    def count(self) -> int:
        """Total number of items."""
        return len(self.object_list)

    @property
    def num_pages(self) -> int:
        """Total number of pages."""
        if self.count == 0:
            return 1 if self.allow_empty_first_page else 0

        hits = max(1, self.count - self.orphans)
        return math.ceil(hits / self.per_page)

    @property
    def page_range(self) -> range:
        """Range of valid page numbers."""
        return range(1, self.num_pages + 1)

    def validate_number(self, number: Any) -> int:
        """
        Validate and return page number as integer.

        Args:
            number: Page number to validate.

        Returns:
            Valid page number.

        Raises:
            PageNotAnInteger: If number is not an integer.
            EmptyPage: If page number is invalid.
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger("Page number must be an integer")

        if number < 1:
            raise EmptyPage("Page number must be 1 or greater")

        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage(f"Page {number} contains no results")

        return number

    def page(self, number: Any) -> "Page[T]":
        """
        Get a Page object for the given page number.

        Args:
            number: Page number (1-indexed).

        Returns:
            Page object.
        """
        number = self.validate_number(number)

        start = (number - 1) * self.per_page
        end = start + self.per_page

        # Handle orphans
        if end + self.orphans >= self.count:
            end = self.count

        return Page(self.object_list[start:end], number, self)

    def get_elided_page_range(
        self,
        number: int,
        on_each_side: int = 3,
        on_ends: int = 2,
    ) -> list[int | str]:
        """
        Get page range with ellipsis for large page counts.

        Example: [1, 2, '...', 8, 9, 10, 11, 12, '...', 99, 100]

        Args:
            number: Current page number.
            on_each_side: Pages to show on each side of current.
            on_ends: Pages to show at start and end.

        Returns:
            List of page numbers and ellipsis strings.
        """
        if self.num_pages <= (on_each_side + on_ends) * 2:
            return list(self.page_range)

        pages = []

        # Start pages
        pages.extend(range(1, on_ends + 1))

        # Middle pages around current
        left = max(on_ends + 1, number - on_each_side)
        right = min(self.num_pages - on_ends, number + on_each_side)

        if left > on_ends + 1:
            pages.append("...")

        pages.extend(range(left, right + 1))

        if right < self.num_pages - on_ends:
            pages.append("...")

        # End pages
        pages.extend(range(self.num_pages - on_ends + 1, self.num_pages + 1))

        return pages


class Page(Generic[T]):
    """
    A single page of paginated results.

    Supports iteration and indexing.
    """

    def __init__(
        self,
        object_list: list[T],
        number: int,
        paginator: Paginator[T],
    ) -> None:
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __repr__(self) -> str:
        return f"<Page {self.number} of {self.paginator.num_pages}>"

    def __len__(self) -> int:
        return len(self.object_list)

    def __iter__(self):
        return iter(self.object_list)

    def __getitem__(self, index: int) -> T:
        return self.object_list[index]

    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.number < self.paginator.num_pages

    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.number > 1

    def has_other_pages(self) -> bool:
        """Check if there are other pages."""
        return self.has_next() or self.has_previous()

    def next_page_number(self) -> int:
        """Get next page number."""
        if not self.has_next():
            raise EmptyPage("No next page")
        return self.number + 1

    def previous_page_number(self) -> int:
        """Get previous page number."""
        if not self.has_previous():
            raise EmptyPage("No previous page")
        return self.number - 1

    def start_index(self) -> int:
        """Get 1-based index of first item on this page."""
        if self.paginator.count == 0:
            return 0
        return (self.number - 1) * self.paginator.per_page + 1

    def end_index(self) -> int:
        """Get 1-based index of last item on this page."""
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page


# FastAPI integration


def paginate_query(
    items: Sequence[T],
    page: int = 1,
    per_page: int = 10,
) -> dict[str, Any]:
    """
    Paginate items and return response dict.

    Useful for API endpoints.

    Example:
        ```python
        from p8s.pagination import paginate_query

        @app.get("/products")
        async def list_products(page: int = 1, per_page: int = 10):
            products = await get_all_products()
            return paginate_query(products, page, per_page)
        ```

    Returns:
        {
            "items": [...],
            "page": 1,
            "per_page": 10,
            "total": 100,
            "pages": 10,
            "has_next": True,
            "has_previous": False,
        }
    """
    paginator = Paginator(items, per_page=per_page)

    try:
        page_obj = paginator.page(page)
    except InvalidPage:
        page_obj = paginator.page(1)

    return {
        "items": list(page_obj),
        "page": page_obj.number,
        "per_page": per_page,
        "total": paginator.count,
        "pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
    }


async def async_paginate(
    session: Any,
    query: Any,
    page: int = 1,
    per_page: int = 10,
) -> dict[str, Any]:
    """
    Paginate an async SQLAlchemy query and return response dict.

    This executes the query with LIMIT/OFFSET for efficient pagination
    and also counts total items.

    Example:
        ```python
        from p8s.pagination import async_paginate
        from sqlmodel import select

        @app.get("/products")
        async def list_products(
            session: AsyncSession = Depends(get_session),
            page: int = 1,
            per_page: int = 10,
        ):
            query = select(Product).where(Product.is_active == True)
            return await async_paginate(session, query, page, per_page)
        ```

    Args:
        session: SQLAlchemy AsyncSession.
        query: SQLAlchemy Select query.
        page: Page number (1-indexed).
        per_page: Items per page.

    Returns:
        {
            "items": [...],
            "page": 1,
            "per_page": 10,
            "total": 100,
            "pages": 10,
            "has_next": True,
            "has_previous": False,
        }
    """
    from sqlalchemy import func
    from sqlalchemy import select as sa_select

    # Ensure valid page number
    if page < 1:
        page = 1

    # Calculate offset
    offset = (page - 1) * per_page

    # Get total count
    # Extract the model from the query's column_descriptions
    count_query = sa_select(func.count()).select_from(query.subquery())
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination to query
    paginated_query = query.offset(offset).limit(per_page)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    # Calculate pages
    pages = math.ceil(total / per_page) if per_page > 0 else 1
    if pages == 0:
        pages = 1

    return {
        "items": list(items),
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_previous": page > 1,
    }
