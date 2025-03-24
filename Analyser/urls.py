from django.contrib import admin
from django.urls import path
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('form/', views.form_view),
    path('analysis/', views.result_view),
    path('', views.home_view),
    path('features/', views.feature_view),
    path('about/', views.about_view),
    path('contact/', views.about_view),
]
