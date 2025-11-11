from django import forms
from django.core.exceptions import ValidationError
from .models import TrackedItem, MarketItem

class TrackedItemForm(forms.ModelForm):
    class Meta:
        model = TrackedItem
        fields = ["name", "item_url_name", "target_price", "chat_id", "min_rank", "max_rank"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Например: Gara Prime Set"}),
            "item_url_name": forms.HiddenInput(),
            "min_rank": forms.NumberInput(attrs={"class":"form-control","placeholder":"0"}),
            "max_rank": forms.NumberInput(attrs={"class":"form-control","placeholder":"max"}),
            "target_price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Цена в платине"}),
            "chat_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ваш Telegram chat ID"}),
        }
        labels = {
            "name": "Название предмета",
            "target_price": "Целевая цена (платина)",
            "chat_id": "Telegram chat ID",
            "min_rank": "Минимальный ранг",
            "max_rank": "Максимальный ранг",
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Введите название предмета.")
        # Проверяем, есть ли такой предмет в MarketItem
        if not MarketItem.objects.filter(item_name__iexact=name).exists():
            raise ValidationError("Выберите предмет из подсказки (должен соответствовать базе).")
        return name

    def clean_item_url_name(self):
        # Сохраняем как пустую строку или значение без пробелов
        value = (self.cleaned_data.get("item_url_name") or "").strip()
        if not value and self.instance:
            value = self.instance.item_url_name
        return value
    
    def clean_target_price(self):
        target = self.cleaned_data.get("target_price")
        if target is None or target <= 0:
            raise ValidationError("Укажите корректную целевую цену (платина > 0).")
        return target

    def clean(self):
        cleaned = super().clean()

        min_rank = cleaned.get("min_rank")
        max_rank = cleaned.get("max_rank")
        name = cleaned.get("name", "").strip()
        item_url_name = (cleaned.get("item_url_name") or "").strip()

        mi = MarketItem.objects.filter(item_name__iexact=name).first()

        # Проверка дубликатов
        qs = TrackedItem.objects.all()
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if item_url_name:
            if qs.filter(item_url_name__iexact=item_url_name).exists():
                raise ValidationError("Этот предмет уже отслеживается.")
        else:
            if qs.filter(name__iexact=name).exists():
                raise ValidationError("Этот предмет уже отслеживается.")

        # Проверка рангов
        if min_rank is not None and max_rank is not None:
            if min_rank > max_rank:
                raise ValidationError("Минимальный ранг не может быть больше максимального.")

        if mi and mi.max_rank is not None:
            if min_rank is not None and min_rank < 0:
                raise ValidationError("Минимальный ранг не может быть меньше 0.")
            if max_rank is not None and max_rank > mi.max_rank:
                raise ValidationError(f"Максимальный ранг не может быть больше {mi.max_rank}.")

        return cleaned