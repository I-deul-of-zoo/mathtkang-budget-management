from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        max_length=128,
        unique=True,
    )  # 계정명
    total = models.PositiveBigIntegerField(default=0)  # 총액