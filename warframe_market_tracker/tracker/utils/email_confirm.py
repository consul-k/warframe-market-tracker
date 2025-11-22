from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse

def build_confirm_link(request, user):
    token = default_token_generator.make_token(user)
    uid = user.pk
    return request.build_absolute_uri(
        reverse("confirm_email", kwargs={"uid": uid, "token": token})
    )