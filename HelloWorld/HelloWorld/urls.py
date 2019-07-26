"""HelloWorld URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from django.conf.urls import url

#from learn import views as learn_views
#from calc import views as calc_views

from tshare import views as tshare_views
from tshare import rest as rest_service

urlpatterns = [
    path('admin/', admin.site.urls),
    
#    url(r'^$', learn_views.home, name = 'home'),
#    path('add/', calc_views.add, name = 'add'),
#    path('new_add/<int:a>/<int:b>/', calc_views.add2, name = 'add2' ),

    url(r'^$', tshare_views.homepage, name = 'home'),
    url('trade_report/', tshare_views.trade_report,name = 'trade_report'),
    path('trade_detail/<str:r_code>/', tshare_views.trade_detail, name='trade_detail'),
    path('all_note/', tshare_views.all_note, name='all_note'),
    path('note_editor/', tshare_views.note_editor, name='note_editor'),
    path('trade_statistics/', tshare_views.trade_statistics, name='trade_statistics'),
    path('share_analysis/<str:r_code>/', tshare_views.share_analysis, name='share_analysis'),
    
#data operation
    path('add_note/', tshare_views.add_note, name='add_note'),
    path('delete_note/', tshare_views.delete_note, name='delete_note'),

#json data
    path('note_json/', rest_service.note_json, name='note_json'),
    path('k_data_json/<str:r_code>/', rest_service.k_data_json, name='k_data_json'),
    path('trade_data_json/', rest_service.trade_data_json, name='trade_data_json'),
    path('ori_trade_data_json/', rest_service.ori_trade_data_json, name='ori_trade_data_json'),
    path('trade_data_json/<str:r_code>/', rest_service.trade_data_json, name='trade_data_json'),
    path('trend_data_json/<str:r_code>/', rest_service.trend_data_json, name='trend_data_json')
]
