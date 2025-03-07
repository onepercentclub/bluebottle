from django.conf import settings
from django.db import models


class Platform(models.Model):
    name = models.CharField(max_length=100)
    domain = models.URLField(unique=True)
    inbox_url = models.URLField()
    outbox_url = models.URLField()
    public_key = models.TextField()
    private_key = models.TextField()
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_platforms",
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.domain})"

    @property
    def actor_url(self):
        return f"{self.domain}/actor"

    def generate_keys(self):
        """Generate public/private key pair for ActivityPub"""
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        public_key = private_key.public_key()

        self.private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        self.public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        self.save()


class PublishableModel(models.Model):
    """Abstract model for ActivityPub publishable content"""

    platforms = models.ManyToManyField(
        "Platform", related_name="%(class)ss", blank=True
    )

    class Meta:
        abstract = True

    def publish_to_platforms(self):
        """Publish content to all active platforms"""
        from .tasks import publish_to_platform

        for platform in self.platforms.filter(is_active=True):
            publish_to_platform.delay(
                self._meta.app_label, self._meta.model_name, self.id, platform.id
            )


class Actor(models.Model):
    """
    ActivityPub Actor model representing a local user
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="actor"
    )
    username = models.CharField(max_length=100, unique=True)
    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="actors"
    )
    followers = models.ManyToManyField(
        "RemoteActor", related_name="following", blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"@{self.username}@{self.platform.domain}"

    @property
    def actor_uri(self):
        return f"{self.platform.domain}/users/{self.username}"

    def send_to_inbox(self, activity):
        """Send an activity to this actor's inbox"""
        # TODO: Implement ActivityPub inbox delivery
        pass


class RemoteActor(models.Model):
    """
    ActivityPub Actor from a remote instance
    """

    actor_uri = models.URLField(unique=True)
    inbox_url = models.URLField()
    username = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"@{self.username}@{self.domain}"

    def send_to_inbox(self, activity):
        """Send an activity to this actor's inbox"""
        # TODO: Implement ActivityPub inbox delivery
        pass


class ActivityPubRegistration(models.Model):
    REGISTRATION_STATUS_CHOICES = [
        ("https://schema.org/CompletedActionStatus", "Completed"),
        ("https://schema.org/PendingActionStatus", "Pending"),
        ("https://schema.org/CancelledActionStatus", "Cancelled"),
    ]

    deed = models.ForeignKey(
        "deeds.Deed", on_delete=models.CASCADE, related_name="activitypub_registrations"
    )
    actor = models.URLField()  # The ActivityPub actor URL of the participant
    inbox = models.URLField()  # The inbox URL of the participant
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=100,
        choices=REGISTRATION_STATUS_CHOICES,
        default="https://schema.org/PendingActionStatus",
    )
    participant_name = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("deed", "actor")


class RemoteDeed(models.Model):
    DEED_STATUS_CHOICES = [
        ("https://schema.org/EventScheduled", "Scheduled"),
        ("https://schema.org/EventCancelled", "Cancelled"),
        ("https://schema.org/EventPostponed", "Postponed"),
    ]

    remote_id = models.URLField(unique=True)
    platform = models.ForeignKey("Platform", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=100,
        choices=DEED_STATUS_CHOICES,
        default="https://schema.org/EventScheduled",
    )
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    organizer_name = models.CharField(max_length=255)
    organizer_url = models.URLField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
