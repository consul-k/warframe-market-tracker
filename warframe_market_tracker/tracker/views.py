from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import TrackedItem, MarketItem
from .forms import TrackedItemForm
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TelegramAuthToken
from django.contrib.auth import login, logout


def index(request):
    if request.user.is_authenticated:
        return redirect("tracker-items")
    return render(request, "tracker/index.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("tracker-index")


@login_required
def item_list(request):
    items = TrackedItem.objects.filter(user=request.user)
    return render(request, "tracker/item_list.html", {"items": items})


@login_required
def add_item(request):
    if request.method == "POST":
        form = TrackedItemForm(request.POST, initial={"user": request.user})

        if form.is_valid():
            name = form.cleaned_data.get("name", "").strip()
            item_url_name = form.cleaned_data.get("item_url_name", "").strip()

            # --- Проверяем предмет ---
            if item_url_name:
                mi = MarketItem.objects.filter(item_url_name=item_url_name).first()
            else:
                mi = MarketItem.objects.filter(item_name__iexact=name).first()

            if not mi:
                form.add_error("name", "Выберите предмет из списка подсказок.")
                return render(request, "tracker/add_item.html", {"form": form})

            obj = form.save(commit=False)
            obj.item_url_name = mi.item_url_name
            obj.name = mi.item_name

            # --- Ранг ---
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
        form = TrackedItemForm(initial={"user": request.user})

    return render(request, "tracker/add_item.html", {"form": form})


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(TrackedItem, id=item_id, user=request.user)

    if request.method == "POST":
        form = TrackedItemForm(request.POST, instance=item, initial={"user": request.user})

        if form.is_valid():
            item.target_price = form.cleaned_data.get("target_price")

            item_url_name = item.item_url_name
            rank_choice = request.POST.get("rank_choice")

            market_item = MarketItem.objects.filter(item_url_name=item_url_name).first()
            rank_changed_message = None

            if rank_choice and market_item:

                if rank_choice == "min":
                    if item.max_rank != 0:
                        rank_changed_message = "Отслеживаемый ранг изменён на <b>Минимальный</b>."
                    item.min_rank = 0
                    item.max_rank = 0

                elif rank_choice == "max":
                    if item.max_rank != market_item.max_rank:
                        rank_changed_message = "Отслеживаемый ранг изменён на <b>Максимальный</b>."
                    item.min_rank = market_item.max_rank
                    item.max_rank = market_item.max_rank

            item.save()

            if rank_changed_message:
                messages.success(request, f"Изменения сохранены. {rank_changed_message}")
            else:
                messages.success(request, "Изменения сохранены.")

            return redirect("tracker-items")

        else:
            messages.error(request, "Исправьте ошибки в форме.")

    else:
        form = TrackedItemForm(instance=item, initial={"user": request.user})

    market_item = MarketItem.objects.filter(item_url_name=item.item_url_name).first()

    return render(
        request,
        "tracker/edit_item.html",
        {
            "form": form,
            "item": item,
            "market_item": market_item
        }
    )


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(TrackedItem, id=item_id, user=request.user)
    item.delete()
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
    return render(request, "tracker/profile.html")


def telegram_auth_check(request):
    token_value = request.session.get("telegram_auth_token")

    if not token_value:
        return redirect("tracker-index")

    try:
        token = TelegramAuthToken.objects.select_related(
            "telegram_profile__user"
        ).get(token=token_value, is_used=True)

    except TelegramAuthToken.DoesNotExist:
        return render(request, "tracker/waiting.html")

    if not token.telegram_profile or not token.telegram_profile.user:
        return render(request, "tracker/waiting.html")

    user = token.telegram_profile.user
    login(request, user)

    del request.session["telegram_auth_token"]

    return redirect("tracker-items")


def link_telegram(request):

    if request.user.is_authenticated:
        return redirect("tracker-items")

    auth_token = TelegramAuthToken.objects.create()

    request.session["telegram_auth_token"] = str(auth_token.token)

    bot_username = "wm_price_tracker_bot"

    telegram_link = f"https://t.me/{bot_username}?start={auth_token.token}"

    return render(
        request,
        "tracker/waiting.html",
        {
            "telegram_link": telegram_link
        },
    )