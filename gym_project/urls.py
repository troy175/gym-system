from django.contrib import admin
from django.urls import path
from gym import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('walkin/', views.walkin, name='walkin'),
    path('membership/', views.register_membership, name='membership'),
    path('monthly/', views.register_monthly, name='monthly'),
    path('add-customer/', views.add_customer, name='add_customer'),
    path('customers/', views.customer_list, name='customers'),
    path('members/', views.members_list, name='members'),
    path('monthly-list/', views.monthly_list, name='monthly_list'),
    path('edit-customer/<int:id>/', views.edit_customer, name='edit_customer'),
    path('pos/', views.pos, name='pos'),
    path('add_inventory/', views.add_product, name='add_inventory'),
    path('products/', views.product_list, name='products'),
    path('edit-product/<int:id>/', views.edit_product, name='edit_product'),
    path('edit-monthly/<int:id>/', views.edit_monthly, name='edit_monthly'),
    path('delete-monthly/<int:id>/', views.delete_monthly, name='delete_monthly'),
    path('today-logs/', views.today_logs, name='today_logs'),
    path('edit-member/<int:id>/', views.edit_member, name='edit_member'),
    path('export-report/', views.export_report, name='export_report'),
]