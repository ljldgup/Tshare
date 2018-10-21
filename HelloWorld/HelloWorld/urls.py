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
from learn import views as learn_views
from calc import views as calc_views
from tshare import views as tshare_views
from . import view

urlpatterns = [
    path('admin/', admin.site.urls),
	url(r'^$', learn_views.home, name = 'home'),
	path('add/', calc_views.add, name = 'add'),
	path('new_add/<int:a>/<int:b>/', calc_views.add2, name = 'add2' ),
	url('trade_report/', tshare_views.trade_report,name = 'trade_report'),
	path('trade_detail/<str:r_code>/', tshare_views.trade_detail, name='trade_detail'),
	path('k_data_json/<str:r_code>/', tshare_views.k_data_json, name='k_data_json'),
	path('trade_data_json/', tshare_views.trade_data_json, name='trade_data_json')
]
