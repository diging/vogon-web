from restable import RESTManager
from repository import auth


class RepositoryManager(RESTManager):
    def __init__(self, configuration, **kwargs):
        self.user = kwargs.pop('user')
        if self.user:
            kwargs.update({'headers': auth.jars_github_auth(self.user)})
        super(RepositoryManager, self).__init__(configuration, **kwargs)

    def get_raw(self, target, **params):
        import requests
        headers = {}
        if self.user:
            headers = auth.jars_github_auth(self.user)
        print headers
        return requests.get(target, headers=headers, params=params).content
