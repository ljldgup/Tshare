from django.shortcuts import render

def hello(request):
    context = {}
    context['hello'] = 'Hello World!'
    return render(request, 'test/hello.html', context)
