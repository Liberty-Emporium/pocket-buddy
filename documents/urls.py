from django.urls import path

from . import views

urlpatterns = [
    # Secretary
    path("files/", views.secretary_list, name="secretary_list"),
    path("upload/", views.upload, name="upload"),
    # Boss
    path("feed/", views.boss_feed, name="boss_feed"),
    # Shared
    path("doc/<int:pk>/", views.document_detail, name="document_detail"),
    path("doc/<int:pk>/file/", views.document_serve, name="document_serve"),
    path("doc/<int:pk>/comment/", views.document_comment, name="document_comment"),
    path("doc/<int:pk>/handle/", views.document_handle, name="document_handle"),
]
