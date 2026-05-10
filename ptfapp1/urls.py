from django.urls import path
from django.views.generic import RedirectView
from .views import (
    Home_View,
    SkillsListView,
    ProjectsListView,
    ShortLinkRedirectView,
    DocumentDownloadView,
    capture_email_view,
)

app_name = 'ptfapp1'   #  namespace in templates-- {% url 'ptfapp1:home' %} 

urlpatterns = [
    # path('',HomeView.as_view(),name='home_base'),
    # Option: redirect root to admin or a default user
    path('', RedirectView.as_view(url='/dashboard/'), name='home_base'),
    path('u/<str:username>/',Home_View.as_view(),name='home'),
    # path('u/<str:username>/',HomeView.as_view(),name='home'),
    path('u/<str:username>/skills/',SkillsListView.as_view(),name='skills_list'),
    path('u/<str:username>/projects/',ProjectsListView.as_view(),name='projects_list'),
    path('u/<str:username>/<slug:slug>/',ShortLinkRedirectView.as_view(), name='short_link'),
    path('documents/<int:doc_id>/download/',DocumentDownloadView.as_view(),name='document_download'),

    # Email capture API
    path('api/capture-email/',capture_email_view,name='capture_email'),
]