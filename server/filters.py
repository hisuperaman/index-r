from collections.abc import Sequence

from django.db.models import QuerySet
from rest_framework.filters import OrderingFilter as _OrderingFilter
from rest_framework.request import Request
from rest_framework.views import APIView


class OrderingFilter(_OrderingFilter):
	"""Orders by the requested fields, then by primary key so pages stay stable."""

	def get_ordering(self, request: Request, queryset: QuerySet, view: APIView) -> Sequence[str] | None:
		ordering = super().get_ordering(request, queryset, view)
		if not ordering:
			return ordering

		pk = queryset.model._meta.pk.name
		if {pk, f'-{pk}', 'pk', '-pk'}.isdisjoint(ordering):
			return *ordering, pk
		return ordering
