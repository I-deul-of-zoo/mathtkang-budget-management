from rest_framework import serializers
from expenditures.models import Expenditure

class ExpenditureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenditure
        fields = (
            'id', 
            'expense_date', 
            'expense_amount', 
            'memo', 
            'is_except', 
            'user', 
            'category'
        )
