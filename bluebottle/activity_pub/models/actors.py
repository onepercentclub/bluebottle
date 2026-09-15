from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from django.db import models, connection
from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models.base import ActivityPubModel, Image
from bluebottle.activities.models import RemoteMember
from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization as BluebottleOrganization


class Inbox(ActivityPubModel):
    pass


class Outbox(ActivityPubModel):
    pass


class PrivateKey(models.Model):
    private_key_pem = models.TextField()


class PublicKey(ActivityPubModel):
    public_key_pem = models.TextField()
    private_key = models.ForeignKey(PrivateKey, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.iri and not self.private_key:

            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            self.private_key = PrivateKey.objects.create(
                private_key_pem=private_key_pem

            )
            self.public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

        super().save(*args, **kwargs)


class Actor(ActivityPubModel):
    inbox = models.ForeignKey('activity_pub.Inbox', on_delete=models.SET_NULL, null=True, blank=True)
    outbox = models.ForeignKey('activity_pub.Outbox', on_delete=models.SET_NULL, null=True, blank=True)
    public_key = models.ForeignKey('activity_pub.PublicKey', on_delete=models.SET_NULL, null=True, blank=True)
    preferred_username = models.CharField(blank=True, null=True)

    @property
    def follow(self):
        from bluebottle.activity_pub.models.activities import Follow
        return Follow.objects.filter(object=self).first()

    @property
    def webfinger_uri(self):
        if self.preferred_username:
            return f'acct:{self.preferred_username}@{connection.tenant.domain_url}'

    def save(self, *args, **kwargs):
        if self.is_local:
            if not self.inbox:
                self.inbox = Inbox.objects.create()
            if not self.outbox:
                self.outbox = Outbox.objects.create()
            if not self.public_key:
                self.public_key = PublicKey.objects.create()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_real_instance().name


class Person(Actor):
    name = models.TextField()
    given_name = models.TextField(null=True, blank=True)
    family_name = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)

    origin = models.OneToOneField(
        Member,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_model'
    )

    adopted = models.OneToOneField(
        RemoteMember,
        null=True,
        on_delete=models.CASCADE,
        related_name='origin'
    )

    source = models.ForeignKey(
        'activity_pub.Organization', null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name


class Organization(Actor):
    name = models.CharField(max_length=300)
    summary = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    image = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)
    icon = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)

    origin = models.OneToOneField(
        BluebottleOrganization,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_model'
    )

    adopted = models.OneToOneField(
        BluebottleOrganization,
        null=True,
        on_delete=models.CASCADE,
        related_name='origin'
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_local and not self.adopted:
            adapter.adopt(self)

    class Meta:
        verbose_name = _("partner")
        verbose_name_plural = _("partners")

    def __str__(self):
        return self.name


class Team(Actor):
    """
    Federated team for team-schedule activities. Maps to time_based.Team.
    """
    captain = models.ForeignKey(
        Person,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='captained_teams',
    )

    origin = models.OneToOneField(
        'time_based.Team',
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_model',
    )
    adopted = models.OneToOneField(
        'time_based.Team',
        null=True,
        on_delete=models.CASCADE,
        related_name='origin',
    )

    def __str__(self):
        return self.name or f'Team {self.pk}'

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')
