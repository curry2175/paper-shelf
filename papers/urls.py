from django.urls import path

from . import views

app_name = "papers"

urlpatterns = [
    path("search/", views.search_papers, name="search"),
    path("bookshelf/", views.bookshelf, name="bookshelf"),
    path("extension/", views.extension_settings, name="extension_settings"),
    path("extension/token/generate/", views.generate_extension_token, name="generate_extension_token"),
    path("extension/token/revoke/", views.revoke_extension_token_view, name="revoke_extension_token"),
    path("api/reading-records/", views.api_save_reading_record, name="api_save_reading_record"),
    path("<int:pk>/", views.paper_detail, name="detail"),
    path("<int:pk>/summarize/", views.generate_summary, name="summarize"),
    path("<int:pk>/mark-read/", views.mark_read, name="mark_read"),
    path("<int:pk>/reading/update/", views.update_reading_record, name="update_reading"),
    path("<int:pk>/reading/remove/", views.remove_reading_record, name="remove_reading"),
]
