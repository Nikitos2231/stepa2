from django.shortcuts import redirect
from django.urls import reverse


class RedirectIfAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if hasattr(request, 'user') and request.user.is_authenticated and request.path in [reverse('login'),
                                                                                           reverse('signup')]:
            return redirect('/')
        return response
