from uuid import uuid4

from django.db.models import Model, UUIDField, DateTimeField

from server.descriptors import FieldsDescriptor


class BaseModel(Model):
	created_at = DateTimeField(auto_now_add=True, editable=False)
	updated_at = DateTimeField(auto_now=True)

	# Adds the `Model.fields.<name>` accessor. BaseModel includes it; mix it into
	# models that can't inherit BaseModel (e.g. a model keyed on another field, or
	# one outside our base hierarchy) to get the same accessor with no schema change.
	fields = FieldsDescriptor()

	class Meta:
		abstract = True

	def __repr__(self) -> str:
		return self.__str__()

	@classmethod
	def get_editable_fields(cls) -> list:
		return list(filter(lambda field: field.editable, cls._meta.get_fields()))

	@classmethod
	def get_unique_fields(cls) -> list:
		return list(
			filter(lambda field: field.unique and not field.many_to_many, cls.get_editable_fields())
		)

	@classmethod
	def get_unique_fields_name(cls) -> list[str]:
		return list(map(lambda field: field.name, cls.get_unique_fields()))

	@classmethod
	def get_non_unique_fields(cls) -> list:
		return list(
			filter(lambda field: not (field.unique or field.many_to_many or field.primary_key),
				   cls.get_editable_fields())
		)

	@classmethod
	def get_non_unique_fields_name(cls) -> list[str]:
		return list(map(lambda field: field.name, cls.get_non_unique_fields()))


class PrimaryModel(BaseModel):
	id = UUIDField(primary_key=True, default=uuid4, editable=False)

	class Meta:
		abstract = True

	def __str__(self):
		return str(self.id)

	def get_id(self):
		return str(self.id)
