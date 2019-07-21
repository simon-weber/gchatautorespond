class CacheDefaultOffMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Cache-Control', 'max-age=0, no-cache, no-store, must-revalidate, private')
        return response
