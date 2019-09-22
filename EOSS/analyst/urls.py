from django.urls import path

from . import views

urlpatterns = [
    # Run data mining
    path('get-driving-features', views.GetDrivingFeatures.as_view()),
    path('get-driving-features-epsilon-moea', views.GetDrivingFeaturesEpsilonMOEA.as_view()),
    path('get-driving-features-with-generalization', views.GetDrivingFeaturesWithGeneralization.as_view()),
    path('get-marginal-driving-features', views.GetMarginalDrivingFeatures.as_view()),

    # Generalization / simplification
    path('generalize-feature', views.GeneralizeFeature.as_view()),
    path('simplify-feature-expression', views.SimplifyFeatureExpression.as_view()),

    # Stop search
    path('stop-search', views.StopSearch.as_view()),

    # Clustering
    path('cluster-data', views.ClusterData.as_view()),
    path('get-cluster', views.GetCluster.as_view()),

    # Logical expression
    path('compute-complexity', views.ComputeComplexity.as_view()),
    path('compute-typicality', views.ComputeTypicality.as_view()),
    path('compute-complexity-of-features', views.ComputeComplexityOfFeatures.as_view()),
    path('convert-to-CNF', views.ConvertToCNF.as_view()),
    path('convert-to-DNF', views.ConvertToDNF.as_view()),

    # Get or set problem entities/parameters
    path('get-problem-parameters', views.GetProblemParameters.as_view()),
    path('set-problem-parameters', views.SetProblemParameters.as_view()),
    path('get-problem-concept-hierarchy', views.GetProblemConceptHierarchy.as_view()),
    path('set-problem-generalized-concepts', views.SetProblemGeneralizedConcepts.as_view()),

    # Import/export feature data
    path('import-feature-data', views.ImportFeatureData.as_view()),
    path('import-target-selection', views.ImportTargetSelection.as_view()),
    path('export-target-selection', views.ExportTargetSelection.as_view()),
]
