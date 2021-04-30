from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from notifications.signals import notify

from annotations.models import TextCollection, VogonUser


@receiver(m2m_changed, sender=TextCollection.participants.through)
def my_handler(sender, action, pk_set, instance, **kwargs):
    if action == 'post_add':
        user = VogonUser.objects.get(pk=list(pk_set)[0])
        notify.send(
            sender=instance.ownedBy, 
            action_object=instance,
            recipient=user, 
            verb=f'You have been added as collaborator to project "{instance.name}"'
        )

    if action == 'post_remove':
        user = VogonUser.objects.get(pk=list(pk_set)[0])
        notify.send(
            sender=instance.ownedBy, 
            action_object=instance,
            recipient=user, 
            verb=f'You have been removed as collaborator from the project "{instance.name}"'
        )
