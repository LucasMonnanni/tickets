from django.shortcuts import render
from django.template.loader import TemplateDoesNotExist 
from logger.models import ErrorLog
import pprint, sys, traceback

def error404(request, exception):
    if exception.__str__().startswith("{'tried'"):
        exception = 'La ruta indicada no existe.'
    return render(request, 'tkts/404.html', {'exception': exception}, status=404)

def error500(request):
    data = request.__dict__.copy()
    del data['META'], data['environ']
    pp = pprint.PrettyPrinter(indent=4)
    str = 'Request data: \n'
    str += pp.pformat(data)
    type, value, tb = sys.exc_info()
    str += 'Exception Value: \n' + pp.pformat(value) + '\n'
    str += 'Value: \n' + pp.pformat(type) + '\n'
    for line in traceback.format_exception(type, value, tb):
        str += line + '\n'
    error = ErrorLog.objects.create(code = 500, data = str)
    error.save()
    return render(request, 'tkts/500.html', status=500)
