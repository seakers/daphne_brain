from django.urls import path

from . import views

urlpatterns = [
    path('get-driving-features', views.GetDrivingFeatures.as_view()),
    path('get-driving-features-epsilon-moea', views.getDrivingFeaturesEpsilonMOEA.as_view()),
    path('get-driving-features-with-generalization', views.getDrivingFeaturesWithGeneralization.as_view()),
    path('run-generalization-local-search', views.GeneralizationLocalSearch.as_view()),

    path('get-driving-features-automated', views.GetDrivingFeaturesAutomated.as_view()),
    path('get-marginal-driving-features', views.GetMarginalDrivingFeatures.as_view()),
    path('cluster-data', views.ClusterData.as_view()),
    path('get-cluster', views.GetCluster.as_view()),

    path('compute-complexity', views.ComputeComplexity.as_view()),
    path('compute-typicality', views.ComputeTypicality.as_view()),

    path('compute-complexity-of-features', views.ComputeComplexityOfFeatures.as_view()),
    path('convert-to-CNF', views.ConvertToCNF.as_view()),
    path('convert-to-DNF', views.ConvertToDNF.as_view()),

    path('get-problem-parameters', views.GetProblemParameters.as_view()),
    path('set-problem-parameters', views.SetProblemParameters.as_view()),
    path('get-taxonomic-scheme', views.getTaxonomicScheme.as_view()),



    path('import-feature-data', views.ImportFeatureData.as_view()),
    path('import-target-selection', views.ImportTargetSelection.as_view()),
    path('export-target-selection', views.ExportTargetSelection.as_view()),
]
