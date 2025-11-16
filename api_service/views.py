"""API view handlers for the `api_service` app.

This module exposes function-based Django REST Framework views for
authentication, user management, categories, transactions and goals.

Conventions:
- Each view is decorated with `@api_view` and, where appropriate,
    `@permission_classes([IsAuthenticated])` to enforce authentication.
- Password hashing is performed server-side (see `create_user` /
    serializer handling) and user fields returned by serializers should
    avoid exposing sensitive attributes.

Small, focused functions are used here; consider refactoring to
ViewSets/ModelViewSets for more concise routing and automatic
behaviour (pagination, filtering) in a future refactor.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import Category, Transaction, User, Goal
from .serializers import CategorySerializer, TransactionSerializer, UserSerializer, GoalSerializer


@api_view(['POST'])
def login_user (request):
    """Authenticate a user and return an auth token.

    Expects POST data: ``username`` and ``password``.

    Response (200): {"token": <token>, "user": { ... public user fields ... }}
    Response (400): {"error": "..."} on invalid credentials.
    """

    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email
            }
        })
    return Response({"error": "Usuário ou senha inválidos"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_user(request):
    """Create a new user.

    Expected POST body: user fields (including a `password` field).

    Notes:
    - The view ensures the provided password is hashed via ``set_password``
      before the user object is persisted.
    - The serializer handles validation; sensitive fields should be
      write-only or excluded from serialized responses.
    """

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # Serializer.create() handles hashing the password
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    """Return the authenticated user's profile.

    GET: returns serialized user information for the currently
    authenticated user. Requires authentication.
    """

    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail(request):
    """Retrieve, update or delete the authenticated user's record.

    Endpoints:
    - GET: return the user's data
    - PUT: update user fields (password handling performed server-side)
    - DELETE: remove the user account

    This view operates only on the authenticated user's own record
    (it ignores any PK passed in via the request and uses ``request.user``).
    """

    pk = request.user.pk
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# categories
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_categories(request):
    """List categories belonging to the authenticated user.

    GET: returns an array of categories for `request.user`.
    Pagination and filtering are not applied here but are recommended
    for large datasets.
    """

    categories = Category.objects.filter(user=request.user)
    return Response(CategorySerializer(categories, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    """Create a new category for the authenticated user.

    POST body should include: `name`, `type` and optional `color`.
    The `user` is set server-side to `request.user` to prevent spoofing.
    """

    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_detail(request, pk):
    """Retrieve, update, or delete a specific category.

    - GET: return category data
    - PUT: update category fields
    - DELETE: remove the category

    The category is always restricted to the authenticated user's
    categories via the queryset filter ``user=request.user``.
    """

    try:
        category = Category.objects.get(pk=pk, user=request.user)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# transactions
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transactions(request):
    """List transactions for the authenticated user.

    The view returns the user's transactions ordered by date (newest
    first). Consider adding pagination and `select_related('category')`
    to reduce DB queries for large lists.
    """

    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return Response(TransactionSerializer(transactions, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    """Create a new transaction for the authenticated user.

    Required POST data: `title`, `amount`, `date`, and `category_id`.
    The view validates that the provided `category_id` belongs to the
    authenticated user before creating the transaction.
    """

    category_id = request.data.get('category_id')
    if not category_id:
        return Response({"error": "category_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        category = Category.objects.get(pk=category_id, user=request.user)
    except Category.DoesNotExist:
        return Response({"error": "Categoria inválida"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TransactionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, category=category)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, pk):
    """Retrieve, update or delete a specific transaction.

    All operations are scoped to the authenticated user's transactions
    (``user=request.user``) to prevent access to other users' data.
    """

    try:
        transaction = Transaction.objects.get(pk=pk, user=request.user)
    except Transaction.DoesNotExist:
        return Response({"error": "transaction not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TransactionSerializer(transaction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# goals
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_goals(request):
    """List goals for the authenticated user, ordered by date.

    Consider adding filtering and pagination for large result sets.
    """

    goals = Goal.objects.filter(user=request.user).order_by('-date')
    serializer = GoalSerializer(goals, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_goal(request):
    """Create a new financial goal for the authenticated user.

    POST body must include `title`, `amount`, and `date`. The `user`
    is set server-side to `request.user`.
    """

    serializer = GoalSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def goal_detail(request, pk):
    """Retrieve, update or delete a specific goal belonging to the user.

    Scopes operations to the authenticated user to prevent unauthorized
    data access.
    """

    try:
        goal = Goal.objects.get(pk=pk, user=request.user)
    except Goal.DoesNotExist:
        return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = GoalSerializer(goal)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = GoalSerializer(goal, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        goal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)