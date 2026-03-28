from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="tracker-index"),

    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("items/", views.item_list, name="tracker-items"),
    path("add/", views.add_item, name="tracker-add"),
    path("edit/<int:item_id>/", views.edit_item, name="tracker-edit"),
    path("delete/<int:item_id>/", views.delete_item, name="tracker-delete"),

    path("check-prices/", views.check_prices_now, name="tracker-check-prices"),

    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:pk>/read/", views.mark_notification_read, name="mark-notification-read"),

    path("autocomplete/", views.autocomplete_items, name="autocomplete"),

    path("profile/", views.profile, name="tracker-profile"),

    path("notifications/unread-count/", views.unread_notifications_count_api),
    path("notifications/latest/", views.latest_notifications, name="latest-notifications"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="mark-all-read"),
]