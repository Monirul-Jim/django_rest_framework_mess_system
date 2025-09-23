from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


STATUS_CHOICES = [
    ("Pending", "Pending"),
    ("Approved", "Approved"),
]

class MemberRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    tran_id = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.status}"

class Mess(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_messes')
    members = models.ManyToManyField(User, related_name='joined_messes', blank=True)
    managers = models.ManyToManyField(User, related_name='managed_messes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Add owner as member and manager
            self.members.add(self.owner)
            self.managers.add(self.owner)
    
    class Meta:
        db_table = 'messes'
        verbose_name_plural = 'Messes'

class Meal(models.Model):
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='meals')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meals')
    date = models.DateField()
    meal_count = models.PositiveSmallIntegerField(
        choices=[(0, '0 meals'), (1, '1 meal'), (2, '2 meals'), (3, '3 meals')],
        default=0
    )
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_meals')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.first_name} - {self.date} - {self.meal_count} meals"
    
    class Meta:
        db_table = 'meals'
        unique_together = ('mess', 'member', 'date')

class MonthlyCalculation(models.Model):
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='calculations')
    month = models.CharField(max_length=7)  # YYYY-MM format
    bazaar_cost = models.DecimalField(max_digits=10, decimal_places=2)
    extra_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_meals = models.PositiveIntegerField()
    cost_per_meal = models.DecimalField(max_digits=8, decimal_places=2)
    calculated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calculations')
    calculated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mess.name} - {self.month}"
    
    class Meta:
        db_table = 'monthly_calculations'
        unique_together = ('mess', 'month')

class MemberContribution(models.Model):
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='contributions')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    month = models.CharField(max_length=7)  # YYYY-MM format
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_contributions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.first_name} - {self.month} - ৳{self.amount}"
    
    class Meta:
        db_table = 'member_contributions'
        unique_together = ('mess', 'member', 'month')

class MemberMealSummary(models.Model):
    calculation = models.ForeignKey(MonthlyCalculation, on_delete=models.CASCADE, related_name='member_summaries')
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    total_meals = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
    contributed_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # positive = should receive, negative = should pay

    def __str__(self):
        return f"{self.member.first_name} - {self.calculation.month} - ৳{self.total_cost}"
    
    class Meta:
        db_table = 'member_meal_summaries'
        unique_together = ('calculation', 'member')
        
# STATUS_CHOICES = [
#     ("Pending", "Pending"),
#     ("Approved", "Approved"),
# ]

# class MemberRequest(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     first_name = models.CharField(max_length=150)
#     last_name = models.CharField(max_length=150)
#     email = models.EmailField()
#     phone = models.CharField(max_length=15)
#     tran_id = models.CharField(max_length=100)
#     description = models.TextField(blank=True)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user.email} - {self.status}"
    
    
# class Mess(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField(blank=True)
#     owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_messes')
#     members = models.ManyToManyField(User, related_name='joined_messes', blank=True)
#     managers = models.ManyToManyField(User, related_name='managed_messes', blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.name
    
#     def save(self, *args, **kwargs):
#         is_new = self.pk is None
#         super().save(*args, **kwargs)
#         if is_new:
#             # Add owner as member and manager
#             self.members.add(self.owner)
#             self.managers.add(self.owner)
    
#     class Meta:
#         db_table = 'messes'
#         verbose_name_plural = 'Messes'

# class Meal(models.Model):
#     mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='meals')
#     member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meals')
#     date = models.DateField()
#     meal_count = models.PositiveSmallIntegerField(
#         choices=[(0, '0 meals'), (1, '1 meal'), (2, '2 meals'), (3, '3 meals')],
#         default=0
#     )
#     added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_meals')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.member.first_name} - {self.date} - {self.meal_count} meals"
    
#     class Meta:
#         db_table = 'meals'
#         unique_together = ('mess', 'member', 'date')

# class MonthlyCalculation(models.Model):
#     mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='calculations')
#     month = models.CharField(max_length=7)  # YYYY-MM format
#     bazaar_cost = models.DecimalField(max_digits=10, decimal_places=2)
#     extra_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     total_cost = models.DecimalField(max_digits=10, decimal_places=2)
#     total_meals = models.PositiveIntegerField()
#     cost_per_meal = models.DecimalField(max_digits=8, decimal_places=2)
#     calculated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calculations')
#     calculated_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.mess.name} - {self.month}"
    
#     class Meta:
#         db_table = 'monthly_calculations'
#         unique_together = ('mess', 'month')
# class MemberContribution(models.Model):
#     mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='contributions')
#     member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
#     month = models.CharField(max_length=7)  # YYYY-MM format
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     description = models.TextField(blank=True)
#     added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_contributions')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.member.first_name} - {self.month} - ৳{self.amount}"
    
#     class Meta:
#         db_table = 'member_contributions'
#         unique_together = ('mess', 'member', 'month')

# class MemberMealSummary(models.Model):
#     calculation = models.ForeignKey(MonthlyCalculation, on_delete=models.CASCADE, related_name='member_summaries')
#     member = models.ForeignKey(User, on_delete=models.CASCADE)
#     total_meals = models.PositiveIntegerField()
#     total_cost = models.DecimalField(max_digits=8, decimal_places=2)

#     def __str__(self):
#         return f"{self.member.first_name} - {self.calculation.month} - ৳{self.total_cost}"
    
#     class Meta:
#         db_table = 'member_meal_summaries'
#         unique_together = ('calculation', 'member')