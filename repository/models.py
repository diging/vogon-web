from django.db import models


class Repository(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    configuration = models.TextField()
    url = models.CharField(max_length=255, default='')

    AMPHORA = 'Amphora'
    REPO_CHOICES = [
        (AMPHORA, 'Amphora')
    ]
    repo_type = models.CharField(
        max_length=100,
        choices=REPO_CHOICES, 
        default=AMPHORA
    )

    def manager(self, user):
        if self.repo_type == self.AMPHORA:
            from repository.managers import AmphoraRepository
            return AmphoraRepository(user=user, endpoint=self.url)
