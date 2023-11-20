from django.db.models import Sum
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from budgets.models import Category, Budget
from budgets.serializers import CategorySerializer

class CategoryList(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CategorySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request):
        try:
            category_id = request.data.get('id')
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return Response(
                {'error': 'Category not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


class BudgetRecommendation(APIView):
    def post(self, request):
        # 입력된 총액
        total_amount = request.data.get('total_amount', 0)

        # 카테고리별 예산 비율 계산
        category_ratios = self.calculate_category_ratios()

        # 카테고리별 예산 계산
        budget_data = {}
        for category, ratio in category_ratios.items():
            budget_amount = round(total_amount * ratio / 100)
            budget_data[category] = {'amount': budget_amount, 'ratio': ratio}

        return Response(
            budget_data, 
            status=status.HTTP_200_OK
        )

    def put(self, request):
        # 수정된 예산 데이터 저장
        budgets = request.data.get('budgets', {})
        for category, budget_info in budgets.items():
            amount = budget_info.get('amount', 0)
            ratio = budget_info.get('ratio', 0)
            category_obj, created = Category.objects.get_or_create(name=category)
            budget_obj, created = Budget.objects.get_or_create(user=request.user, category=category_obj)
            budget_obj.amount = amount
            budget_obj.ratio = ratio
            budget_obj.save()

        return Response(
            {'message': 'Budgets updated successfully'}, 
            status=status.HTTP_200_OK
        )

    def calculate_category_ratios(self):
        # 카테고리별 예산 비율을 계산하는 함수 (평균값 사용)
        category_ratios = {}

        # 모든 유저의 카테고리별 예산을 조회하여 평균 계산
        all_users_budgets = Budget.objects.all()
        total_ratio_sum = 0

        for category in Category.objects.all():
            category_budgets = all_users_budgets.filter(category=category)
            category_ratio_sum = category_budgets.aggregate(Sum('ratio'))['ratio__sum'] or 0
            category_ratio_avg = category_ratio_sum / category_budgets.count() if category_budgets.count() > 0 else 0
            category_ratios[category.name] = category_ratio_avg
            total_ratio_sum += category_ratio_avg

        # 10% 이하의 카테고리들은 모두 묶어 기타로 설정
        for category in Category.objects.all():
            if category_ratios[category.name] < 10:
                category_ratios['기타'] = category_ratios.get('기타', 0) + category_ratios[category.name]
                del category_ratios[category.name]

        # 기타 카테고리의 비율이 10% 미만이라면 0으로 설정
        category_ratios['기타'] = max(0, category_ratios.get('기타', 0))

        # 비율을 전체 합이 100%가 되도록 정규화
        if total_ratio_sum > 0:
            for category in category_ratios:
                category_ratios[category] = (category_ratios[category] / total_ratio_sum) * 100

        return category_ratios