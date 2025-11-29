from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from tracker.forms import CustomSetPasswordForm

urlpatterns = [
    path('', views.index, name='tracker-index'),
    path('add/', views.add_item, name='tracker-add'),
    path('items/', views.item_list, name='tracker-items'),
    path('items/<int:item_id>/edit/', views.edit_item, name='tracker-edit'),
    path("delete/<int:item_id>/", views.delete_item, name="tracker-delete"),
    path('autocomplete/', views.autocomplete_items, name='autocomplete_items'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('auth/password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('auth/password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),

    path('auth/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(form_class=CustomSetPasswordForm), name='password_reset_confirm'),
    
    path('auth/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]