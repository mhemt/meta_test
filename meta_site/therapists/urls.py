from django.urls import path
from .views import ListTherapistView, DetailTherapistView


urlpatterns = [
    path('', ListTherapistView.as_view(), name='therapists'),
    path('<int:pk>/', DetailTherapistView.as_view(), name='therapist'),
]
