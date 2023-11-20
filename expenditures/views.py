from datetime import datetime
from django.db.models import Sum
from django.utils.dateparse import parse_datetime
from django.db.models.functions import ExtractMonth

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from budgets.models import Category, Budget
from expenditures.models import Expenditure
from expenditures.serializers import ExpenditureSerializer


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