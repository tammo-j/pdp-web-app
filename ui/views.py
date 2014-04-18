from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from orders.models import Setting

def search(request):
    ticket_url = reverse('ui.views.ticket')
    return render(request, 'ui/search.html', {'ticket_url':ticket_url})

def search_printed(request):
    ticket_url = request.build_absolute_uri(reverse('ui.views.ticket'))
    print_url = ''
    setting = Setting.objects.filter(name='printer').first()
    if setting != None:
        print_url = setting.value 
    return render(request, 'ui/search.html', {'print_url':print_url,'ticket_url':ticket_url})

def ticket(request):
    return render(request, 'ui/ticket.html')

@login_required
def queue(request):
    return render(request, 'ui/queue.html')
