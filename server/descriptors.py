"""
Reusable model-layer machinery for the abstract base models in server.models.
"""
from django.core.exceptions import FieldDoesNotExist

from enums.Enum import Lookup


class FieldName(str):
	"""
	A model field-name string that also carries the FieldEnum query helpers, so
	``Model.fields.updated_at.desc() == '-updated_at'``. Being a str subclass it
	works anywhere a field name is expected — serializer Meta.fields, order_by(),
	filter lookups — while the methods build the ordering/lookup strings.
	"""

	def asc(self) -> str:
		return str(self)

	def desc(self) -> str:
		return f"-{self}"

	def isnull(self) -> str:
		return Lookup.ISNULL(self)

	def exact(self) -> str:
		return Lookup.EXACT(self)

	def iexact(self) -> str:
		return Lookup.IEXACT(self)

	def icontains(self) -> str:
		return Lookup.ICONTAINS(self)

	def gte(self) -> str:
		return Lookup.GTE(self)

	def lte(self) -> str:
		return Lookup.LTE(self)

	def gt(self) -> str:
		return Lookup.GT(self)

	def lt(self) -> str:
		return Lookup.LT(self)


class _FieldNames:
	"""
	Attribute access to a model's field names, validated against the model:
	``MyModel.fields.name == 'name'``. Unknown names raise AttributeError, so a
	typo in e.g. a serializer's Meta.fields fails at import, not silently.

	Each name comes back as a FieldName (a str), so it carries asc/desc/isnull/…
	helpers like FieldEnum. The IDE can't suggest the field names themselves
	(they're resolved at runtime via _meta), but it does autocomplete those
	helpers on the result. Access needs the app registry ready, so use it from
	serializers/views, not at models.py import time.
	"""

	def __init__(self, model):
		self._model = model

	def __getattr__(self, name: str) -> FieldName:
		try:
			return FieldName(self._model._meta.get_field(name).name)
		except FieldDoesNotExist:
			raise AttributeError(f"{self._model.__name__} has no field '{name}'")


class FieldsDescriptor:
	"""Exposes ``Model.fields.<name>`` on models that set ``fields = FieldsDescriptor()``."""

	def __get__(self, instance, owner) -> _FieldNames:
		return _FieldNames(owner)
