class TamuSubdomainsSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        if response.cookies:
            host = request.get_host()
            # check if it's a different domain
            if "engr.tamu.edu" in host:
                for cookie in response.cookies:
                    response.cookies[cookie]['domain'] = "daphne.engr.tamu.edu"

        return response
