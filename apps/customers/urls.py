"""
URL patterns for customers app.
"""

from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # M-Pesa Daraja STK callback (public HTTPS endpoint; no login)
    path('mpesa/stk-callback/', views.mpesa_stk_callback_view, name='mpesa_stk_callback'),

    # Customer self-service portal (must be before <int:pk>/ routes)
    path('portal/', views.customer_portal_view, name='portal'),
    path('portal/profile/', views.customer_portal_profile_view, name='portal_profile'),
    path('portal/vehicle/add/', views.customer_portal_vehicle_add_view, name='portal_vehicle_add'),
    path('portal/book/', views.customer_book_job_view, name='book_job'),
    path(
        'portal/jobs/<int:job_pk>/payment-method/',
        views.customer_job_select_payment_method_view,
        name='job_select_payment_method',
    ),
    path(
        'portal/jobs/<int:job_pk>/pay/mpesa/',
        views.customer_job_mpesa_pay_view,
        name='job_pay_mpesa',
    ),
    path(
        'portal/jobs/<int:job_pk>/pay/mpesa/stk/',
        views.customer_job_mpesa_stk_initiate_view,
        name='job_mpesa_stk',
    ),

    # Customers
    path('', views.customer_list_view, name='list'),
    path('create/', views.customer_create_view, name='create'),
    path('<int:pk>/', views.customer_detail_view, name='detail'),
    path('<int:pk>/edit/', views.customer_edit_view, name='edit'),
    
    # Vehicles
    path('<int:customer_pk>/vehicles/add/', views.vehicle_create_view, name='vehicle_create'),
    path('vehicles/<int:pk>/', views.vehicle_detail_view, name='vehicle_detail'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit_view, name='vehicle_edit'),
    
    # Quick form
    path('quick-add/', views.quick_customer_vehicle_view, name='quick_add'),
    
    # API
    path('api/search/', views.api_customer_search, name='api_search'),
    path('api/vehicles/search/', views.api_vehicle_search, name='api_vehicle_search'),
    path('api/<int:customer_pk>/vehicles/', views.api_customer_vehicles, name='api_vehicles'),
]
