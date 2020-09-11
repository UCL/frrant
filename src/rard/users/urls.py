from django.urls import path

from rard.users.views import user_detail_view, user_update_view

app_name = "users"
urlpatterns = [
    path("update-profile/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
