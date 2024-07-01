import datetime
import os
import random
import string
import uuid
from builtins import object
from builtins import range
from builtins import str

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, UserManager
)
from django.core.mail.message import EmailMessage
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import lazy, cached_property
from django.utils.translation import gettext_lazy as _
from djchoices.choices import DjangoChoices, ChoiceItem
from future.utils import python_2_unicode_compatible
from rest_framework_jwt.settings import api_settings

from bluebottle.bb_accounts.utils import valid_email
from bluebottle.initiatives.models import Theme
from bluebottle.members.tokens import login_token_generator
from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import get_language_choices, get_default_language
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from .utils import send_welcome_mail
from ..segments.models import Segment


def generate_picture_filename(instance, filename):
    """
    Creates a random directory and file name for uploaded pictures.

    The random directory allows the uploaded images to be evenly spread over
    1296 directories. This allows us to host more files before hitting bad
    performance of the OS filesystem and/or utility programs which can occur
    when a directory has thousands of files.

    An example return value is of this method is:
        'profiles/tw/tws9ea4eqaj37xnu24svp2vwndsytzysa.jpg'
    """
    # Create the upload directory string.
    char_set = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choice(char_set) for i in range(33))
    upload_directory = os.path.join('profiles', random_string[0:2])

    # Get the file extension from the original filename.
    original_filename = os.path.basename(filename)
    file_extension = os.path.splitext(original_filename)[1]

    # Create the normalized path.
    normalized_filename = random_string + file_extension
    return os.path.normpath(os.path.join(upload_directory, normalized_filename))


class BlueBottleUserManager(UserManager):
    def create_user(self, username=None, email=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        extra_fields['last_login'] = now
        extra_fields['date_joined'] = now
        extra_fields['is_active'] = True
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        now = timezone.now()
        extra_fields['last_login'] = now
        extra_fields['date_joined'] = now
        extra_fields['is_active'] = True
        if not username:
            username = email
        return super().create_superuser(username, email, password, **extra_fields)

    def get_by_natural_key(self, username):
        if isinstance(username, int):
            return self.get(pk=username)
        else:
            return self.get(**{
                '{}__iexact'.format(self.model.USERNAME_FIELD): username
            })


@python_2_unicode_compatible
class BlueBottleBaseUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for BlueBottle.

    When extending the user model, the serializer should extend too.
    We provide a default base serializer in sync with the base user model
    The Django Meta attribute seems the best place for this configuration, so we
    have to add this.
    """
    class Gender(DjangoChoices):
        male = ChoiceItem('male', label=_('Male'))
        female = ChoiceItem('female', label=_('Female'))

    class UserType(DjangoChoices):
        person = ChoiceItem('person', label=_('Person'))
        company = ChoiceItem('company', label=_('Company'))
        foundation = ChoiceItem('foundation', label=_('Foundation'))
        school = ChoiceItem('school', label=_('School'))
        group = ChoiceItem('group', label=_('Club / association'))

    email = models.EmailField(_('email address'), db_index=True, max_length=254, unique=True)
    username = models.CharField(_('username'), max_length=254, unique=True)

    is_staff = models.BooleanField(_('staff status'),
                                   default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'),
                                    default=False,
                                    help_text=_('Designates whether this user should be treated as active. Unselect '
                                                'this instead of deleting accounts.'))

    disable_token = models.CharField(blank=True, max_length=32, null=True)

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    updated = models.DateTimeField(_('updated'), auto_now=True)

    last_seen = models.DateTimeField(_('Last Seen'), blank=True, null=True)
    deleted = models.DateTimeField(_('deleted'), blank=True, null=True)

    user_type = models.CharField(_('Member Type'), choices=UserType.choices, default=UserType.person, max_length=25)

    first_name = models.CharField(_('first name'), blank=True, max_length=100)
    last_name = models.CharField(_('last name'), blank=True, max_length=100)
    location = models.ForeignKey(
        'geo.Location', blank=True,
        verbose_name=_('Office'),
        null=True, on_delete=models.SET_NULL)

    location_verified = models.BooleanField(
        default=False,
        help_text=_('Office location is verified by the user')
    )

    favourite_themes = models.ManyToManyField(Theme, blank=True)
    skills = models.ManyToManyField('time_based.Skill', blank=True)

    search_distance = models.CharField(_('Distance'), max_length=10, default='50km', blank=True, null=True)
    any_search_distance = models.BooleanField(_('Any distance'), default=True)
    exclude_online = models.BooleanField(_('Don’t show online/remote activities'), default=False)

    phone_number = models.CharField(_('phone number'), blank=True, max_length=50)
    gender = models.CharField(_('gender'), blank=True, choices=Gender.choices, max_length=6)
    birthdate = models.DateField(_('birthdate'), blank=True, null=True)
    about_me = models.TextField(_('about me'), blank=True)
    # TODO Use generate_picture_filename (or something) for upload_to
    picture = ImageField(
        _('picture'), blank=True, upload_to='profiles',

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    is_co_financer = models.BooleanField(
        _('Co-financer'),
        default=False,
        help_text=_('Donations by co-financers are shown in a separate list on the '
                    'project page. These donation will always be visible.'))
    can_pledge = models.BooleanField(
        _('Can pledge'),
        default=False,
        help_text=_('User can create a pledge donation.'))

    # Use lazy for the choices and default, so that tenant properties
    # will be correctly loaded
    primary_language = models.CharField(_('primary language'),
                                        choices=lazy(get_language_choices, tuple)(),
                                        default=lazy(get_default_language, str)(),
                                        help_text=_('Language used for website and emails.'),
                                        max_length=7)
    share_time_knowledge = models.BooleanField(_('share time and knowledge'), default=False)
    share_money = models.BooleanField(_('share money'), default=False)
    newsletter = models.BooleanField(_('newsletter'), default=True, help_text=_('Subscribe to newsletter.'))
    campaign_notifications = models.BooleanField(
        _('Updates'),
        help_text=_('Updates from initiatives and activities that this person follows'),
        default=True
    )
    submitted_initiative_notifications = models.BooleanField(
        _('Submitted initiatives'),
        help_text=_('Staff member receives a notification when an initiative is submitted an ready to be reviewed.'),
        default=False
    )

    website = models.URLField(_('website'), blank=True)
    facebook = models.CharField(_('facebook profile'), blank=True, max_length=50)
    twitter = models.CharField(_('twitter profile'), blank=True, max_length=15)
    skypename = models.CharField(_('skype profile'), blank=True, max_length=32)

    partner_organization = models.ForeignKey(
        'organizations.Organization',
        blank=True, null=True,
        help_text=_('Users that are connected to a partner organisation '
                    'will skip the organisation step in initiative create.'),
        related_name='partner_organization_members',
        verbose_name=_('Partner organisation'),
        on_delete=models.CASCADE
    )

    is_anonymized = models.BooleanField(_('Is anonymized'), default=False)
    welcome_email_is_sent = models.BooleanField(_('Welcome email is sent'), default=False)

    USERNAME_FIELD = 'email'

    slug_field = 'username'

    objects = BlueBottleUserManager()

    class Meta(object):
        abstract = True
        verbose_name = _('member')
        verbose_name_plural = _('members')

        permissions = (
            ('api_read_member', 'Can view members through the API'),
            ('api_read_full_member', 'Can view full members through the API'),
            ('api_add_member', 'Can add members through the API'),
            ('api_change_member', 'Can change members through the API'),
            ('api_delete_member', 'Can delete members through the API'),

            ('api_read_own_member', 'Can view own members through the API'),
            ('api_change_own_member', 'Can change own members through the API'),
            ('api_delete_own_member', 'Can delete own members through the API'),
        )

    class JSONAPIMeta():
        resource_name = 'members'

    def update_deleted_timestamp(self):
        """ Automatically set or unset the deleted timestamp."""
        if not self.is_active and self.deleted is None:
            self.deleted = timezone.now()
        elif self.is_active and self.deleted is not None:
            self.deleted = None

    def generate_username(self):
        """ Generate and set a username if it hasn't already been set. """
        if not self.username:
            username = self.email
            original_username = username
            queryset = self.__class__.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            # Increase the number while searching for the next valid slug
            # depending on the given slug, clean-up
            next_num = 2
            while queryset.filter(username=username):
                username = original_username
                end = str(next_num)
                username = '{0}_{1}'.format(username, end)
                next_num += 1

            # Finally set the generated username.
            self.username = username

    def clean(self):
        self.update_deleted_timestamp()
        self.generate_username()

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = u'{0} {1}'.format(self.first_name, self.last_name)
        return full_name.strip()

    def anonymize(self):
        self.is_active = False
        self.is_anonymized = True
        self.email = '{}-anonymous@example.com'.format(self.pk)  # disabled emails need to be unique too
        self.username = '{}-anonymous@example.com'.format(self.pk)  # disabled emails need to be unique too
        self.remote_id = '{}-anonymous@example.com'.format(self.pk)  # disabled emails need to be unique too
        self.set_unusable_password()
        self.first_name = 'Deactivated'
        self.last_name = 'Member'
        self.user_name = ''
        self.picture = ''
        self.avatar = ''
        self.about_me = ''
        self.gender = ''
        self.birthdate = '1000-01-01'
        self.location = None
        self.website = ''
        self.facebook = ''
        self.twitter = ''
        self.skypename = ''
        self.partner_organization = None

        self.save()

    @property
    def full_name(self):
        return self.get_full_name()

    def get_short_name(self):
        """
        The user is identified by their email address.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User with content type HTML.
        """
        # It's possible to send multi-part text / HTML email by following these
        # instructions: https://docs.djangoproject.com/en/1.5/topics/email
        # /#sending-alternative-content-types
        msg = EmailMessage(subject, message, from_email, [self.email])
        msg.content_subtype = 'html'  # Main content is now text/html
        msg.send()

    def get_jwt_token(self):
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

        payload = jwt_payload_handler(self)
        token = jwt_encode_handler(payload)
        return token

    def get_login_token(self):
        return login_token_generator.make_token(self)

    @property
    def short_name(self):
        return self.get_short_name()

    @cached_property
    def is_initiator(self):
        return self.own_initiatives.exists() or self.activity_managers_initiatives.exists()

    @cached_property
    def is_supporter(self):
        from bluebottle.funding.states import DonorStateMachine
        from bluebottle.funding.models import Donor
        return bool(self.contributor_set.instance_of(Donor).
                    filter(status=DonorStateMachine.succeeded.value).count())

    @cached_property
    def is_volunteer(self):
        from bluebottle.time_based.models import (
            DateParticipant,
            DeadlineParticipant,
            PeriodicParticipant,
            ScheduleParticipant,
        )
        from bluebottle.time_based.states import ParticipantStateMachine

        return bool(
            self.contributor_set.instance_of(
                DateParticipant,
                PeriodicParticipant,
                DeadlineParticipant,
                ScheduleParticipant,
            )
            .filter(status=ParticipantStateMachine.accepted.value)
            .count()
        )

    @cached_property
    def amount_donated(self):
        from bluebottle.funding.states import DonorStateMachine
        from bluebottle.funding.models import Donor
        from bluebottle.funding.utils import calculate_total
        donations = self.contributor_set.instance_of(Donor).filter(
            status=DonorStateMachine.succeeded.value
        )
        return calculate_total(donations)

    @cached_property
    def time_spent(self):
        from bluebottle.time_based.models import TimeContribution, TimeContributionStateMachine
        total = TimeContribution.objects.filter(
            contributor__user=self,
            status=TimeContributionStateMachine.succeeded
        ).aggregate(
            time_spent=models.Sum('value')
        )['time_spent'] or datetime.timedelta()

        return total.total_seconds() / 3600

    @cached_property
    def subscribed(self):
        return self.campaign_notifications

    def reset_disable_token(self):
        # Generates a random UUID and converts it to a 32-character
        # hexidecimal string
        token = uuid.uuid4().hex
        self.disable_token = token
        self.save()

    def get_disable_token(self):
        if not self.disable_token:
            self.reset_disable_token()
        return self.disable_token

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.generate_username()
        super(BlueBottleBaseUser, self).save(force_insert, force_update, using, update_fields)


@receiver(post_save)
def send_welcome_mail_callback(sender, instance, created, **kwargs):
    from django.contrib.auth import get_user_model

    USER_MODEL = get_user_model()
    if getattr(settings, "SEND_WELCOME_MAIL") and \
            isinstance(instance, USER_MODEL) and \
            created and \
            instance.is_active and \
            not instance.welcome_email_is_sent:
        if valid_email(instance.email):
            send_welcome_mail(user=instance)


@receiver(post_save)
def connect_to_segments(sender, instance, created, **kwargs):
    from django.contrib.auth import get_user_model

    USER_MODEL = get_user_model()
    if isinstance(instance, USER_MODEL) and '@' in instance.email:
        user_email_domain = instance.email.split('@')[1]
        for segment in Segment.objects.filter(email_domains__icontains=user_email_domain).all():
            instance.segments.add(segment)
