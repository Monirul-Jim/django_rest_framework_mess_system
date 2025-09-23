from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Mess, Meal, MonthlyCalculation, MemberMealSummary,MemberContribution,MemberRequest

User = get_user_model()
class MemberRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberRequest
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "email",
            "phone",
            "tran_id",
            "description",
            "status",
            "created_at"
        ]
        read_only_fields = ["id", "user", "status", "created_at"]

        

class UserBasicSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'phone', 'first_name', 'last_name')
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class MemberRequestSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MemberRequest
        fields = ('id', 'user', 'first_name', 'last_name', 'email', 'phone', 'tran_id', 'description', 'status', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

class MemberContributionSerializer(serializers.ModelSerializer):
    member = UserBasicSerializer(read_only=True)
    added_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MemberContribution
        fields = ('id', 'mess', 'member', 'month', 'amount', 'description', 'added_by', 'created_at')
        read_only_fields = ('id', 'mess', 'added_by', 'created_at')

class MemberContributionCreateSerializer(serializers.ModelSerializer):
    member_id = serializers.IntegerField()
    
    class Meta:
        model = MemberContribution
        fields = ('member_id', 'month', 'amount', 'description')
    
    def validate_member_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Member not found")
        return value

class MessSerializer(serializers.ModelSerializer):
    owner = UserBasicSerializer(read_only=True)
    members = UserBasicSerializer(many=True, read_only=True)
    managers = UserBasicSerializer(many=True, read_only=True)
    
    class Meta:
        model = Mess
        fields = ('id', 'name', 'description', 'owner', 'members', 'managers', 'created_at', 'updated_at')
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

class MessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mess
        fields = ('name', 'description')

class AddMemberSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    
    def validate_phone(self, value):
        try:
            user = User.objects.get(phone=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this phone number not found")
        return value

class AddManagerSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value

class MealSerializer(serializers.ModelSerializer):
    member = UserBasicSerializer(read_only=True)
    added_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Meal
        fields = ('id', 'mess', 'member', 'date', 'meal_count', 'added_by', 'created_at')
        read_only_fields = ('id', 'mess', 'added_by', 'created_at')

class MealCreateSerializer(serializers.ModelSerializer):
    member_id = serializers.IntegerField()
    
    class Meta:
        model = Meal
        fields = ('date', 'member_id', 'meal_count')
    
    def validate_member_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Member not found")
        return value

class MemberMealSummarySerializer(serializers.ModelSerializer):
    member = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MemberMealSummary
        fields = ('member', 'total_meals', 'total_cost', 'contributed_amount', 'balance')

class MonthlyCalculationSerializer(serializers.ModelSerializer):
    calculated_by = UserBasicSerializer(read_only=True)
    member_summaries = MemberMealSummarySerializer(many=True, read_only=True)
    member_meals = serializers.SerializerMethodField()
    member_costs = serializers.SerializerMethodField()
    member_contributions = serializers.SerializerMethodField()
    member_balances = serializers.SerializerMethodField()
    
    class Meta:
        model = MonthlyCalculation
        fields = (
            'id', 'mess', 'month', 'bazaar_cost', 'extra_cost', 'total_cost',
            'total_meals', 'cost_per_meal', 'calculated_by', 'calculated_at',
            'member_summaries', 'member_meals', 'member_costs', 'member_contributions', 'member_balances'
        )
        read_only_fields = ('id', 'mess', 'calculated_by', 'calculated_at')
    
    def get_member_meals(self, obj):
        return {str(summary.member.id): summary.total_meals for summary in obj.member_summaries.all()}
    
    def get_member_costs(self, obj):
        return {str(summary.member.id): float(summary.total_cost) for summary in obj.member_summaries.all()}
    
    def get_member_contributions(self, obj):
        return {str(summary.member.id): float(summary.contributed_amount) for summary in obj.member_summaries.all()}
    
    def get_member_balances(self, obj):
        return {str(summary.member.id): float(summary.balance) for summary in obj.member_summaries.all()}

class MonthlyCalculationCreateSerializer(serializers.Serializer):
    member_contributions = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of member contributions: [{'member_id': 1, 'amount': 2100}, ...]"
    )
    extra_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def validate_member_contributions(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one member contribution is required")
        
        for contribution in value:
            if 'member_id' not in contribution or 'amount' not in contribution:
                raise serializers.ValidationError("Each contribution must have 'member_id' and 'amount'")
            
            try:
                User.objects.get(id=contribution['member_id'])
            except User.DoesNotExist:
                raise serializers.ValidationError(f"Member with ID {contribution['member_id']} not found")
        
        return value
# class MemberRequestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MemberRequest
#         fields = [
#             "id",
#             "user",
#             "first_name",
#             "last_name",
#             "email",
#             "phone",
#             "tran_id",
#             "description",
#             "status",
#             "created_at"
#         ]
#         read_only_fields = ["id", "user", "status", "created_at"]

        
# class UserBasicSerializer(serializers.ModelSerializer):
#     name = serializers.SerializerMethodField()
    
#     class Meta:
#         model = User
#         fields = ('id', 'email', 'name', 'phone', 'first_name', 'last_name')
    
#     def get_name(self, obj):
#         return f"{obj.first_name} {obj.last_name}".strip()

# class MessSerializer(serializers.ModelSerializer):
#     owner = UserBasicSerializer(read_only=True)
#     members = UserBasicSerializer(many=True, read_only=True)
#     managers = UserBasicSerializer(many=True, read_only=True)
    
#     class Meta:
#         model = Mess
#         fields = ('id', 'name', 'description', 'owner', 'members', 'managers', 'created_at', 'updated_at')
#         read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

# class MessCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Mess
#         fields = ('name', 'description')

# class AddMemberSerializer(serializers.Serializer):
#     phone = serializers.CharField(max_length=15)
    
#     def validate_phone(self, value):
#         try:
#             user = User.objects.get(phone=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User with this phone number not found")
#         return value

# class AddManagerSerializer(serializers.Serializer):
#     user_id = serializers.IntegerField()
    
#     def validate_user_id(self, value):
#         try:
#             user = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User not found")
#         return value

# class MealSerializer(serializers.ModelSerializer):
#     member = UserBasicSerializer(read_only=True)
#     added_by = UserBasicSerializer(read_only=True)
    
#     class Meta:
#         model = Meal
#         fields = ('id', 'mess', 'member', 'date', 'meal_count', 'added_by', 'created_at')
#         read_only_fields = ('id', 'mess', 'added_by', 'created_at')

# class MealCreateSerializer(serializers.ModelSerializer):
#     member_id = serializers.IntegerField()
    
#     class Meta:
#         model = Meal
#         fields = ('date', 'member_id', 'meal_count')
    
#     def validate_member_id(self, value):
#         try:
#             user = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Member not found")
#         return value

# class MemberMealSummarySerializer(serializers.ModelSerializer):
#     member = UserBasicSerializer(read_only=True)
    
#     class Meta:
#         model = MemberMealSummary
#         fields = ('member', 'total_meals', 'total_cost')

# class MonthlyCalculationSerializer(serializers.ModelSerializer):
#     calculated_by = UserBasicSerializer(read_only=True)
#     member_summaries = MemberMealSummarySerializer(many=True, read_only=True)
#     member_meals = serializers.SerializerMethodField()
#     member_costs = serializers.SerializerMethodField()
    
#     class Meta:
#         model = MonthlyCalculation
#         fields = (
#             'id', 'mess', 'month', 'bazaar_cost', 'extra_cost', 'total_cost',
#             'total_meals', 'cost_per_meal', 'calculated_by', 'calculated_at',
#             'member_summaries', 'member_meals', 'member_costs'
#         )
#         read_only_fields = ('id', 'mess', 'calculated_by', 'calculated_at')
    
#     def get_member_meals(self, obj):
#         return {str(summary.member.id): summary.total_meals for summary in obj.member_summaries.all()}
    
#     def get_member_costs(self, obj):
#         return {str(summary.member.id): float(summary.total_cost) for summary in obj.member_summaries.all()}

# class MonthlyCalculationCreateSerializer(serializers.Serializer):
#     bazaar_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
#     extra_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)