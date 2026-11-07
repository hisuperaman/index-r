from rest_framework.pagination import CursorPagination as _CursorPagination


class CursorPagination(_CursorPagination):
	"""Cursor pagination whose page size the caller may lower or raise up to a cap."""
	page_size_query_param = 'page_size'
	max_page_size = 100
