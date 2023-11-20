from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from budgets.models import Category, Budget
from budgets.serializers import CategorySerializer

class CategoryList(APIView):
    def get(self, request, format=None):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)