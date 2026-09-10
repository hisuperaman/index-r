from enums.paper import SourceType
from django.core.validators import MinValueValidator, MaxValueValidator 
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.db.models import (
    CharField, TextField, DateField, 
    ForeignKey, ManyToManyField, PositiveIntegerField,PositiveSmallIntegerField, 
    BooleanField,JSONField,Index, Q,F,CheckConstraint,UniqueConstraint, CASCADE,
)
from server.models import BaseModel
  
class Author(BaseModel):
    # The core information
    name = CharField(max_length=255)
    orcid = CharField(max_length=19, blank=True, null=True, unique=True)
    affiliation = CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Paper(BaseModel):
    source = CharField(max_length=50, choices=SourceType.choices, db_index=True)
    external_id = CharField(max_length=255)

    title = TextField()  
    abstract = TextField(blank=True, null=True)  
    pdf_url = TextField()  
    publication_date  = DateField(blank=True, null=True)
    publication_month = PositiveSmallIntegerField(blank=True, null=True,choices=[(i, i) for i in range(1, 13)], )
    publication_year = PositiveSmallIntegerField(
    blank=True, null=True,
    validators=[MinValueValidator(1900), MaxValueValidator(2100)],)
    authors = ManyToManyField(
        Author,
        through="PaperAuthor",
        related_name="papers",
    )
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["source", "external_id"],
                name="unique_source_external_id",
            ),
        ]
        indexes = [
            Index(fields=["-publication_year", "-publication_month","-publication_date"]),
        ]

    def __str__(self):
        return f"[{self.source}] {self.title[:50]}"

class PaperAuthor(BaseModel):
    paper = ForeignKey(Paper, on_delete=CASCADE, related_name="paper_authors")
    author = ForeignKey(Author, on_delete=CASCADE, related_name="author_credits")
    order = PositiveIntegerField(validators=[MinValueValidator(1)])
    is_corresponding = BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["paper", "author"],
                name="unique_paper_author",
            ),
            UniqueConstraint(
                fields=["paper", "order"],          
                name="unique_paper_author_order",
            ),
        ]
       
    def __str__(self):
        return f"{self.author.name} (#{self.order}) on {self.paper.title[:30]}"

class Chunk(BaseModel):
    paper = ForeignKey(
        Paper,
        on_delete=CASCADE,
        related_name="chunks",     
    )
    heading = CharField(max_length=500, blank=True, null=True)
    text = TextField() 
    search_vector = SearchVectorField(null=True, blank=True)            

    start_page = PositiveIntegerField()                
    end_page = PositiveIntegerField()                  
    page_labels = JSONField(default=list, blank=True)  # Printed labels like ["112", "113"]

    chunk_index = PositiveIntegerField()               # Position of chunk within the paper

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["paper", "chunk_index"],
                name="unique_paper_chunk_index",
            ),
            CheckConstraint(
            condition=Q(end_page__gte=F("start_page")),
            name="chunk_end_page_gte_start_page",
        ),

        ]
        indexes = [
            Index(fields=["paper", "start_page"]),
            Index(fields=["paper", "end_page"]),
            GinIndex(fields=["search_vector"], name="chunk_search_vector_gin"),
        ]

    def __str__(self):
        if self.start_page == self.end_page:
            return f"Chunk {self.chunk_index} (p.{self.start_page})"
        return f"Chunk {self.chunk_index} (pp.{self.start_page}–{self.end_page})"
