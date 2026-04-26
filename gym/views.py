from django.shortcuts import render, redirect
from datetime import date, timedelta
from .models import Customer, DailyEntry, Membership
from django.db.models import Sum
from .models import Product, Sale, SaleItem
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .models import MembershipLog
import pandas as pd
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    today = date.today()

    # =========================
    # 💪 GYM USERS TODAY (ONLY DAILY LOG)
    # =========================
    today_entries = DailyEntry.objects.filter(date=today)

    walkin_today = today_entries.filter(entry_type='walkin').count()
    monthly_today = today_entries.filter(
        entry_type='monthly',
        price=0
    ).count()
    total_today_count = walkin_today + monthly_today

    # =========================
    # 💰 TOTAL EARNINGS TODAY
    # =========================

    # 🔥 ALL DAILY PAYMENTS (walkin + membership + promo if nandito)
    daily_total = DailyEntry.objects.filter(
        date=today
    ).aggregate(total=Sum('price'))['total'] or 0

    pos_total = Sale.objects.aggregate(total=Sum('total'))['total'] or 0

    # 🔥 FINAL TOTAL
    total_today = daily_total + pos_total

    # =========================
    # OTHER DATA (UNCHANGED)
    # =========================
    customers = Customer.objects.all()
    members = Customer.objects.filter(is_member=True)

    active_monthly = Membership.objects.filter(end_date__gte=today)

    expiring = Membership.objects.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=3)
    )

    yearly_expiring = MembershipLog.objects.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=3)
    )

    for m in yearly_expiring:
        m.days_remaining = (m.end_date - today).days

    context = {
        'walkin_today': walkin_today,
        'monthly_today': monthly_today,
        'count_today': total_today_count,
        'total_today': total_today,
        'pos_total': pos_total,

        'customers': customers,
        'members': members,
        'monthly': active_monthly,
        'expiring': expiring,
        'yearly_expiring': yearly_expiring,
    }

    return render(request, 'home.html', context)

@login_required
def walkin(request):
    today = date.today()

    customers = Customer.objects.all()

    # 🔥 ACTIVE MONTHLY MEMBERS
    monthly_ids = Membership.objects.filter(
        end_date__gte=today
    ).values_list('customer_id', flat=True)

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        entry_type = request.POST.get('entry_type')
        walkin_type = request.POST.get('walkin_type')
        price = request.POST.get('price')
        amount = request.POST.get('amount')

        if not customer_id:
            return redirect('walkin')

        customer = Customer.objects.get(id=customer_id)

        # 🔥 MONTHLY = FREE
        if entry_type == 'monthly':
            price = 0
            amount = 0
        else:
            price = float(price or 0)
            amount = float(amount or 0)

        DailyEntry.objects.create(
            customer=customer,
            entry_type=entry_type,
            walkin_type=walkin_type,
            price=price,
            amount_paid=amount,
            change=amount - price
        )

        return redirect('home')

    return render(request, 'walkin.html', {
        'customers': customers,
        'monthly_ids': list(monthly_ids)
    })

@login_required
def register_membership(request):
    today = date.today()

    # 🔥 FILTER ACTIVE MEMBERS
    customers = Customer.objects.exclude(
        id__in=MembershipLog.objects.filter(
            end_date__gte=today
        ).values_list('customer_id', flat=True)
    )

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        second_customer_id = request.POST.get('second_customer')
        entry_type = request.POST.get('entry_type')
        price = float(request.POST.get('price') or 0)
        amount = float(request.POST.get('amount') or 0)

        if not customer_id:
            return redirect('membership')

        customer = Customer.objects.get(id=customer_id)

        if entry_type == 'membership':
            customer.is_member = True
            customer.save()

            start = date.today()
            end = start + relativedelta(years=1)

            MembershipLog.objects.create(
                customer=customer,
                start_date=start,
                end_date=end
            )

            # ✔ KEEP (for earnings)
            DailyEntry.objects.create(
                customer=customer,
                entry_type='membership',
                price=price,
                amount_paid=amount,
                change=amount - price
            )

        elif entry_type == 'promo':
            if not second_customer_id:
                return redirect('membership')

            second_customer = Customer.objects.get(id=second_customer_id)

            customer.is_member = True
            second_customer.is_member = True
            customer.save()
            second_customer.save()

            for c in [customer, second_customer]:
                start = date.today()
                end = start + relativedelta(years=1)

                MembershipLog.objects.create(
                    customer=c,
                    start_date=start,
                    end_date=end
                )

            per_person = price / 2

            for c in [customer, second_customer]:
                DailyEntry.objects.create(
                    customer=c,
                    entry_type='membership_promo',
                    price=per_person,
                    amount_paid=per_person,
                    change=0
                )

        return redirect('home')

    return render(request, 'membership.html', {'customers': customers})

@login_required
def register_monthly(request):
    today = date.today()

    # 🔥 FILTER:
    # ✔ member
    # ✔ walang active monthly
    customers = Customer.objects.filter(is_member=True).exclude(
        id__in=Membership.objects.filter(
            end_date__gte=today
        ).values_list('customer_id', flat=True)
    )

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        plan = request.POST.get('plan')
        start_date = request.POST.get('start_date')
        price = request.POST.get('price')
        amount = request.POST.get('amount')

        if not customer_id or not start_date or not plan:
            return redirect('monthly')

        customer = Customer.objects.get(id=customer_id)

        if not customer.is_member:
            return redirect('monthly')

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        if plan == '1_month':
            end_date = start_date + relativedelta(months=1)
        elif plan == '3_months':
            end_date = start_date + relativedelta(months=3)
        elif plan == '12_months':
            end_date = start_date + relativedelta(years=1)
        else:
            end_date = start_date + relativedelta(months=1)

        Membership.objects.update_or_create(
            customer=customer,
            defaults={
                'plan': plan,
                'start_date': start_date,
                'end_date': end_date
            }
        )

        # ✔ KEEP (for earnings)
        if price and amount:
            DailyEntry.objects.create(
                customer=customer,
                entry_type='monthly',
                price=float(price),
                amount_paid=float(amount),
                change=float(amount) - float(price)
            )

        return redirect('home')

    return render(request, 'monthly.html', {'customers': customers})

@login_required
def add_customer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        customer_type = request.POST.get('customer_type')

        Customer.objects.create(
            name=name,
            contact_number=contact,
            address=address,
            customer_type=customer_type
        )

        return redirect('home')

    return render(request, 'add_customer.html')

@login_required
def edit_customer(request, id):
    customer = Customer.objects.get(id=id)

    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.customer_type = request.POST.get('customer_type')
        customer.contact_number = request.POST.get('contact')
        customer.address = request.POST.get('address')   
        customer.is_member = 'is_member' in request.POST
        customer.save()

        return redirect('home')

    return render(request, 'edit_customer.html', {'customer': customer})

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'customers.html', {'customers': customers})

@login_required
def members_list(request):
    members = Customer.objects.filter(is_member=True)

    # 🔥 ADD START DATE
    for m in members:
        log = MembershipLog.objects.filter(customer=m).order_by('-start_date').first()
        m.start_date = log.start_date if log else None
        m.end_date = log.end_date if log else None

    return render(request, 'members.html', {'members': members})

@login_required
def monthly_list(request):
    today = date.today()
    monthly = Membership.objects.filter(end_date__gte=today)
    return render(request, 'monthly_list.html', {'monthly': monthly})

@login_required
def pos(request):
    products = Product.objects.all()
    
    if request.method == "POST":
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('qty')
        
        sale = Sale.objects.create(total=0)
        total = 0
        
        for pid, qty in zip(product_ids, quantities):
            if not qty:
                continue
        
            product = Product.objects.get(id=pid)
            qty = int(qty)
            
            if product.stock < qty:
                continue
            
            subtotal = product.price * qty
            total += subtotal
            
            product.stock -= qty
            product.save()
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                subtotal=subtotal
            )
            
        sale.total = total
        sale.save()
        
        return redirect('home')

    return render(request, 'pos.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        
        if not name or not price or not stock:
            return redirect('add_product')

        try:
            price = float(price)
            stock = int(stock)
        except:
            return redirect('add_product')
        
        Product.objects.create(
            name=name,
            price=price,
            stock=stock
        )
        
        return redirect('products')
    
    return render(request, 'add_product.html')

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

@login_required
def edit_product(request, id):
    product = Product.objects.get(id=id)
    
    if request.method == "POST":
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.save()
        
        return redirect('products')
    
    return render(request, 'edit_product.html', {'product': product})

@login_required
def edit_monthly(request, id):
    monthly = Membership.objects.get(id=id)

    if request.method == 'POST':
        monthly.plan = request.POST.get('plan')

        end_date = request.POST.get('end_date')

        if end_date:
            monthly.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        monthly.save()

        return redirect('monthly_list')

    return render(request, 'edit_monthly.html', {'monthly': monthly})

@login_required
def delete_monthly(request, id):
    monthly = Membership.objects.get(id=id)

    if request.method == "POST":
        monthly.delete()
        return redirect('monthly_list')
    
@login_required
def today_logs(request):
    today = date.today()
    logs = DailyEntry.objects.filter(date=today).order_by('-id')
    
    return render(request, 'today_logs.html', {
        'logs': logs
    })
    
@login_required
def edit_member(request, id):
    customer = Customer.objects.get(id=id)

    membership_log = MembershipLog.objects.filter(customer=customer).order_by('-start_date').first()

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if membership_log:
            if start_date:
                membership_log.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

            if end_date:
                membership_log.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            membership_log.save()

        return redirect('members')

    return render(request, 'edit_member.html', {
        'customer': customer,
        'membership_log': membership_log
    })
   
@login_required 
def export_report(request):
    # 🔹 DAILY LOGS
    daily = DailyEntry.objects.all().values(
        'customer__name', 'entry_type', 'price', 'date'
    )
    df_daily = pd.DataFrame(list(daily))

    # 🔹 YEARLY MEMBERSHIP
    membership = MembershipLog.objects.all().values(
        'customer__name', 'start_date', 'end_date'
    )
    df_membership = pd.DataFrame(list(membership))

    # 🔹 MONTHLY
    monthly = Membership.objects.all().values(
        'customer__name', 'plan', 'start_date', 'end_date'
    )
    df_monthly = pd.DataFrame(list(monthly))

    sales = SaleItem.objects.all().values(
        'product__name',
        'quantity',
        'sale__date',
        'subtotal'
    )

    df_sales = pd.DataFrame(list(sales))

    # 🔥 RENAME PARA MALINIS
    if not df_sales.empty:
        df_sales.rename(columns={
            'sale__date': 'date',
            'product__name': 'product'
        }, inplace=True)

        df_sales['date'] = pd.to_datetime(df_sales['date']).dt.tz_localize(None)

    # 🔥 CREATE EXCEL FILE
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="gym_report.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df_daily.to_excel(writer, sheet_name='Daily Logs', index=False)
        df_membership.to_excel(writer, sheet_name='Yearly Membership', index=False)
        df_monthly.to_excel(writer, sheet_name='Monthly', index=False)
        df_sales.to_excel(writer, sheet_name='Sales', index=False)

    return response