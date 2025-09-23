from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'mess', views.MessViewSet, basename='mess')

urlpatterns = [
    path('', include(router.urls)),
    path('mess/<int:mess_id>/meals/', views.add_meal, name='add_meal'),
    path('mess/<int:mess_id>/meals/<str:month>/', views.get_meals, name='get_meals'),
    path('mess/<int:mess_id>/calculate/<str:month>/', views.calculate_month, name='calculate_month'),
    path('mess/<int:mess_id>/calculation/<str:month>/', views.get_calculation, name='get_calculation'),
    path('mess/<int:mess_id>/contributions/<str:month>/', views.manage_contributions, name='manage_contributions'),
    path("members/request/<int:pk>/approve/", views.approve_member_request, name="approve_member_request"),
    path("members/all-requests/", views.all_member_requests, name="all_member_requests"),
    path("members/become-member/", views.become_member_request, name="become_member_request"),
]