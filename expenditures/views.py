import random
from faker import Faker
from datetime import datetime, timedelta
from django.db.models import Sum
from django.utils.dateparse import parse_datetime
from django.db.models.functions import ExtractDay, ExtractWeekDay

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from budgets.models import Category, Budget
from expenditures.models import Expenditure
from expenditures.serializers import ExpenditureSerializer

fake = Faker()


class ExpenditureList(APIView):
    def get(self, request):
        # 기간 필터링
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        start_date = parse_datetime(start_date_str) if start_date_str else None
        end_date = parse_datetime(end_date_str) if end_date_str else None

        # 카테고리 필터링
        category_id = request.query_params.get('category_id', None)
        category_filter = {'category_id': category_id} if category_id else {}

        # 최소, 최대 금액 필터링
        min_amount = request.query_params.get('min_amount', None)
        max_amount = request.query_params.get('max_amount', None)
        amount_filter = {}
        if min_amount:
            amount_filter['expense_amount__gte'] = min_amount
        if max_amount:
            amount_filter['expense_amount__lte'] = max_amount

        # 지출 목록 조회
        expenditures = Expenditure.objects.filter(
            user=request.user,
            expense_date__range=(start_date, end_date),
            **category_filter,
            **amount_filter
        )

        # 합계 계산
        total_expense = expenditures.aggregate(Sum('expense_amount'))['expense_amount__sum']
        category_totals = (
            expenditures.values('category__name')
                        .annotate(category_total=Sum('expense_amount'))
        )

        # 결과 반환
        serializer = ExpenditureSerializer(expenditures, many=True)
        data = {
            'expenditures': serializer.data,
            'total_expense': total_expense,
            'category_totals': list(category_totals)
        }

        return Response(data)

    def post(self, request):
        serializer = ExpenditureSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpenditureDetail(APIView):
    def get_object(self, id):
        try:
            return Expenditure.objects.get(pk=id)
        except Expenditure.DoesNotExist:
            return None

    def get(self, request, id):
        expenditure = self.get_object(id)

        if expenditure is not None:
            serializer = ExpenditureSerializer(expenditure)
            return Response(serializer.data)

        return Response(
            {'error': 'Expenditure not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    def put(self, request, id):
        expenditure = self.get_object(id)

        if expenditure is not None:
            serializer = ExpenditureSerializer(expenditure, data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'error': 'Expenditure not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    def delete(self, request, id):
        expenditure = self.get_object(id)

        if expenditure is not None:
            expenditure.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'error': 'Expenditure not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


class TodayRecommendation(APIView):
    def get(self, request, format=None):
        # 오늘 지출 가능 금액 계산
        today = datetime.now().date()

        # 월별 카테고리 예산 조회
        categories = Category.objects.all()
        category_budgets = {}
        for category in categories:
            category_budget = category.budget_set.filter(user=request.user).first()
            if category_budget:
                category_budgets[category.name] = category_budget.amount
            else:
                category_budgets[category.name] = 0

        # 이전 일자의 과다 소비 고려하여 오늘 예산 계산
        expenditures_before_today = Expenditure.objects.filter(
            user=request.user,
            expense_date__date__lt=today
        )
        total_expenditure_before_today = expenditures_before_today.aggregate(Sum('expense_amount'))['expense_amount__sum']

        remaining_days = (today.replace(day=1) + timedelta(days=31) - today).days
        remaining_budget = max(0, sum(category_budgets.values()) - total_expenditure_before_today)
        daily_budget = remaining_budget / remaining_days if remaining_days > 0 else 0

        # 카테고리 별 오늘 지출 가능 금액 계산
        category_recommendations = {}
        for category_name, category_budget in category_budgets.items():
            category_expenditure_before_today = (
                expenditures_before_today.filter(category__name=category_name)
                                        .aggregate(Sum('expense_amount'))['expense_amount__sum'] or 0
            )
            category_remaining_budget = max(0, category_budget - category_expenditure_before_today)
            category_daily_budget = category_remaining_budget / remaining_days if remaining_days > 0 else 0
            category_recommendations[category_name] = round(category_daily_budget)

        # 메시지 생성
        total_recommendation = round(daily_budget)
        message = self.generate_recommendation_message(total_recommendation)

        # 결과 반환
        result_data = {
            'total_recommendation': total_recommendation,
            'category_recommendations': category_recommendations,
            'message': message
        }

        return Response(result_data)

    def generate_recommendation_message(self, total_recommendation):
        if total_recommendation == 0:
            return "오늘은 예산을 모두 사용했어요. 다음에는 더 신중하게 사용해보세요!"
        elif total_recommendation > 0 and total_recommendation <= 10000:
            return "잘 아끼고 있을 때, 적당히 사용 중이시네요. 계속 이렇게 가세요!"
        elif total_recommendation > 10000 and total_recommendation <= 20000:
            return "기준을 조금 넘었을 때. 조금 더 절약해보는 건 어떨까요?"
        else:
            return "예산을 많이 초과하셨어요. 지출을 줄이는 노하우를 찾아보세요!"


class NotiTodayExpenditure(APIView):
    def get(self, request):
        # 오늘 지출한 내역 조회
        today = datetime.now().date()
        expenditures_today = Expenditure.objects.filter(
            user=request.user,
            expense_date__date=today
        )
        today_total_amount = expenditures_today.aggregate(Sum('expense_amount'))['expense_amount__sum']

        # 월별 카테고리 통계 조회
        month_start = today.replace(day=1)
        expenditures_month = Expenditure.objects.filter(
            user=request.user,
            expense_date__date__gte=month_start
        )

        # 카테고리 별 지출 합계 계산
        category_totals = (
            expenditures_month.values('category__name')
                            .annotate(category_total=Sum('expense_amount'))
        )

        # 카테고리별 예산 조회 및 계산
        categories = Category.objects.all()
        category_stats = []
        for category in categories:
            category_budget = category.budget_set.filter(user=request.user).first()
            category_total_amount = next(
                (item['category_total'] for item in category_totals if item['category__name'] == category.name),
                0
            )
            if category_budget:
                today_appropriate_amount = category_budget.amount * today.day / month_start.days_in_month
                danger_percentage = (category_total_amount - today_appropriate_amount) / today_appropriate_amount * 100
            else:
                today_appropriate_amount = 0
                danger_percentage = 0

            category_stat = {
                'category_name': category.name,
                'today_appropriate_amount': today_appropriate_amount,
                'today_expense_amount': category_total_amount,
                'danger_percentage': danger_percentage
            }
            category_stats.append(category_stat)

        result_data = {
            'today_total_amount': today_total_amount,
            'category_stats': category_stats
        }

        return Response(result_data)


class Statistics(APIView):
    def generate_dummy_data(self, user, num_entries=30):
        # 더미 데이터 생성
        categories = Category.objects.all()
        for _ in range(num_entries):
            date = fake.date_this_month()
            category = random.choice(categories)
            amount = random.randint(1000, 50000)
            Expenditure.objects.create(
                expense_date=date,
                expense_amount=amount,
                user=user,
                category=category
            )