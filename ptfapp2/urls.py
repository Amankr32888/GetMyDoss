from django.urls import path ,include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'ptfapp2'   #  namespace— use {% url 'ptfapp2:dashboard' %} in templates

urlpatterns = [

    # path('', include('django.contrib.auth.urls')),
    # ─── Auth   ─────────────────────
    
    # path('login/',auth_views.LoginView.as_view(template_name='registration/login.html'),name='login'),
    
    
    path('login/', views.custom_login_view, name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('password-change/', views.password_change_view, name='password_change'),

    # ─── Dashboard and themes 
    path('', views.dashboard_view, name='dashboard'),
    path('save-theme/', views.save_theme_view, name='save_theme'),
    
    # ─── User Sign Up   ──────────────────
    path('set-password/', views.SetPasswordView.as_view(), name='set_password'),
    
    # ─── Profile   ──────────────────
    path('accounts/profile_page/', views.profile_page, name='profile_page'),
    path('profile_form/', views.profile_form_view, name='profile_form'),  

    # ─── Skills   ───────────────────
    path('skills/',                    views.skills_list_view, name='skills_list'),
    path('skills/add/',                views.skill_form_view,  name='skill_add'),
    path('skills/<int:pk>/edit/',      views.skill_form_view,  name='skill_edit'),
    path('skills/<int:pk>/delete/',    views.skill_delete_view, name='skill_delete'),

    # ─── Projects   ─────────────────
    path('projects/',                  views.projects_list_view,  name='projects_list'),
    path('projects/add/',              views.project_form_view,   name='project_add'),
    path('projects/<int:pk>/edit/',    views.project_form_view,   name='project_edit'),
    path('projects/<int:pk>/delete/',  views.project_delete_view, name='project_delete'),

    # ─── Social Links   ─────────────
    path('social-links/',                  views.social_links_list_view,  name='social_links_list'),
    path('social-links/add/',              views.social_link_form_view,   name='social_link_add'),
    path('social-links/<int:pk>/edit/',    views.social_link_form_view,   name='social_link_edit'),
    path('social-links/<int:pk>/delete/',  views.social_link_delete_view, name='social_link_delete'),

    # ─── Short Links   ──────────────
    path('short-links/',                  views.short_links_list_view,  name='short_links_list'),
    path('short-links/add/',              views.short_link_form_view,   name='short_link_add'),
    path('short-links/<int:pk>/edit/',    views.short_link_form_view,   name='short_link_edit'),
    path('short-links/<int:pk>/delete/',  views.short_link_delete_view, name='short_link_delete'),

    # ─── Documents   ────────────────
    path('documents/',                  views.documents_list_view,  name='documents_list'),
    path('documents/add/',              views.document_form_view,   name='document_add'),
    path('documents/<int:pk>/edit/',    views.document_form_view,   name='document_edit'),
    path('documents/<int:pk>/delete/',  views.document_delete_view, name='document_delete'),

    # ─── Contact Messages   ─────────
    path('messages/', views.messages_list_view, name='messages_list'),

    # ─── Co-Users (Superuser only)   
    path('co-users/',                  views.couser_list_view,  name='couser_list'),
    path('co-users/add/',              views.couser_form_view,  name='couser_add'),
    path('co-users/<int:pk>/edit/',    views.couser_form_view,  name='couser_edit'),
    path('co-users/<int:pk>/delete/',  views.couser_delete_view, name='couser_delete'),
]