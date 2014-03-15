from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def search(request):
    return render(request, 'ui/search.html')

def ticket(request):
    return render(request, 'ui/ticket.html')

@login_required
def queue(request):
    return render(request, 'ui/queue.html')
