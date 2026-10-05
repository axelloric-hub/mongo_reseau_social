"""middleware.py - Ajoute les en-tetes CORS pour que le navigateur accepte les appels inter-ports."""
from django.http import HttpResponse


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        reponse = HttpResponse(status=204) if request.method == "OPTIONS" else self.get_response(request)
        reponse["Access-Control-Allow-Origin"] = "*"
        reponse["Access-Control-Allow-Headers"] = "Content-Type"
        reponse["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return reponse
