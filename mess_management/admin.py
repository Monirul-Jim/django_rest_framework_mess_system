from django.contrib import admin
from .models import Mess, Meal, MonthlyCalculation, MemberMealSummary,MemberRequest,MemberContribution


@admin.register(Mess)
class MessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'member_count', 'manager_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__email', 'owner__first_name', 'owner__last_name')
    filter_horizontal = ('members', 'managers')
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'
    
    def manager_count(self, obj):
        return obj.managers.count()
    manager_count.short_description = 'Managers'

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('member', 'mess', 'date', 'meal_count', 'added_by', 'created_at')
    list_filter = ('date', 'meal_count', 'created_at')
    search_fields = ('member__email', 'member__first_name', 'mess__name')
    date_hierarchy = 'date'

@admin.register(MonthlyCalculation)
class MonthlyCalculationAdmin(admin.ModelAdmin):
    list_display = ('mess', 'month', 'total_cost', 'total_meals', 'cost_per_meal', 'calculated_by', 'calculated_at')
    list_filter = ('month', 'calculated_at')
    search_fields = ('mess__name', 'calculated_by__email')
    readonly_fields = ('total_cost', 'cost_per_meal', 'calculated_at')

@admin.register(MemberRequest)
class MemberRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'first_name', 'last_name', 'phone')

@admin.register(MemberContribution)
class MemberContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'mess', 'month', 'amount', 'added_by', 'created_at')
    list_filter = ('month', 'created_at', 'mess')
    search_fields = ('member__email', 'member__first_name', 'mess__name')

@admin.register(MemberMealSummary)
class MemberMealSummaryAdmin(admin.ModelAdmin):
    list_display = ('member', 'calculation', 'total_meals', 'total_cost', 'contributed_amount', 'balance')
    list_filter = ('calculation__month', 'calculation__mess')
    search_fields = ('member__email', 'member__first_name', 'calculation__mess__name')