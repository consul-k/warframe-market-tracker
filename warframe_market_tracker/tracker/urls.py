from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='tracker-index'),
    path("logout/", views.logout_view, name="logout"),
    path("telegram-auth-check/", views.telegram_auth_check, name="telegram-auth-check"),
    path('add/', views.add_item, name='tracker-add'),
    path('items/', views.item_list, name='tracker-items'),
    path('items/<int:item_id>/edit/', views.edit_item, name='tracker-edit'),
    path("delete/<int:item_id>/", views.delete_item, name="tracker-delete"),
    path('autocomplete/', views.autocomplete_items, name='autocomplete_items'),
    path("link-telegram/", views.link_telegram, name="link-telegram"),
]