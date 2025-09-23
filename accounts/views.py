from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from django.contrib.auth.models import Group
from .models import User
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user_serializer = UserSerializer(user)
        return Response({
            'message': 'User created successfully',
            'user': user_serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def signin(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        user_serializer = UserSerializer(user)
        print(user_serializer.data)
        
        response = Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)
        
        # Set refresh token in httpOnly cookie
        response.set_cookie(
            'refresh_token',
            refresh_token,
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        
        return response
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({'error': 'Refresh token not found'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        return Response({'access_token': access_token}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout(request):
    response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    response.delete_cookie('refresh_token')
    return response


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_users(request):
    user = request.user

    # Only Super_Admin can access
    if not user.groups.filter(name="Super_Admin").exists():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # GET → list users
    if request.method == "GET":
        users = User.objects.filter(is_staff=False)
        from .serializers import UserSerializer  # ensure serializer has groups
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST → assign user to groups
    if request.method == "POST":
        user_id = request.data.get('user_id')
        group_names = request.data.get('group_names')  # should be a list

        if not user_id or not group_names:
            return Response(
                {'error': 'user_id and group_names are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_user = get_object_or_404(User, id=user_id)

        # Get or create all groups
        groups = []
        for name in group_names:
            group, _ = Group.objects.get_or_create(name=name)
            groups.append(group)

        # Overwrite groups with the provided list
        target_user.groups.set(groups)
        target_user.save()

        return Response(
            {'message': f'User assigned to groups {", ".join(group_names)}'},
            status=status.HTTP_200_OK
        )