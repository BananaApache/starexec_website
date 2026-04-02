from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Redirect root to home
    path("", RedirectView.as_view(url="/home/", permanent=False)),
    # Auth Routes
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Core Dashboard
    path("home/", views.home, name="home"),
    path("space-content/", views.get_space_content, name="get_space_content"),
    # NEW: Proxy endpoint for modals
    path("proxy/", views.proxy_starexec_page, name="proxy_starexec_page"),
    # Download Endpoints
    path(
        "download/space/<int:space_id>/",
        views.download_space_file,
        name="download_space_file",
    ),
    path(
        "download/xml/<int:space_id>/",
        views.download_space_xml_file,
        name="download_space_xml",
    ),
    # Job routes
    path("jobs/create/", views.create_job, name="create_job"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/json/", views.get_job_json, name="job_json"),
    path("queues/", views.get_queues, name="get_queues"),
]
