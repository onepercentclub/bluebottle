class ExcludeWebSocketMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for WebSocket routes
        if request.path.startswith('/ws/'):
            return None

        # Otherwise, continue as normal
        return self.get_response(request)
