class RequestCounterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0

    def __call__(self, request):
        self.request_count += 1
        return self.get_response(request)

    def get_request_count(self):
        return self.request_count
