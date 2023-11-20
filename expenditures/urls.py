from django.urls import path
from expenditures import views

app_name = "expenditures"

urlpatterns = [
    path('', views.ExpenditureList.as_view()),
    path('<int:id>/', views.ExpenditureDetail.as_view()),
    path('noti/', views.NotiTodayExpenditure.as_view()),
]