from django.urls import path
from . import views

urlpatterns = [
    # user
    path('user/create/', views.create_user, name='create_user'),
    path('user/login/', views.login_user, name='login_user'),
    path('user/me/', views.get_user, name='get_user'),
    path('user/list/', views.fetch_all_users, name="fetch_all_users"),
    path('user/edit/', views.user_detail, name='edut_user'),
    path('user/delete/', views.user_detail, name='delete_user'),
    # categories
    path('categories/', views.get_categories, name='get_categories'),
    path('categories/create/', views.create_category, name='get_categories'),
    path('categories/<int:pk>/', views.category_detail, name='get_category'),
    # transactions
    path('transactions/', views.get_transactions, name='get_transactions'),
    path('transactions/create', views.create_transaction, name='create_transaction'),
    path('transactions/<int:pk>/', views.transaction_detail, name='edit_transaction'),
    # goals
    path('goals/', views.get_goals, name='get_goals'),
    path('goals/create/', views.create_goal, name='create_goal'),
    path('goals/<int:pk>/', views.goal_detail, name='goal_detail'),
    # currencies
    path('currencies/', views.currency_list, name='currency_list'),
    # wallets
    path('wallet/create/', views.wallet_create, name='wallet_create'),
    path('wallet/update/', views.wallet_create, name='wallet_update'),
    path('wallet/list/', views.wallet_list, name='wallet_list'),
    path('wallet/list/<int:pk>/', views.wallet_list, name='wallet_list'),
    path('wallet/delete/<int:pk>/', views.wallet_delete, name='wallet_delete')
]
