from django.contrib import admin

from .models import ExtensionToken, Paper, PaperSummary, ReadingRecord, SearchHistory


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("pmid", "short_title", "journal", "publication_date")
    search_fields = ("pmid", "title", "doi", "journal")

    @admin.display(description="제목")
    def short_title(self, obj):
        return obj.title[:80]


@admin.register(PaperSummary)
class PaperSummaryAdmin(admin.ModelAdmin):
    list_display = ("paper", "status", "model_name", "updated_at")
    search_fields = ("paper__pmid", "paper__title")


@admin.register(ReadingRecord)
class ReadingRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "paper", "read_at", "rating")
    list_filter = ("read_at", "rating")
    search_fields = ("user__username", "paper__title", "paper__pmid")


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "keyword", "days", "searched_at")
    search_fields = ("user__username", "keyword")


@admin.register(ExtensionToken)
class ExtensionTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "selector", "created_at", "last_used_at")
    search_fields = ("user__username", "user__email", "selector")
    readonly_fields = ("verifier_digest", "created_at", "last_used_at")
