from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='tracker-index'),
    path('add/', views.add_item, name='tracker-add'),
    path('items/', views.item_list, name='tracker-items'),
    path('items/<int:item_id>/edit/', views.edit_item, name='tracker-edit'),
    path("delete/<int:item_id>/", views.delete_item, name="tracker-delete"),
    path('autocomplete/', views.autocomplete_items, name='autocomplete_items'),
]
