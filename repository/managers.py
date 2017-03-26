from restable import RESTManager
from repository import auth


class RepositoryManager(RESTManager):
    def __init__(self, configuration, **kwargs):
        self.user = kwargs.pop('user')
        kwargs.update({'headers': auth.jars_github_auth(self.user)})
        super(RepositoryManager, self).__init__(configuration, **kwargs)