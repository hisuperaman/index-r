from django.db import models
from server.models import BaseModel  # Assuming BaseModel gives you 'id', 'created_at', 'updated_at'

class Paper(BaseModel):
    title = models.CharField(max_length=500)  # Titles can be long
    authors = models.CharField(max_length=500, blank=True, null=True)  # Optional
    abstract = models.TextField(blank=True, null=True)  # Large text, optional
    pdf_url = models.URLField(max_length=500)  # The link to the PDF file
    publication_date = models.DateField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']  # Show newest first

    def __str__(self):
        return self.title


class Chunk(BaseModel):
    # ForeignKey links each Chunk to exactly one Paper
    paper = models.ForeignKey(
        Paper, 
        on_delete=models.CASCADE,  # If Paper is deleted, delete all its Chunks
        related_name='chunks'      # Allows you to do paper.chunks.all()
    )
    text = models.TextField()  # The actual text extracted from this chunk
    page_number = models.IntegerField()
    chunk_index = models.IntegerField()  # To know order (1, 2, 3...)
    
    class Meta:
        ordering = ['chunk_index', 'page_number']
        unique_together = ['paper', 'chunk_index']  # Prevents duplicate chunk numbers

    def __str__(self):
        return f"Chunk {self.chunk_index} - {self.paper.title[:30]}"