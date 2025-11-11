from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import TrackedItem, MarketItem
from .forms import TrackedItemForm
from django.views.decorators.http import require_GET
from django.contrib import messages

def index(request):
    return render(request, "tracker/index.html")

def item_list(request):
    items = TrackedItem.objects.all()
    return render(request, "tracker/item_list.html", {"items": items})

def add_item(request):
    if request.method == "POST":
        form = TrackedItemForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data.get("name", "").strip()
            item_url_name = form.cleaned_data.get("item_url_name", "").strip()

            # --- 1. Проверяем, что предмет выбран через autocomplete ---
            mi = None
            if item_url_name:
                mi = MarketItem.objects.filter(item_url_name=item_url_name).first()
            else:
                mi = MarketItem.objects.filter(item_name__iexact=name).first()

            if not mi:
                form.add_error("name", "Выберите предмет из списка подсказок.")
                return render(request, "tracker/add_item.html", {"form": form})

            # --- 2. Создаем объект, но не сохраняем ---
            obj = form.save(commit=False)
            obj.item_url_name = mi.item_url_name
            obj.name = mi.item_name   # гарантируем корректное имя

            # --- 3. Обрабатываем выбор ранга ---
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

            # --- 4. Сохраняем ---
            obj.save()

            messages.success(request, "Предмет успешно добавлен!")
            return redirect("tracker-items")

        messages.error(request, "Проверьте введённые данные.")
    else:
        form = TrackedItemForm()

    return render(request, "tracker/add_item.html", {"form": form})

def edit_item(request, item_id):
    item = get_object_or_404(TrackedItem, id=item_id)

    if request.method == "POST":
        form = TrackedItemForm(request.POST, instance=item)
        if form.is_valid():
            # Название и URL не редактируем вручную
            name = item.name
            item_url_name = item.item_url_name

            # Обновляем только редактируемые поля
            item.target_price = form.cleaned_data.get("target_price")
            item.chat_id = form.cleaned_data.get("chat_id")

            # --- Проверяем выбор ранга
            rank_choice = request.POST.get("rank_choice")  # может быть 'min' или 'max'
            market_item = MarketItem.objects.filter(item_url_name=item_url_name).first()
            rank_changed_message = None  # сообщение для пользователя

            if rank_choice and market_item:
                if rank_choice == "min":
                    if item.max_rank != 0:  # чтобы не показывать сообщение без необходимости
                        rank_changed_message = "Отслеживаемый ранг изменён на <b>Минимальный</b>."
                    item.min_rank = 0
                    item.max_rank = 0

                elif rank_choice == "max":
                    if item.max_rank != market_item.max_rank:
                        rank_changed_message = "Отслеживаемый ранг изменён на <b>Максимальный</b>."
                    item.min_rank = market_item.max_rank
                    item.max_rank = market_item.max_rank

            # Сохраняем изменения
            item.save()

            # Формируем сообщение пользователю
            if rank_changed_message:
                messages.success(request, f"Изменения сохранены. {rank_changed_message}")
            else:
                messages.success(request, "Изменения сохранены.")

            return redirect("tracker-items")
        else:
            messages.error(request, "Исправьте ошибки в форме.")
    else:
        form = TrackedItemForm(instance=item)

    market_item = MarketItem.objects.filter(item_url_name=item.item_url_name).first()
    return render(request, "tracker/edit_item.html", {"form": form, "item": item, "market_item": market_item})

def delete_item(request, item_id):
    item = get_object_or_404(TrackedItem, id=item_id)
    item.delete()
    # После удаления возвращаемся к списку
    return redirect("tracker-items")

@require_GET
def autocomplete_items(request):
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        # ограничиваем количество результатов для производительности
        qs = MarketItem.objects.filter(item_name__icontains=q).order_by('item_name')[:12]
        # возвращаем только поля, которые нужны фронтенду
        results = [
            {"name": item.item_name, "url": item.item_url_name, "max_rank": item.max_rank,}
            for item in qs
        ]
    return JsonResponse(results, safe=False)
