class TamuSubdomainsSessionMiddleware(object):
    def process_response(self, request, response):
        if response.cookies:
            host = request.get_host()
            # check if it's a different domain
            if "engr.tamu.edu" in host:
                for cookie in response.cookies:
                    if 'domain' in response.cookies[cookie]:
                        response.cookies[cookie]['domain'] = "engr.tamu.edu"
        return response
