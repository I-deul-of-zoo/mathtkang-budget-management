from django.urls import path
from budgets import views

app_name = "budgets"

urlpatterns =[
    path('/', views.CategoryList.as_view()),
    path('rec/', views.BudgetRecommendation.as_view()),
]