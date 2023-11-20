from django.urls import path
from auths import views

app_name = "auths"

urlpatterns =[
    path("signup", views.SignUp.as_view()),
    path("jwt-login", views.JWTLogin.as_view()),
]