from grapi.backend.mock import Resource

from .data import MESSAGES, USERS


class UserResource(Resource):
    def __init__(self, options):
        Resource.__init__(self, options)

    def on_get(self, req, resp, userid=None, folderid=None, itemid=None, method=None):
        if method == 'messages':

            data = {
                '@odata.context': '/api/gc/v1/me/messages',
                '@odata.nextLink': '/api/gc/v1/me/messages?$skip=10',
                'value': MESSAGES,
            }
        else:
            data = {
                '@odata.context': '/api/gc/v1/users',
                'value': USERS,
            }

        self.respond_json(resp, data)
