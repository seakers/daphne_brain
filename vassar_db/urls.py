from django.urls import path, include

from . import views

# Group level operations
# We will use the UserInformation model for users

urlpatterns = [


    path('get-table', views.GetTables.as_view(), name='get_table'),

    # New user: creates a new user lol
    path('new-user', views.NewUser.as_view(), name='new_user'),


    # New group: can be called by anybody - caller becomes group admin
    path('new-group', views.NewGroup.as_view(), name='new_group'),

    # Edit group: can only be called by a group admin
    path('edit-group', views.EditGroup.as_view(), name='edit_group'),


    # New problem: could belong to multiple groups - uses 
    path('new-problem', views.NewProblem.as_view(), name='new_problem'),

    # Edit problem: performs a large amount of problem operations
    path('edit-problem', views.EditProblem.as_view(), name='edit_problem'),
    

    # New instrument: could belong to multiple groups
    path('new-instrument', views.NewInstrument.as_view(), name='new_instrument'),

    # Edit instrument: performs a large amount of instrument operations
    path('edit-instrument', views.EditInstrument.as_view(), name='edit_instrument'),
]
