from django.contrib import admin

from enums.Paper import PaperLookup
from papers.models import Author, Paper, PaperAuthor


class VisibilityFilter(admin.SimpleListFilter):
	title = "visibility"
	parameter_name = "visibility"

	def lookups(self, request, model_admin):
		return [("public", "Shared corpus"), ("private", "Private uploads")]

	def queryset(self, request, queryset):
		if self.value() == "public":
			return queryset.public()
		if self.value() == "private":
			return queryset.filter(**{Paper.fields.owner.isnull(): False})
		return queryset


class PaperAuthorInline(admin.TabularInline):
	model = PaperAuthor
	fields = [PaperAuthor.fields.order, PaperAuthor.fields.author]
	readonly_fields = fields
	extra = 0
	can_delete = False


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
	list_display = [
		Paper.fields.title, Paper.fields.source, Paper.fields.owner, PaperLookup.ingestion_status.value,
		Paper.fields.citation_count, Paper.fields.publication_date, Paper.fields.created_at,
	]
	list_filter = [VisibilityFilter, Paper.fields.source]
	search_fields = [Paper.fields.title, Paper.fields.doi, Paper.fields.external_id]
	list_select_related = [Paper.fields.owner]
	ordering = [Paper.fields.created_at.desc()]
	inlines = [PaperAuthorInline]

	def get_readonly_fields(self, request, obj=None):
		return [field.name for field in Paper._meta.fields] + [PaperLookup.ingestion_status.value]

	def has_add_permission(self, request):
		return False


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
	list_display = [Author.fields.name, Author.fields.orcid]
	search_fields = [Author.fields.name, Author.fields.orcid]
	ordering = [Author.fields.name]
