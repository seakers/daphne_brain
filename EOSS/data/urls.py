from django.urls import path, include

from . import views

urlpatterns = [
    path('import-data', views.ImportData.as_view(), name='daphne_import_data'),
    path('save-data', views.SaveData.as_view(), name='daphne_save_data'),
    path('download-data', views.DownloadData.as_view(), name='daphne_download_data'),
    path('dataset-list', views.DatasetList.as_view(), name='dataset_list'),
    path('set-problem', views.SetProblem.as_view(), name='set_problem'),
]
