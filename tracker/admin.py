from django.contrib import admin
from .models import Expense, Budget

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'category', 'date', 'description')
    list_filter = ('category', 'date', 'user')
    search_fields = ('user__username', 'category', 'description')
    date_hierarchy = 'date'
    ordering = ('-date',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'monthly_limit', 'month')
    list_filter = ('category', 'month', 'user')
    search_fields = ('user__username', 'category')
    ordering = ('-month',)