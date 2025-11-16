from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum, Q
from decimal import Decimal

class User(AbstractUser):
    dob = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
            return f"{self.first_name} {self.last_name}"
    
    def get_total_balance(self):
        """Calculate total balance: initial_balance + income - expenses."""
        income = Transaction.objects.filter(
            user=self,
            category__type='INCOME'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        expenses = Transaction.objects.filter(
            user=self,
            category__type='EXPENSE'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return self.initial_balance + income - expenses

class Category(models.Model):
    TYPE_CHOICES = [
        ('INCOME', 'Entrada'),
        ('EXPENSE', 'Saída'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    color = models.CharField(max_length=7, default='#000')

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - R${self.amount}"

class Goal(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title