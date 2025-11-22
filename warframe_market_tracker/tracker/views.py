from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import TrackedItem, MarketItem
from .forms import TrackedItemForm
from .forms import CustomUserCreationForm
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

@login_required
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

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = request.build_absolute_uri(
                reverse('activate', kwargs={'uidb64': uid, 'token': token})
            )
            
            send_mail(
                "Подтверждение регистрации",
                f"Для активации аккаунта перейдите по ссылке:\n{activation_link}",
                from_email=None,
                recipient_list=[user.email],
            )

            messages.success(request, "Аккаунт создан. Проверьте почту для подтверждения.")
            return redirect('login')  # важный redirect
    else:
        form = CustomUserCreationForm()

    return render(request, 'tracker/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email подтверждён. Теперь вы можете войти.")
        return redirect('login')
    else:
        messages.error(request, "Ссылка недействительна или уже использована.")
        return redirect('login')

@login_required
def profile(request):
    return render(request, 'tracker/profile.html')