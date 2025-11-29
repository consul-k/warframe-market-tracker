from django.core.exceptions import ValidationError

def validate_not_same_password(value, user=None):
    if user and user.check_password(value):
        raise ValidationError("Новый пароль не должен совпадать с текущим.")