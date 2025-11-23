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
    
    def get_total_wallets_balance_in_usd(self):
        """Calculate total balance: initial_balance + income - expenses."""
        currencies = Currency.objects.all()
        # wallets = Wallet.objects.filter(user=self)
        total_value_in_usd = 0
        for cur in Wallet.objects.filter(user=self):
            total_balance = cur.get_total_balance()
            total_value_in_usd += total_balance * cur.currency.value_in_usd        
        
        return total_value_in_usd

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

class Currency(models.Model):
    # TODO run service to update currencies daily
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=3)
    symbol = models.CharField(max_length=3)
    country = models.CharField(max_length=3) # Country ISO code
    value_in_usd = models.DecimalField(max_digits=10, decimal_places=3)

class Wallet(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.RESTRICT, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_balance = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    initial_balance = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_wallet_balance_in_usd(self):
        print(self.get_total_balance())
        print(self.currency.value_in_usd)
        print(self.get_total_balance() * self.currency.value_in_usd)
        balance = self.get_total_balance() * self.currency.value_in_usd
        return balance
        
    
    def get_total_balance(self):
        income = Transaction.objects.filter(wallet=self, category__type='INCOME').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        expenses = Transaction.objects.filter(wallet=self, category__type='INCOME').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return self.initial_balance + income - expenses
    # TODO restrict user from creating wallets in the same currency
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.description} - R${self.amount}"