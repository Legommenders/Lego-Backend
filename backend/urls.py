"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from evaluation.views import EvaluationView, ExperimentView, ExperimentRegisterView, LogView, LogSummarizeView, \
    ExportView

urlpatterns = [
    # Evaluation URLs
    path('evaluations/', EvaluationView.as_view(), name='evaluation-list'),
    path('evaluations/export', ExportView.as_view(), name='evaluation-export'),
    path('evaluations/<str:signature>', EvaluationView.as_view(), name='evaluation-detail'),

    path('experiments/log', LogView.as_view(), name='experiment-log'),
    path('experiments/<str:session>', ExperimentView.as_view(), name='experiment-info'),
    path('experiments/', ExperimentView.as_view(), name='experiment-list'),
    path('experiments/<str:session>/register', ExperimentRegisterView.as_view(), name='experiment-register'),
    path('log-summarize', LogSummarizeView.as_view(), name='log-analyse'),

    # # Tag URLs
    # path('tags/', TagView.as_view(), name='tag-list'),
    # path('tags/<str:name>/', TagView.as_view(), name='tag-detail'),
    #
    # # Connection URLs
    # path('connections/', ConnectionView.as_view(), name='connection-list'),
]
