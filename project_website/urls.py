
from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/home/', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('space-content/', views.get_space_content, name='get_space_content'),
    path('download/space/<int:space_id>/', views.download_space_file, name='download_space_file'),
    path('download/xml/<int:space_id>/', views.download_space_xml_file, name='download_space_xml'),
]
