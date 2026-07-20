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
    path("account/recovery/", paper_views.account_recovery, name="account_recovery"),
    path(
        "account/recovery/username/",
        paper_views.username_recovery,
        name="username_recovery",
    ),
    path(
        "account/recovery/username/done/",
        paper_views.username_recovery_done,
        name="username_recovery_done",
    ),
    path(
        "account/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
            success_url="/account/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "account/password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "account/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url="/account/reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "account/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("papers/", include("papers.urls")),
]
