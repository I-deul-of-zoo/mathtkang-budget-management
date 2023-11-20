import jwt
import requests
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

from auths.serializers import CreateUserSerializer, ValidationSerializer
from auths.models import User


class SignUp(APIView):
    '''
    🔗 url: /auths/signup
    ✅ 회원가입
    {
        "username": "user1",
        "password": "devpassword1"
    }
    '''
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        print(request.data)

        if not username or not password:
            raise ParseError(detail="잘못된 요청입니다. username, password 모두 존재해야합니다.")
        
        serializer = ValidationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(password)  # hashed password
            user.save()

            return Response(
                CreateUserSerializer(user).data,
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "error": "회원가입에 실패했습니다.", 
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class JWTLogin(APIView):
    '''
    🔗 url: /auths/jwt-login
    ✅ JWT 로그인
    '''
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            raise ParseError(detail="잘못된 요청입니다. username, password 모두 존재해야합니다.")

        user = authenticate(
            request, 
            username=username, 
            password=password
        )

        if user is not None:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response(
                {
                    "username": user.username,
                    'access_token': access_token,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "username 또는 password가 잘못되었습니다."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )