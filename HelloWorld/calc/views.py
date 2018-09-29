from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
 
def add(request):
    a = request.GET['a']
    b = request.GET['b']
    c = int(a)+int(b)
    return HttpResponse(str(c))
	
def add2(request, a, b):
    c = int(a) + int(b)
    return HttpResponse(str(c))
	

def latest_books(request):
	book_list = Book.objects.order_by('‐pub_date')[:10]
	return render_to_response('latest_books.html', {'book_list': book_list})