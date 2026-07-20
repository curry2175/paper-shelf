from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path

from papers import views as paper_views

def health_check(request):
    return JsonResponse({"ok": True, "service": "paper-shelf"})


urlpatterns = [
    path("health/", health_check, name="health"),
    path("admin/", admin.site.urls),
    path("", paper_views.home, name="home"),
    path("signup/", paper_views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("papers/", include("papers.urls")),
]
