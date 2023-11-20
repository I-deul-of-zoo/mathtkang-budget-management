from django.urls import path
from budgets import views

app_name = "budgets"

urlpatterns =[
    path('budgets/', views.CategoryList.as_view()),
]