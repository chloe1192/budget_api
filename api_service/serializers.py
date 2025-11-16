from rest_framework import serializers
from .models import Category, Transaction, User, Goal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'dob', 'avatar', 'initial_balance', 'created_at', 'edited_at', 'password']
        extra_kwargs = {'password': {'write_only': True}}

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'type', 'user']
        read_only_fields = ['user']

class TransactionSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'title', 'description', 'amount', 'date', 'category', 'category_id']
        read_only_fields = ['user', 'category']

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']