from django.urls import path

from . import views

urlpatterns = [
    path('command', views.Command.as_view(), name='command'),
    path('commands', views.CommandList.as_view(), name='command_list'),
    path('import-data', views.ImportData.as_view(), name='daphne_import_data'),
    path('save-data', views.SaveData.as_view(), name='daphne_save_data'),
    path('download-data', views.DownloadData.as_view(), name='daphne_download_data'),
    path('dataset-list', views.DatasetList.as_view(), name='dataset_list'),
    path('clear-session', views.ClearSession.as_view(), name='clear_session'),
    path('import-data-matfile', views.ImportDataEDLSTATS.as_view(), name='daphne_import_data-matfile'),
    path('set-problem', views.SetProblem.as_view(), name='set_problem'),
    path('active-feedback-settings', views.ActiveFeedbackSettings.as_view(), name='set_active_feedback_settings')
]
