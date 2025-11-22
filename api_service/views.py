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
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Q, Count
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Category, Transaction, User, Goal
from .serializers import CategorySerializer, TransactionSerializer, UserSerializer, GoalSerializer


class StandardResultsSetPagination(PageNumberPagination):
    """Default paginator for list endpoints.

    Query params:
    - page: page number (1-based)
    - page_size: items per page (max 100)
    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST')
def login_user (request):
    """Authenticate a user and return an auth token.

    Expects POST data: ``username`` and ``password``.

    Rate limit: 5 requests per minute per IP address to prevent brute force attacks.

    Response (200): {"token": <token>, "user": { ... public user fields ... }}
    Response (400): {"error": "..."} on invalid credentials.
    Response (429): Too many requests if rate limit exceeded.
    """
    
    # Check if rate limit was hit
    if getattr(request, 'limited', False):
        return Response(
            {"error": "Too many login attempts. Please try again in a minute."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    username = request.data.get('username')
    password = request.data.get('password')
    user_exists = get_object_or_404(User, username=username)
    print("User exists: ", user_exists)
    if user_exists == "":
        return Response({"error": "O usuario nao existe"}, status=status.HTTP_400_BAD_REQUEST)
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
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/h', method='POST')
def create_user(request):
    """Create a new user.

    Expected POST body: user fields (including a `password` field).

    Rate limit: 3 requests per hour per IP address to prevent spam account creation.

    Notes:
    - The view ensures the provided password is hashed via ``set_password``
      before the user object is persisted.
    - The serializer handles validation; sensitive fields should be
      write-only or excluded from serialized responses.
    """
    # Check if rate limit was hit
    if getattr(request, 'limited', False):
        return Response(
            {"error": "Too many registration attempts. Please try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    serializer = UserSerializer(data=request.data)
    print("serializer: ", serializer)
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

# TODO remove in production
@api_view(['get'])
@permission_classes([AllowAny])
def fecth_all_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
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
    user = get_object_or_404(User, pk=pk)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            if 'password' in request.data:
                # Validate new password
                try:
                    validate_password(request.data['password'], user)
                except DjangoValidationError as e:
                    return Response({'password': e.messages}, status=status.HTTP_400_BAD_REQUEST)
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

    # Optional filter by id
    id_param = request.query_params.get('id')
    if id_param:
        categories = categories.filter(id=id_param)

    # Optional filter by type (INCOME | EXPENSE)
    type_param = request.query_params.get('type')
    if type_param:
        categories = categories.filter(type=type_param)

    # Optional search by name
    q = request.query_params.get('q')
    if q:
        categories = categories.filter(name__icontains=q)

    # Optional ordering (default name asc). Allowed: name, -name
    ordering = request.query_params.get('ordering', 'name')
    if ordering not in ['name', '-name']:
        ordering = 'name'
    categories = categories.order_by(ordering)
    
    # order by transactions count descending
    sort_by = request.query_params.get('sort_by')
    if sort_by == 'transactions_count':
        categories = categories.annotate(transactions_count=Count('transaction')).order_by('-transactions_count')

    # Only paginate when explicitly requested to preserve backward compatibility
    paginate_flag = request.query_params.get('paginate')
    has_page_params = (
        'page' in request.query_params or 'page_size' in request.query_params or (paginate_flag and paginate_flag.lower() in ['1', 'true', 'yes'])
    )

    if has_page_params:
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    else:
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='30/m', method='POST')
def create_category(request):
    """Create a new category for the authenticated user.

    POST body should include: `name`, `type` and optional `color`.
    The `user` is set server-side to `request.user` to prevent spoofing.
    
    Rate limit: 30 requests per minute per user to prevent abuse.
    """
    
    if getattr(request, 'limited', False):
        return Response(
            {"error": "Too many requests. Please slow down."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

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

    category = get_object_or_404(Category, pk=pk, user=request.user)

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
@ratelimit(key='user', rate='100/m', method='GET')
def get_transactions(request):
    """List transactions for the authenticated user.

    The view returns the user's transactions ordered by date (newest
    first). Consider adding pagination and `select_related('category')`
    to reduce DB queries for large lists.
    
    Rate limit: 100 requests per minute per user.
    """
    
    if getattr(request, 'limited', False):
        return Response(
            {"error": "Too many requests. Please slow down."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    transactions = (Transaction.objects
                    .filter(user=request.user)
                    .select_related('category'))

    # Filters
    category_id = request.query_params.get('category_id')
    if category_id:
        transactions = transactions.filter(category_id=category_id)

    type_param = request.query_params.get('type')  # INCOME | EXPENSE via category
    if type_param:
        transactions = transactions.filter(category__type=type_param)

    start_date = request.query_params.get('start_date')  # ISO 8601
    end_date = request.query_params.get('end_date')
    if start_date:
        dt = parse_datetime(start_date)
        if dt is None:
            return Response({
                'error': {
                    'start_date': 'Invalid datetime. Use ISO 8601, e.g., 2025-11-16T14:30:00Z or 2025-11-16T14:30:00+00:00.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        transactions = transactions.filter(date__gte=dt)
    if end_date:
        dt = parse_datetime(end_date)
        if dt is None:
            return Response({
                'error': {
                    'end_date': 'Invalid datetime. Use ISO 8601, e.g., 2025-11-16T14:30:00Z or 2025-11-16T14:30:00+00:00.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        transactions = transactions.filter(date__lte=dt)

    q = request.query_params.get('q')
    if q:
        transactions = transactions.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # Ordering: allowed fields only
    allowed_ordering = ['date', '-date', 'amount', '-amount']
    ordering = request.query_params.get('ordering', '-date')
    if ordering not in allowed_ordering:
        ordering = '-date'
    transactions = transactions.order_by(ordering)

    paginate_flag = request.query_params.get('paginate')
    has_page_params = (
        'page' in request.query_params or 'page_size' in request.query_params or (paginate_flag and paginate_flag.lower() in ['1', 'true', 'yes'])
    )

    if has_page_params:
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(transactions, request)
        serializer = TransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    else:
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='60/m', method='POST')
def create_transaction(request):
    """Create a new transaction for the authenticated user.

    Required POST data: `title`, `amount`, `date`, and `category_id`.
    The view validates that the provided `category_id` belongs to the
    authenticated user before creating the transaction.
    
    Rate limit: 60 requests per minute per user to prevent abuse.
    """
    
    if getattr(request, 'limited', False):
        return Response(
            {"error": "Too many requests. Please slow down."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

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

    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

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

    goals = Goal.objects.filter(user=request.user)

    # Filters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    if start_date:
        dt = parse_datetime(start_date)
        if dt is None:
            return Response({
                'error': {
                    'start_date': 'Invalid datetime. Use ISO 8601, e.g., 2025-11-16T14:30:00Z or 2025-11-16T14:30:00+00:00.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        goals = goals.filter(date__gte=dt)
    if end_date:
        dt = parse_datetime(end_date)
        if dt is None:
            return Response({
                'error': {
                    'end_date': 'Invalid datetime. Use ISO 8601, e.g., 2025-11-16T14:30:00Z or 2025-11-16T14:30:00+00:00.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        goals = goals.filter(date__lte=dt)

    q = request.query_params.get('q')
    if q:
        goals = goals.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # Ordering
    allowed_ordering = ['date', '-date', 'amount', '-amount', 'title', '-title']
    ordering = request.query_params.get('ordering', '-date')
    if ordering not in allowed_ordering:
        ordering = '-date'
    goals = goals.order_by(ordering)

    paginate_flag = request.query_params.get('paginate')
    has_page_params = (
        'page' in request.query_params or 'page_size' in request.query_params or (paginate_flag and paginate_flag.lower() in ['1', 'true', 'yes'])
    )

    if has_page_params:
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(goals, request)
        serializer = GoalSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    else:
        serializer = GoalSerializer(goals, many=True)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='30/m', method='POST')
def create_goal(request):
    """Create a new financial goal for the authenticated user.

    POST body must include `title`, `amount`, and `date`. The `user`
    is set server-side to `request.user`.
    
    Rate limit: 30 requests per minute per user to prevent abuse.
    """
    
    if getattr(request, 'limited', False):
        return Response(
            {"error": "Too many requests. Please slow down."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

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

    goal = get_object_or_404(Goal, pk=pk, user=request.user)

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