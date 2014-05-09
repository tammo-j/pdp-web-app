from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from orders.models import Setting

def search(request):
    return render(request, 'ui/search.html')

def search_printed(request):
    print_url = ''
    setting = Setting.objects.filter(name='printer').first()
    if setting != None:
        print_url = setting.value 
    return render(request, 'ui/search.html', {'print_url':print_url})

@login_required
def queue(request):
    print_url = ''
    setting = Setting.objects.filter(name='printer_admin').first()
    if setting != None:
        print_url = setting.value 
    return render(request, 'ui/queue.html', {'print_url':print_url, 'footer':True})

def queue_tablet(request):
    print_url = ''
    setting = Setting.objects.filter(name='printer_admin').first()
    if setting != None:
        print_url = setting.value 
    return render(request, 'ui/queue.html', {'print_url':print_url, 'footer':False})
