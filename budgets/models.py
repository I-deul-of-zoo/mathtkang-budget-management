from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)

class Budget(models.Model):
    amount = models.PositiveIntegerField(default=0)  # 금액
    ratio = models.FloatField(default=0)  # 비율
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey('budgets.Category', on_delete=models.CASCADE)
