from django.db import models
from datetime import date
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


# 👤 Customer
class Customer(models.Model):
    CUSTOMER_TYPE = [
        ('student', 'Student'),
        ('regular', 'Regular'),
    ]

    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPE, default='regular')
    is_member = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# 💳 Monthly Plan
class Membership(models.Model):
    PLAN_CHOICES = [
        ('1_month', '1 Month'),
        ('3_months', '3 Months'),
        ('12_months', '12 Months'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        if not self.customer.is_member:
            raise ValidationError("Customer must be a member first.")

    def is_active(self):
        return self.end_date >= date.today()

    def days_remaining(self):
        return (self.end_date - date.today()).days


# 🔥 DAILY ENTRY
class DailyEntry(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    entry_type = models.CharField(max_length=20)  # walkin / monthly
    walkin_type = models.CharField(max_length=20, blank=True, null=True)

    price = models.DecimalField(max_digits=6, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=6, decimal_places=2)
    change = models.DecimalField(max_digits=6, decimal_places=2)

    # ✅ IMPORTANT (FOR FILTERING)
    date = models.DateField(auto_now_add=True)

    # ✅ FOR EXACT TIME
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ AUDIT
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.customer.name} - {self.date}"


# 🛒 Product
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# 🧾 Sale
class Sale(models.Model):
    date = models.DateTimeField(auto_now_add=True)  # 🔥 KEEP (wag palitan)

    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


# 🧾 Sale Items
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.IntegerField()
    subtotal = models.DecimalField(max_digits=8, decimal_places=2)


# 👤 YEARLY MEMBERSHIP LOG
class MembershipLog(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.customer.name} - {self.start_date}"