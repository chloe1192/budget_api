from rest_framework import serializers
from django.utils import timezone
from .models import Category, Currency, Transaction, User, Goal, Wallet
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model.

    Implements create() and update() to ensure passwords are hashed
    via the model's ``set_password`` method before saving.
    """
    
    total_wallets_balance_in_usd = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        # Keep password write-only so it never appears in serialized output
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'dob', 'avatar', 'initial_balance', 'created_at', 'edited_at', 'password', 'total_wallets_balance_in_usd']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'dob': {'required': False},
            'avatar': {'required': False},
            'initial_balance': {'required': False}
        }
    
    def get_total_wallets_balance_in_usd(self, obj):
        """Return the user's calculated total balance."""
        return obj.get_total_wallets_balance_in_usd()
    
    def validate_password(self, value):
      """Validate password using Django's password validators."""
      if value:
          try:
              validate_password(value)
          except ValidationError as e:
              raise serializers.ValidationError(list(e.messages))
      return value
    
    def create(self, validated_data):
        """Create a new User instance and hash the password.

        The password is expected in `validated_data['password']` and will
        be removed from the dict before creating the instance so it is
        not stored in plaintext.
        """
          
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        else:
          return validated_data
        return user

    def update(self, instance, validated_data):
        """Update a User instance and hash new password if provided.

        If a 'password' key is included it's removed from validated_data and
        applied via the model's `set_password` to ensure secure storage.
        """

        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model.

    - Exposes id, name, color, type and the owner (`user`).
    - `user` is marked read-only because the server should assign the
      authenticated user when creating categories (do not trust client).
    - Keep this class minimal; add validation here if category ownership
      or naming rules are needed.
    """

    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'type', 'user']
        read_only_fields = ['user']

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model.

    - `category_id` accepts a primary key for an existing Category and
      is mapped to the `category` relation on the model (write-only).
    - `category` is returned as a nested CategorySerializer for reads.
    - `user` is intentionally read-only: views should call
      serializer.save(user=request.user) to associate the record.
    - Consider adding validation to ensure the provided category belongs
      to the authenticated user (not implemented here).
    """

    # Enforce ISO8601 input with clearer error message for date
    date = serializers.DateTimeField(
      error_messages={
        'invalid': 'Invalid datetime format for "date". Use ISO 8601, e.g., 2025-11-16T14:30:00Z or 2025-11-16T14:30:00+00:00.'
      }
    )

    # Accept category PK on write, map to `category` relation.
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    # Return nested category representation on reads.
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'title', 'description', 'amount', 'date', 'category', 'category_id']
        # user and category are managed server-side / read-only in responses
        read_only_fields = ['user', 'category']

    def validate_date(self, value):
      """Require timezone-aware datetimes for consistency."""
      if timezone.is_naive(value):
        raise serializers.ValidationError('The "date" must include a timezone offset (e.g., Z or +00:00).')
      return value

class GoalSerializer(serializers.ModelSerializer):
    """Serializer for Goal model.

    - Exposes all fields but marks user, created_at and updated_at as read-only.
    - Keep business validation (target date, amounts) in this serializer if
      project rules require it.
    """

    # Enforce ISO8601 input with clearer error message for date
    date = serializers.DateTimeField(
      error_messages={
        'invalid': 'Invalid datetime format for "date". Use ISO 8601, e.g., 2025-11-16T14:30:00Z or 2025-11-16T14:30:00+00:00.'
      }
    )

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_date(self, value):
      """Require timezone-aware datetimes for consistency."""
      if timezone.is_naive(value):
        raise serializers.ValidationError('The "date" must include a timezone offset (e.g., Z or +00:00).')
      return value

class CurrencySerializer(serializers.ModelSerializer):
  class Meta:
    model = Currency
    fields = '__all__'
    read_only = True

class WalletSerializer(serializers.ModelSerializer):
  
  currency_id = serializers.PrimaryKeyRelatedField(
    queryset = Currency.objects.all(), source='currency', write_only=True
  )
  currency = CurrencySerializer(read_only=True)
  total_balance = serializers.SerializerMethodField(read_only=True)
  wallet_balance_in_usd = serializers.SerializerMethodField(read_only=True)
  
  class Meta:
    model = Wallet
    fields = ['id', 'currency_id', 'currency', 'user', 'initial_balance', 'total_balance', 'created_at', 'wallet_balance_in_usd']
    read_only_fields = ['user', 'created_at', 'currency']
    
  def get_total_balance(self, obj):
    return obj.get_total_balance()
  
  def get_wallet_balance_in_usd(self, obj):
    return obj.get_wallet_balance_in_usd()
  