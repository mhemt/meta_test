from django.http import HttpResponseNotFound, HttpResponseServerError
from django.views.generic import DetailView, ListView

from .models import Therapist, Method


class DetailTherapistView(DetailView):
    model = Therapist
    context_object_name = 'therapist'

    def get_context_data(self, **kwargs):
        context = super(DetailTherapistView, self).get_context_data(**kwargs)
        context['methods'] = Method.objects.filter(therapists=self.object)
        return context


class ListTherapistView(ListView):
    model = Therapist
    context_object_name = 'therapists'


def custom_handler404(request, exception):
    return HttpResponseNotFound('Ой, что то сломалось... Простите извините!')


def custom_handler500(request):
    return HttpResponseServerError('Ой, что то сломалось... Простите извините!')
