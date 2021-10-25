from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views import defaults as default_views

admin.autodiscover()
admin.site.login = login_required(admin.site.login)

base_urlpatterns = [
    path("users/", include("rard.users.urls", namespace="users")),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(
            html_email_template_name="registration/password_reset_email.html"
        ),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    # research urls
    path("", include("rard.research.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    base_urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        base_urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls))
        ] + base_urlpatterns

prefix = getattr(settings, "URL_PREFIX", "")


urlpatterns = [path("{}".format(prefix), include((base_urlpatterns)))]
