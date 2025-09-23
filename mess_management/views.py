from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum
from datetime import datetime
from .models import Mess, Meal, MonthlyCalculation, MemberMealSummary,MemberRequest,MemberContribution
from .serializers import (
    MessSerializer, MessCreateSerializer, AddMemberSerializer, AddManagerSerializer,
    MealSerializer, MealCreateSerializer, MonthlyCalculationSerializer,
    MonthlyCalculationCreateSerializer,MemberRequestSerializer,MemberContributionSerializer,MemberContributionCreateSerializer
)
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
User = get_user_model()

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def become_member_request(request):
    user = request.user

    if request.method == "POST":
        # Create a new member request
        data = request.data
        serializer = MemberRequestSerializer(data={
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "tran_id": data.get("tran_id"),
            "description": data.get("description")
        })
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({
                "message": "Member request submitted successfully",
                "request": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == "GET":
        # List member requests for the logged-in user
        requests = MemberRequest.objects.filter(user=user)
        serializer = MemberRequestSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def all_member_requests(request):
    requests = MemberRequest.objects.all()
    serializer = MemberRequestSerializer(requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def approve_member_request(request, pk):
    try:
        member_request = MemberRequest.objects.get(pk=pk)
    except MemberRequest.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get("status", "Approved")
    if new_status not in ["Pending", "Approved"]:
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    member_request.status = new_status
    member_request.save()
    return Response({
        "message": "Status updated",
        "request": MemberRequestSerializer(member_request).data
    }, status=status.HTTP_200_OK)

class MessViewSet(ModelViewSet):
    serializer_class = MessSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Mess.objects.filter(members=self.request.user).prefetch_related(
            'members', 'managers', 'owner'
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessCreateSerializer
        return MessSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        mess = self.get_object()
        
        # Check if user is manager
        if not mess.managers.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Only managers can add members'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AddMemberSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            try:
                user = User.objects.get(phone=phone)
                if mess.members.filter(id=user.id).exists():
                    return Response(
                        {'error': 'User is already a member'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                mess.members.add(user)
                mess_serializer = MessSerializer(mess)
                return Response({'mess': mess_serializer.data}, status=status.HTTP_200_OK)
            
            except User.DoesNotExist:
                return Response(
                    {'error': 'User with this phone number not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_manager(self, request, pk=None):
        mess = self.get_object()
        
        # Check if user is owner
        if mess.owner != request.user:
            return Response(
                {'error': 'Only owner can add managers'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AddManagerSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user = User.objects.get(id=user_id)
                if not mess.members.filter(id=user.id).exists():
                    return Response(
                        {'error': 'User is not a member of this mess'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                mess.managers.add(user)
                mess_serializer = MessSerializer(mess)
                return Response({'mess': mess_serializer.data}, status=status.HTTP_200_OK)
            
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_meal(request, mess_id):
    mess = get_object_or_404(Mess, id=mess_id)
    
    # Check if user is manager
    if not mess.managers.filter(id=request.user.id).exists():
        return Response(
            {'error': 'Only managers can add meals'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = MealCreateSerializer(data=request.data)
    if serializer.is_valid():
        member_id = serializer.validated_data['member_id']
        try:
            member = User.objects.get(id=member_id)
            if not mess.members.filter(id=member.id).exists():
                return Response(
                    {'error': 'User is not a member of this mess'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create or update meal
            meal, created = Meal.objects.update_or_create(
                mess=mess,
                member=member,
                date=serializer.validated_data['date'],
                defaults={
                    'meal_count': serializer.validated_data['meal_count'],
                    'added_by': request.user
                }
            )
            
            return Response({'success': True}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_meals(request, mess_id, month):
    mess = get_object_or_404(Mess, id=mess_id)
    
    # Check if user is member
    if not mess.members.filter(id=request.user.id).exists():
        return Response(
            {'error': 'Not a member of this mess'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get meals for the month
    meals = Meal.objects.filter(
        mess=mess,
        date__startswith=month
    ).select_related('member', 'added_by')
    
    serializer = MealSerializer(meals, many=True)
    return Response({'meals': serializer.data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def calculate_month(request, mess_id, month):
    mess = get_object_or_404(Mess, id=mess_id)
    
    # Check if user is manager
    if not mess.managers.filter(id=request.user.id).exists():
        return Response(
            {'error': 'Only managers can calculate monthly costs'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = MonthlyCalculationCreateSerializer(data=request.data)
    if serializer.is_valid():
        member_contributions_data = serializer.validated_data['member_contributions']
        extra_cost = serializer.validated_data['extra_cost']
        
        # Calculate total bazaar cost from individual contributions
        # total_bazaar_cost = sum(float(contrib['amount']) for contrib in member_contributions_data)
        # total_cost = total_bazaar_cost + extra_cost
        total_bazaar_cost = sum(Decimal(contrib['amount']) for contrib in member_contributions_data)
        extra_cost = Decimal(extra_cost)  # ensure extra_cost is Decimal
        total_cost = total_bazaar_cost + extra_cost

        
        # Get all meals for the month
        meals = Meal.objects.filter(
            mess=mess,
            date__startswith=month
        ).values('member').annotate(
            total_meals=Sum('meal_count')
        )
        
        # Calculate totals
        total_meals = sum(meal['total_meals'] for meal in meals)
        # cost_per_meal = total_cost / total_meals if total_meals > 0 else 0
        cost_per_meal = (total_cost / total_meals) if total_meals > 0 else Decimal("0")
        
        # Create or update calculation
        calculation, created = MonthlyCalculation.objects.update_or_create(
            mess=mess,
            month=month,
            defaults={
                'bazaar_cost': total_bazaar_cost,
                'extra_cost': extra_cost,
                'total_cost': total_cost,
                'total_meals': total_meals,
                'cost_per_meal': cost_per_meal,
                'calculated_by': request.user
            }
        )
        
        # Delete existing member summaries and contributions
        MemberMealSummary.objects.filter(calculation=calculation).delete()
        MemberContribution.objects.filter(mess=mess, month=month).delete()
        
        # Create member contributions
        contributions_dict = {}
        for contrib_data in member_contributions_data:
            member = User.objects.get(id=contrib_data['member_id'])
            # amount = float(contrib_data['amount'])
            amount = Decimal(contrib_data['amount'])

            
            MemberContribution.objects.create(
                mess=mess,
                member=member,
                month=month,
                amount=amount,
                description=contrib_data.get('description', ''),
                added_by=request.user
            )
            contributions_dict[member.id] = amount
        
        # Create member summaries
        for meal in meals:
            member = User.objects.get(id=meal['member'])
            member_cost = meal['total_meals'] * cost_per_meal
            contributed_amount = contributions_dict.get(member.id, 0)
            balance = contributed_amount - member_cost  # positive = should receive, negative = should pay
            
            MemberMealSummary.objects.create(
                calculation=calculation,
                member=member,
                total_meals=meal['total_meals'],
                total_cost=member_cost,
                contributed_amount=contributed_amount,
                balance=balance
            )
        
        calculation_serializer = MonthlyCalculationSerializer(calculation)
        return Response({'calculation': calculation_serializer.data}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_calculation(request, mess_id, month):
    mess = get_object_or_404(Mess, id=mess_id)
    
    # Check if user is member
    if not mess.members.filter(id=request.user.id).exists():
        return Response(
            {'error': 'Not a member of this mess'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        calculation = MonthlyCalculation.objects.get(mess=mess, month=month)
        serializer = MonthlyCalculationSerializer(calculation)
        return Response({'calculation': serializer.data}, status=status.HTTP_200_OK)
    except MonthlyCalculation.DoesNotExist:
        return Response({'calculation': None}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def manage_contributions(request, mess_id, month):
    mess = get_object_or_404(Mess, id=mess_id)
    
    # Check if user is member
    if not mess.members.filter(id=request.user.id).exists():
        return Response(
            {'error': 'Not a member of this mess'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'GET':
        # Get contributions for the month
        contributions = MemberContribution.objects.filter(
            mess=mess,
            month=month
        ).select_related('member', 'added_by')
        
        serializer = MemberContributionSerializer(contributions, many=True)
        return Response({'contributions': serializer.data}, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Only managers can add contributions
        if not mess.managers.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Only managers can add contributions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MemberContributionCreateSerializer(data=request.data)
        if serializer.is_valid():
            member_id = serializer.validated_data['member_id']
            try:
                member = User.objects.get(id=member_id)
                if not mess.members.filter(id=member.id).exists():
                    return Response(
                        {'error': 'User is not a member of this mess'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create or update contribution
                contribution, created = MemberContribution.objects.update_or_create(
                    mess=mess,
                    member=member,
                    month=month,
                    defaults={
                        'amount': serializer.validated_data['amount'],
                        'description': serializer.validated_data.get('description', ''),
                        'added_by': request.user
                    }
                )
                
                return Response({'success': True}, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response(
                    {'error': 'Member not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
# def become_member_request(request):
#     user = request.user

#     if request.method == "POST":
#         # Create a new member request
#         data = request.data
#         serializer = MemberRequestSerializer(data={
#             "first_name": data.get("first_name"),
#             "last_name": data.get("last_name"),
#             "email": data.get("email"),
#             "phone": data.get("phone"),
#             "tran_id": data.get("tran_id"),
#             "description": data.get("description")
#         })
#         if serializer.is_valid():
#             serializer.save(user=user)
#             return Response({
#                 "message": "Member request submitted successfully",
#                 "request": serializer.data
#             }, status=status.HTTP_201_CREATED)
#         return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
#     elif request.method == "GET":
#         # List member requests for the logged-in user
#         requests = MemberRequest.objects.filter(user=user)
#         serializer = MemberRequestSerializer(requests, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def all_member_requests(request):
#     requests = MemberRequest.objects.all()
#     serializer = MemberRequestSerializer(requests, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)

# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def approve_member_request(request, pk):
#     try:
#         member_request = MemberRequest.objects.get(pk=pk)
#     except MemberRequest.DoesNotExist:
#         return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

#     new_status = request.data.get("status", "Approved")
#     if new_status not in ["Pending", "Approved"]:
#         return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

#     member_request.status = new_status
#     member_request.save()
#     return Response({
#         "message": "Status updated",
#         "request": MemberRequestSerializer(member_request).data
#     }, status=status.HTTP_200_OK)


# class MessViewSet(ModelViewSet):
#     serializer_class = MessSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         return Mess.objects.filter(members=self.request.user).prefetch_related(
#             'members', 'managers', 'owner'
#         )
    
#     def get_serializer_class(self):
#         if self.action == 'create':
#             return MessCreateSerializer
#         return MessSerializer
    
#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)
    
#     @action(detail=True, methods=['post'])
#     def add_member(self, request, pk=None):
#         mess = self.get_object()
        
#         # Check if user is manager
#         if not mess.managers.filter(id=request.user.id).exists():
#             return Response(
#                 {'error': 'Only managers can add members'}, 
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         serializer = AddMemberSerializer(data=request.data)
#         if serializer.is_valid():
#             phone = serializer.validated_data['phone']
#             try:
#                 user = User.objects.get(phone=phone)
#                 if mess.members.filter(id=user.id).exists():
#                     return Response(
#                         {'error': 'User is already a member'}, 
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
                
#                 mess.members.add(user)
#                 mess_serializer = MessSerializer(mess)
#                 return Response({'mess': mess_serializer.data}, status=status.HTTP_200_OK)
            
#             except User.DoesNotExist:
#                 return Response(
#                     {'error': 'User with this phone number not found'}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     @action(detail=True, methods=['post'])
#     def add_manager(self, request, pk=None):
#         mess = self.get_object()
        
#         # Check if user is owner
#         if mess.owner.id != request.user.id:
#             return Response(
#                 {'error': 'Only owner can add managers'}, 
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         serializer = AddManagerSerializer(data=request.data)
#         if serializer.is_valid():
#             user_id = serializer.validated_data['user_id']
#             try:
#                 user = User.objects.get(id=user_id)
#                 if not mess.members.filter(id=user.id).exists():
#                     return Response(
#                         {'error': 'User is not a member of this mess'}, 
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
                
#                 mess.managers.add(user)
#                 mess_serializer = MessSerializer(mess)
#                 return Response({'mess': mess_serializer.data}, status=status.HTTP_200_OK)
            
#             except User.DoesNotExist:
#                 return Response(
#                     {'error': 'User not found'}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
# def add_meal(request, mess_id):
#     mess = get_object_or_404(Mess, id=mess_id)
    
#     # Check if user is manager
#     if not mess.managers.filter(id=request.user.id).exists():
#         return Response(
#             {'error': 'Only managers can add meals'}, 
#             status=status.HTTP_403_FORBIDDEN
#         )
    
#     serializer = MealCreateSerializer(data=request.data)
#     if serializer.is_valid():
#         member_id = serializer.validated_data['member_id']
#         try:
#             member = User.objects.get(id=member_id)
#             if not mess.members.filter(id=member.id).exists():
#                 return Response(
#                     {'error': 'User is not a member of this mess'}, 
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Create or update meal
#             meal, created = Meal.objects.update_or_create(
#                 mess=mess,
#                 member=member,
#                 date=serializer.validated_data['date'],
#                 defaults={
#                     'meal_count': serializer.validated_data['meal_count'],
#                     'added_by': request.user
#                 }
#             )
            
#             return Response({'success': True}, status=status.HTTP_200_OK)
            
#         except User.DoesNotExist:
#             return Response(
#                 {'error': 'Member not found'}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET'])
# @permission_classes([permissions.IsAuthenticated])
# def get_meals(request, mess_id, month):
#     mess = get_object_or_404(Mess, id=mess_id)
    
#     # Check if user is member
#     if not mess.members.filter(id=request.user.id).exists():
#         return Response(
#             {'error': 'Not a member of this mess'}, 
#             status=status.HTTP_403_FORBIDDEN
#         )
    
#     # Get meals for the month
#     meals = Meal.objects.filter(
#         mess=mess,
#         date__startswith=month
#     ).select_related('member', 'added_by')
    
#     serializer = MealSerializer(meals, many=True)
#     return Response({'meals': serializer.data}, status=status.HTTP_200_OK)

# @api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
# def calculate_month(request, mess_id, month):
#     mess = get_object_or_404(Mess, id=mess_id)
    
#     # Check if user is manager
#     if not mess.managers.filter(id=request.user.id).exists():
#         return Response(
#             {'error': 'Only managers can calculate monthly costs'}, 
#             status=status.HTTP_403_FORBIDDEN
#         )
    
#     serializer = MonthlyCalculationCreateSerializer(data=request.data)
#     if serializer.is_valid():
#         bazaar_cost = serializer.validated_data['bazaar_cost']
#         extra_cost = serializer.validated_data['extra_cost']
        
#         # Get all meals for the month
#         meals = Meal.objects.filter(
#             mess=mess,
#             date__startswith=month
#         ).values('member').annotate(
#             total_meals=Sum('meal_count')
#         )
        
#         # Calculate totals
#         total_meals = sum(meal['total_meals'] for meal in meals)
#         total_cost = bazaar_cost + extra_cost
#         cost_per_meal = total_cost / total_meals if total_meals > 0 else 0
        
#         # Create or update calculation
#         calculation, created = MonthlyCalculation.objects.update_or_create(
#             mess=mess,
#             month=month,
#             defaults={
#                 'bazaar_cost': bazaar_cost,
#                 'extra_cost': extra_cost,
#                 'total_cost': total_cost,
#                 'total_meals': total_meals,
#                 'cost_per_meal': cost_per_meal,
#                 'calculated_by': request.user
#             }
#         )
        
#         # Delete existing member summaries
#         MemberMealSummary.objects.filter(calculation=calculation).delete()
        
#         # Create member summaries
#         for meal in meals:
#             member = User.objects.get(id=meal['member'])
#             member_cost = meal['total_meals'] * cost_per_meal
            
#             MemberMealSummary.objects.create(
#                 calculation=calculation,
#                 member=member,
#                 total_meals=meal['total_meals'],
#                 total_cost=member_cost
#             )
        
#         calculation_serializer = MonthlyCalculationSerializer(calculation)
#         return Response({'calculation': calculation_serializer.data}, status=status.HTTP_200_OK)
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET'])
# @permission_classes([permissions.IsAuthenticated])
# def get_calculation(request, mess_id, month):
#     mess = get_object_or_404(Mess, id=mess_id)
    
#     # Check if user is member
#     if not mess.members.filter(id=request.user.id).exists():
#         return Response(
#             {'error': 'Not a member of this mess'}, 
#             status=status.HTTP_403_FORBIDDEN
#         )
    
#     try:
#         calculation = MonthlyCalculation.objects.get(mess=mess, month=month)
#         serializer = MonthlyCalculationSerializer(calculation)
#         return Response({'calculation': serializer.data}, status=status.HTTP_200_OK)
#     except MonthlyCalculation.DoesNotExist:
#         return Response({'calculation': None}, status=status.HTTP_200_OK)
    

# @api_view(['GET', 'POST'])
# @permission_classes([permissions.IsAuthenticated])
# def manage_contributions(request, mess_id, month):
#     mess = get_object_or_404(Mess, id=mess_id)
    
#     # Check if user is member
#     if not mess.members.filter(id=request.user.id).exists():
#         return Response(
#             {'error': 'Not a member of this mess'}, 
#             status=status.HTTP_403_FORBIDDEN
#         )
    
#     if request.method == 'GET':
#         # Get contributions for the month
#         contributions = MemberContribution.objects.filter(
#             mess=mess,
#             month=month
#         ).select_related('member', 'added_by')
        
#         serializer = MemberContributionSerializer(contributions, many=True)
#         return Response({'contributions': serializer.data}, status=status.HTTP_200_OK)
    
#     elif request.method == 'POST':
#         # Only managers can add contributions
#         if not mess.managers.filter(id=request.user.id).exists():
#             return Response(
#                 {'error': 'Only managers can add contributions'}, 
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         serializer = MemberContributionCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             member_id = serializer.validated_data['member_id']
#             try:
#                 member = User.objects.get(id=member_id)
#                 if not mess.members.filter(id=member.id).exists():
#                     return Response(
#                         {'error': 'User is not a member of this mess'}, 
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
                
#                 # Create or update contribution
#                 contribution, created = MemberContribution.objects.update_or_create(
#                     mess=mess,
#                     member=member,
#                     month=month,
#                     defaults={
#                         'amount': serializer.validated_data['amount'],
#                         'description': serializer.validated_data.get('description', ''),
#                         'added_by': request.user
#                     }
#                 )
                
#                 return Response({'success': True}, status=status.HTTP_200_OK)
                
#             except User.DoesNotExist:
#                 return Response(
#                     {'error': 'Member not found'}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)