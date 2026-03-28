from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.views.decorators.http import require_GET
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import TrackedItem, MarketItem, Notification
from .forms import TrackedItemForm
from tracker.services.market_api import get_item_prices


def get_unread_count(request):
    if request.user.is_authenticated:
        return request.user.notifications.filter(is_read=False).count()
    return 0


def index(request):
    if request.user.is_authenticated:
        return redirect("tracker-items")

    return render(request, "tracker/index.html", {
        "unread_notifications_count": 0
    })


@login_required
def logout_view(request):
    logout(request)
    return redirect("tracker-index")


@login_required
def item_list(request):
    items = TrackedItem.objects.filter(user=request.user)

    return render(request, "tracker/item_list.html", {
        "items": items,
        "unread_notifications_count": get_unread_count(request)
    })


@login_required
def add_item(request):
    if request.method == "POST":
        form = TrackedItemForm(request.POST, user=request.user)

        if form.is_valid():
            name = form.cleaned_data.get("name", "").strip()
            item_url_name = form.cleaned_data.get("item_url_name", "").strip()

            if item_url_name:
                mi = MarketItem.objects.filter(item_url_name=item_url_name).first()
            else:
                mi = MarketItem.objects.filter(item_name__iexact=name).first()

            if not mi:
                form.add_error("name", "Выберите предмет из списка подсказок.")
                return render(request, "tracker/add_item.html", {
                    "form": form,
                    "unread_notifications_count": get_unread_count(request)
                })

            obj = form.save(commit=False)
            obj.item_url_name = mi.item_url_name
            obj.name = mi.item_name

            rank_choice = request.POST.get("rank_choice", "max")

            if mi.max_rank and mi.max_rank > 0:
                if rank_choice == "min":
                    obj.min_rank = 0
                    obj.max_rank = 0
                else:
                    obj.min_rank = mi.max_rank
                    obj.max_rank = mi.max_rank
            else:
                obj.min_rank = None
                obj.max_rank = None

            obj.user = request.user
            obj.save()

            messages.success(request, "Предмет успешно добавлен!")
            return redirect("tracker-items")

        messages.error(request, "Проверьте введённые данные.")

    else:
        form = TrackedItemForm(user=request.user)

    return render(request, "tracker/add_item.html", {
        "form": form,
        "unread_notifications_count": get_unread_count(request)
    })


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(TrackedItem, id=item_id, user=request.user)

    if request.method == "POST":
        form = TrackedItemForm(request.POST, instance=item, user=request.user)

        if form.is_valid():
            item.target_price = form.cleaned_data.get("target_price")

            rank_choice = request.POST.get("rank_choice")
            market_item = MarketItem.objects.filter(item_url_name=item.item_url_name).first()

            if rank_choice and market_item:
                if rank_choice == "min":
                    item.min_rank = 0
                    item.max_rank = 0
                elif rank_choice == "max":
                    item.min_rank = market_item.max_rank
                    item.max_rank = market_item.max_rank

            item.save()
            messages.success(request, "Изменения сохранены.")
            return redirect("tracker-items")

        messages.error(request, "Исправьте ошибки в форме.")

    else:
        form = TrackedItemForm(instance=item, user=request.user)

    market_item = MarketItem.objects.filter(item_url_name=item.item_url_name).first()

    return render(request, "tracker/edit_item.html", {
        "form": form,
        "item": item,
        "market_item": market_item,
        "unread_notifications_count": get_unread_count(request)
    })


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(TrackedItem, id=item_id, user=request.user)
    item.delete()
    messages.success(request, "Предмет удалён.")
    return redirect("tracker-items")


@require_GET
def autocomplete_items(request):
    q = request.GET.get("q", "").strip()

    results = []

    if len(q) >= 2:
        qs = MarketItem.objects.filter(
            item_name__icontains=q
        ).order_by("item_name")[:12]

        results = [
            {
                "name": item.item_name,
                "url": item.item_url_name,
                "max_rank": item.max_rank,
            }
            for item in qs
        ]

    return JsonResponse(results, safe=False)


@login_required
def profile(request):
    items_count = TrackedItem.objects.filter(user=request.user).count()

    return render(request, "tracker/profile.html", {
        "items_count": items_count,
        "unread_notifications_count": get_unread_count(request)
    })

@login_required
def check_prices_now(request):
    items = TrackedItem.objects.filter(user=request.user)

    updated = 0

    for item in items:
        try:
            rank = item.max_rank if item.max_rank is not None else None
            min_price, avg_price = get_item_prices(item.item_url_name, rank)

            item.last_min_price = min_price
            item.last_avg_price = avg_price
            item.save(update_fields=["last_min_price", "last_avg_price"])

            updated += 1

        except Exception:
            continue

    messages.success(request, f"Обновлено цен для {updated} предметов.")
    return redirect("tracker-items")


@login_required
def notifications_view(request):
    notifications = request.user.notifications.order_by("-created_at")

    return render(request, "tracker/notifications.html", {
        "notifications": notifications,
        "unread_notifications_count": get_unread_count(request)
    })


@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    return redirect("notifications")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("tracker-items")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("tracker-items")
    else:
        form = UserCreationForm()

    return render(request, "tracker/register.html", {
        "form": form,
        "unread_notifications_count": 0
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("tracker-items")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("tracker-items")
    else:
        form = AuthenticationForm()

    return render(request, "tracker/login.html", {
        "form": form,
        "unread_notifications_count": 0
    })

@login_required
def unread_notifications_count_api(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({"count": count})

@login_required
def latest_notifications(request):
    notifications = request.user.notifications.filter(
        is_read=False
    ).order_by("-created_at")[:5]

    data = [
        {
            "id": n.id,
            "text": n.text,
        }
        for n in notifications
    ]

    return JsonResponse(data, safe=False)

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("notifications")