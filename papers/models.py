from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Paper(models.Model):
    pmid = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.TextField()
    authors = models.TextField(blank=True)
    journal = models.CharField(max_length=500, blank=True)
    publication_date = models.CharField(max_length=100, blank=True)
    doi = models.CharField(max_length=255, blank=True)
    pubmed_url = models.URLField(max_length=500, blank=True)
    abstract = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title[:100]


class PaperSummary(models.Model):
    STATUS_CHOICES = [("success", "성공"), ("failed", "실패")]

    paper = models.OneToOneField(
        Paper, related_name="summary", on_delete=models.CASCADE
    )
    research_question = models.TextField(blank=True)
    why_it_matters = models.TextField(blank=True)
    study_design = models.TextField(blank=True)
    study_population = models.TextField(blank=True)
    main_results = models.JSONField(default=list, blank=True)
    easy_explanation = models.TextField(blank=True)
    limitations = models.JSONField(default=list, blank=True)
    beginner_takeaway = models.TextField(blank=True)
    difficult_terms = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=100, default="PubMed Abstract")
    model_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="success")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.paper.pmid} 요약"


class ReadingRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reading_records",
        on_delete=models.CASCADE,
    )
    paper = models.ForeignKey(
        Paper, related_name="reading_records", on_delete=models.CASCADE
    )
    read_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    source_url = models.URLField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-read_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "paper"], name="unique_user_read_paper"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.paper.pmid}"


class SearchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="search_history",
        on_delete=models.CASCADE,
    )
    keyword = models.CharField(max_length=500)
    days = models.PositiveIntegerField(default=7)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-searched_at"]

    def __str__(self):
        return f"{self.user}: {self.keyword}"


class ExtensionToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="extension_token",
        on_delete=models.CASCADE,
    )
    selector = models.CharField(max_length=32, unique=True, db_index=True)
    verifier_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} extension token"
