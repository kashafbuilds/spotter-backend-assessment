from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, FuelStationViewSet


router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='product')
router.register(r'fuel-stations', FuelStationViewSet, basename='fuel-station')


urlpatterns = [
    path('', include(router.urls)),
]