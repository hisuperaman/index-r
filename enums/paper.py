from django.db.models import TextChoices
class SourceType(TextChoices):
    ARXIV = "arxiv", "arXiv"
    SEMANTIC_SCHOLAR = "semantic_scholar", "Semantic Scholar"
    OPENALEX = "openalex", "OpenAlex"