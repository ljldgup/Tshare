from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
 
 
def index(request):
    return HttpResponse(u"learn")

 
def home(request):
	temp={}
	temp['list_name']='the test list'
	temp['tlist']=['fuckA','fuckB','fuckC']
	temp['tdict']={}
	temp['tdict']['A']='Alla'
	temp['tdict']['B']='Cindy'
	temp['tdict']['C']='Mei'
	temp['tdict']['number']=142
	return render(request, 'template/home.html',temp)