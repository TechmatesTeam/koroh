from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    # Chat session management
    path('sessions/', views.ChatSessionListView.as_view(), name='session-list'),
    path('sessions/<uuid:session_id>/', views.ChatSessionDetailView.as_view(), name='session-detail'),
    
    # Message sending
    path('send/', views.SendMessageView.as_view(), name='send-message'),
    path('quick/', views.quick_chat, name='quick-chat'),
    path('anonymous/', views.anonymous_chat, name='anonymous-chat'),
    
    # Platform integration endpoints
    path('analyze-cv/', views.analyze_cv_chat, name='analyze-cv-chat'),
    path('generate-portfolio/', views.generate_portfolio_chat, name='generate-portfolio-chat'),
    path('job-recommendations/', views.job_recommendations_chat, name='job-recommendations-chat'),
]