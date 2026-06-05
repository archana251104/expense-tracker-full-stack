# tracker/views.py

from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.contrib.auth import login # type: ignore
from django.contrib import messages # type: ignore
from django.db.models import Sum # type: ignore
from django.http import HttpResponse # type: ignore
from datetime import datetime, timedelta
import json
import csv
from .models import Expense, Budget
from .forms import ExpenseForm, BudgetForm, RegisterForm

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})

@login_required
def index(request):
    expenses = Expense.objects.filter(user=request.user)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)
    
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    category_data = {}
    category_colors = {
        'Food': '#f48fb1', 'Transport': '#ffb6c1', 'Shopping': '#d8b4fe',
        'Entertainment': '#c4b5fd', 'Bills': '#a78bfa', 'Healthcare': '#f9a8d4',
        'Education': '#f472b6', 'Other': '#ec4899',
    }
    
    for expense in expenses:
        if expense.category in category_data:
            category_data[expense.category] += float(expense.amount)
        else:
            category_data[expense.category] = float(expense.amount)
    
    category_labels = list(category_data.keys())
    category_amounts = list(category_data.values())
    category_color_list = [category_colors.get(cat, '#c084fc') for cat in category_labels]
    
    monthly_data = {}
    today = datetime.now().date()
    for i in range(12):
        month_date = today.replace(day=1) - timedelta(days=30 * i)
        month_name = month_date.strftime('%b %Y')
        monthly_data[month_name] = 0
    
    for expense in expenses:
        month_name = expense.date.strftime('%b %Y')
        if month_name in monthly_data:
            monthly_data[month_name] += float(expense.amount)
    
    months = list(monthly_data.keys())[::-1]
    monthly_amounts = list(monthly_data.values())[::-1]
    
    daily_data = {}
    for i in range(30):
        day = (today - timedelta(days=i)).strftime('%d %b')
        daily_data[day] = 0
    
    for expense in expenses.filter(date__gte=today - timedelta(days=30)):
        day_name = expense.date.strftime('%d %b')
        if day_name in daily_data:
            daily_data[day_name] += float(expense.amount)
    
    days = list(daily_data.keys())[::-1]
    daily_amounts = list(daily_data.values())[::-1]
    
    current_month = today.replace(day=1)
    budget_alerts = []
    budgets = Budget.objects.filter(user=request.user, month=current_month)
    
    for budget in budgets:
        spent = expenses.filter(category=budget.category, date__year=today.year, date__month=today.month).aggregate(Sum('amount'))['amount__sum'] or 0
        if spent > budget.monthly_limit:
            percentage = (spent / budget.monthly_limit) * 100
            budget_alerts.append({
                'category': budget.category,
                'limit': float(budget.monthly_limit),
                'spent': float(spent),
                'percentage': round(percentage, 1)
            })
    
    top_category = max(category_data, key=category_data.get) if category_data else 'None'
    top_category_amount = category_data.get(top_category, 0)
    days_with_expenses = expenses.values('date').distinct().count()
    avg_daily = total / max(1, days_with_expenses)
    
    context = {
        'expenses': expenses[:100],
        'total': total,
        'expense_count': expenses.count(),
        'category_labels': json.dumps(category_labels),
        'category_amounts': json.dumps(category_amounts),
        'category_colors': json.dumps(category_color_list),
        'months': json.dumps(months),
        'monthly_amounts': json.dumps(monthly_amounts),
        'days': json.dumps(days),
        'daily_amounts': json.dumps(daily_amounts),
        'top_category': top_category,
        'top_category_amount': top_category_amount,
        'avg_daily': round(avg_daily, 2),
        'budget_alerts': budget_alerts,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'tracker/index.html', context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('index')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/add_expense.html', {'form': form})

@login_required
def edit_expense(request, id):
    expense = get_object_or_404(Expense, id=id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('index')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'tracker/edit_expense.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, id):
    expense = get_object_or_404(Expense, id=id, user=request.user)
    expense.delete()
    messages.success(request, 'Expense deleted successfully!')
    return redirect('index')

# tracker/views.py (Only the budget_settings function - updated)

@login_required
def budget_settings(request):
    from datetime import datetime
    
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            # Auto-set month to current month
            budget.month = datetime.now().date().replace(day=1)
            
            # Check if budget already exists for this category this month
            existing = Budget.objects.filter(
                user=request.user,
                category=budget.category,
                month=budget.month
            ).first()
            
            if existing:
                existing.monthly_limit = budget.monthly_limit
                existing.save()
                messages.success(request, f'Budget for {budget.category} updated successfully!')
            else:
                budget.save()
                messages.success(request, f'Budget for {budget.category} set successfully!')
            return redirect('budget_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BudgetForm()
    
    # Get current month's budgets
    today = datetime.now().date()
    current_month = today.replace(day=1)
    
    budgets = Budget.objects.filter(user=request.user, month=current_month)
    
    spending_data = []
    for budget in budgets:
        spent = Expense.objects.filter(
            user=request.user,
            category=budget.category,
            date__year=today.year,
            date__month=today.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        remaining = float(budget.monthly_limit) - float(spent)
        percentage = (float(spent) / float(budget.monthly_limit)) * 100 if float(budget.monthly_limit) > 0 else 0
        width = max(0, min(100, round(percentage, 1)))
        
        spending_data.append({
            'category': budget.category,
            'limit': float(budget.monthly_limit),
            'spent': float(spent),
            'remaining': round(remaining, 2),
            'percentage': round(percentage, 1),
            'width': width,
        })
    
    context = {
        'form': form,
        'spending_data': spending_data,
    }
    return render(request, 'tracker/budget_settings.html', context)

@login_required
def export_csv(request):
    expenses = Expense.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Description', 'Amount'])
    for expense in expenses:
        writer.writerow([expense.date, expense.category, expense.description, expense.amount])
    return response

@login_required
def export_chart_data(request):
    expenses = Expense.objects.filter(user=request.user)
    category_data = {}
    for expense in expenses:
        if expense.category in category_data:
            category_data[expense.category] += float(expense.amount)
        else:
            category_data[expense.category] = float(expense.amount)
    data = {'category_chart': {'labels': list(category_data.keys()), 'values': list(category_data.values())}}
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="chart_data.json"'
    return response

@login_required
def profile(request):
    if request.method == 'POST':
        request.user.email = request.POST.get('email')
        request.user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    expenses = Expense.objects.filter(user=request.user)
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_avg = total_expenses / max(1, expenses.dates('date', 'month').count())
    
    context = {
        'total_expenses': total_expenses,
        'monthly_avg': round(monthly_avg, 2),
        'total_transactions': expenses.count(),
    }
    return render(request, 'tracker/profile.html', context)