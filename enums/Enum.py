from enum import Enum


class Lookup(Enum):
	ISNULL = 'isnull'
	EXACT = 'exact'
	IEXACT = 'iexact'
	ICONTAINS = 'icontains'
	IN = 'in'
	GTE = 'gte'
	LTE = 'lte'
	GT = 'gt'
	LT = 'lt'

	def __call__(self, field: str) -> str:
		return f"{field}__{self.value}"


class FieldEnum(Enum):

	def asc(self) -> str:
		return self.value

	def desc(self) -> str:
		return f"-{self.value}"

	def isnull(self) -> str:
		return Lookup.ISNULL.__call__(self.value)

	def exact(self) -> str:
		return Lookup.EXACT.__call__(self.value)

	def iexact(self) -> str:
		return Lookup.IEXACT.__call__(self.value)

	def icontains(self) -> str:
		return Lookup.ICONTAINS.__call__(self.value)

	def gte(self) -> str:
		return Lookup.GTE.__call__(self.value)

	def lte(self) -> str:
		return Lookup.LTE.__call__(self.value)

	def gt(self) -> str:
		return Lookup.GT.__call__(self.value)

	def lt(self) -> str:
		return Lookup.LT.__call__(self.value)

	@classmethod
	def values(cls) -> list:
		return [field.value for field in cls]
