from django.urls import path

from dialogue import views

urlpatterns = [
    path('import-data-matfile', views.ImportDataEDLSTATS.as_view(), name='daphne_import_data-matfile'),
]
