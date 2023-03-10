from django.urls import path

from info.views import index, logout, graph, download

app_name = 'info'
urlpatterns = [
    path('index/', index, name='index'),
    path('logout/', logout, name='logout'),
    path('graph/', graph, name='graph'),
    path('download/', download, name='download'),
]
