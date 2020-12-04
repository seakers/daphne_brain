from django.urls import path

from . import views

urlpatterns = [
    path('procedure', views.PdfViewer.as_view()),
    path('figure', views.PngViewer.as_view())
]