from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    def get(self, request):
        response = Response({"status": "ok"})
        response._has_been_logged = True
        return response
