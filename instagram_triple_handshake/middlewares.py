import time


class RequestsPauseSpiderMiddleware:

    delay = 7

    def process_response(self, request, response, spider):
        if response.url == 'https://www.instagram.com/':
            time.sleep(self.delay)
        return response

