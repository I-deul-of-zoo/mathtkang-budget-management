from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Expenditure(models.Model):
    appropriate_amount = models.PositiveIntegerField(default=0)  # 적정금액
    expense_amount = models.PositiveIntegerField(default=0)  # 지출금액
    memo = models.TextField(null=True, blank=True)  # 메모
    is_except = models.BooleanField(default=False)  # 합계 제외 여부
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey('budgets.Category', on_delete=models.CASCADE)