import os
import random
import string
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import lazy

from django_extensions.db.fields import ModificationDateTimeField
from djchoices.choices import DjangoChoices, ChoiceItem
from rest_framework_jwt.settings import api_settings

from bluebottle.bb_accounts.utils import valid_email
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.clients import properties
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Country
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.utils.utils import StatusDefinition
from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import Address


# TODO: Make this generic for all user file uploads.
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


# Our custom user model is based on option 3 from Two Scoops of Django
# - Chapter 16: Dealing With the User Model.
class BlueBottleUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email address must be set')
        email = BlueBottleUserManager.normalize_email(email)
        user = self.model(email=email, is_staff=False, is_active=True,
                          is_superuser=False,
                          last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.generate_username()
        user.reset_disable_token()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


def get_language_choices():
    """ Lazyly get the language choices."""
    return properties.LANGUAGES


def get_default_language():
    """ Lazyly get the default language."""
    return properties.LANGUAGE_CODE


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

    email = models.EmailField(_('email address'), max_length=254, unique=True,
                              db_index=True)
    username = models.CharField(_('username'), unique=True, max_length=254)
    is_staff = models.BooleanField(
        _('staff status'), default=False, help_text=_(
            'Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(
        _('active'), default=False,
        help_text=_(
            'Designates whether this user should be treated as active. Unselect this instead of deleting '
            'accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    updated = ModificationDateTimeField()
    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)
    user_type = models.CharField(_('Member Type'), max_length=25,
                                 choices=UserType.choices,
                                 default=UserType.person)

    # Public Profile
    first_name = models.CharField(_('first name'), max_length=100, blank=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True)
    place = models.CharField(_('Location your at now'), max_length=100,
                             blank=True)
    location = models.ForeignKey('geo.Location', help_text=_('Location'),
                                 null=True, blank=True)
    favourite_themes = models.ManyToManyField(ProjectTheme, blank=True)
    skills = models.ManyToManyField('tasks.Skill', blank=True)

    last_seen = models.DateTimeField(_('Last Seen'), null=True, blank=True)

    # TODO Use generate_picture_filename (or something) for upload_to
    picture = ImageField(_('picture'), upload_to='profiles', blank=True)

    is_co_financer = models.BooleanField(
        _('Co-financer'), default=False,
        help_text=_(
            'Donations by co-financers are shown in a separate list on the project page.'
            'These donation will always be visible.'))

    can_pledge = models.BooleanField(
        _('Can pledge'), default=False,
        help_text=_('User can create a pledge donation.'))

    about_me = models.TextField(_('about me'), max_length=265, blank=True)

    # Private Settings

    # Use lazy for the choices and default, so that tenant properties
    # will be correctly loaded
    primary_language = models.CharField(
        _('primary language'), max_length=5,
        help_text=_('Language used for website and emails.'),
        choices=lazy(get_language_choices, tuple)(),
        default=lazy(get_default_language, str)())
    share_time_knowledge = models.BooleanField(_('share time and knowledge'),
                                               default=False)
    share_money = models.BooleanField(_('share money'), default=False)
    newsletter = models.BooleanField(_('newsletter'),
                                     help_text=_('Subscribe to newsletter.'),
                                     default=True)
    phone_number = models.CharField(_('phone number'), max_length=50,
                                    blank=True)
    gender = models.CharField(_('gender'), max_length=6, blank=True,
                              choices=Gender.choices)
    birthdate = models.DateField(_('birthdate'), null=True, blank=True)

    disable_token = models.CharField(max_length=32, blank=True, null=True)

    campaign_notifications = models.BooleanField(_('Project Notifications'),
                                                 default=True)

    objects = BlueBottleUserManager()

    # The Fields are back again...

    website = models.URLField(_('website'), blank=True)

    facebook = models.CharField(_('facebook profile'), max_length=50,
                                blank=True)

    twitter = models.CharField(_('twitter profile'), max_length=15, blank=True)

    skypename = models.CharField(_('skype profile'), max_length=32, blank=True)

    USERNAME_FIELD = 'email'
    # Only email and password is required to create a user account but this is how you'd require other fields.
    # REQUIRED_FIELDS = ['first_name', 'last_name']

    slug_field = 'username'

    class Meta:
        abstract = True
        verbose_name = _('member')
        verbose_name_plural = _('members')

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
            queryset = self._default_manager.all()
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

    @property
    def short_name(self):
        return self.get_short_name()

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

    @property
    def task_count(self):
        """
        Returns the number of tasks a user is the author of  and / or is a
        task member in
        """
        task_count = Task.objects.filter(author=self).count()
        taskmember_count = TaskMember.objects.filter(
            member=self, status__in=['applied', 'accepted', 'realized']).count()

        return task_count + taskmember_count

    @property
    def tasks_performed(self):
        """ Returns the number of tasks that the user participated in."""
        return TaskMember.objects.filter(
            member=self, status='realized').count()

    def get_donations_qs(self):
        qs = Donation.objects.filter(order__user=self)
        return qs.filter(order__status__in=[StatusDefinition.PENDING,
                                            StatusDefinition.SUCCESS])

    @property
    def donation_count(self):
        """ Returns the number of donations a user has made """
        return self.get_donations_qs().count()

    @cached_property
    def funding(self):
        """ Returns the number of projects a user has donated to """
        return self.get_donations_qs().distinct('project').count()

    @property
    def projects_supported(self):
        return self.funding + self.sourcing

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.generate_username()

        super(BlueBottleBaseUser, self).save(force_insert, force_update, using,
                                             update_fields)
        try:
            self.address
        except UserAddress.DoesNotExist:
            self.address = UserAddress.objects.create(user=self)
            self.address.save()

        if self.location:
            self.address.country = self.location.country
            self.address.save()


class UserAddress(Address):
    class AddressType(DjangoChoices):
        primary = ChoiceItem('primary', label=_("Primary"))
        secondary = ChoiceItem('secondary', label=_("Secondary"))

    address_type = models.CharField(_("address type"), max_length=10,
                                    blank=True, choices=AddressType.choices,
                                    default=AddressType.primary)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                verbose_name=_("user"), related_name="address")

    def save(self, *args, **kwargs):
        if not self.country:
            code = getattr(properties, 'DEFAULT_COUNTRY_CODE', None)
            if Country.objects.filter(alpha2_code=code).count():
                self.country = Country.objects.get(alpha2_code=code)
        super(UserAddress, self).save(*args, **kwargs)

    class Meta:
        db_table = 'members_useraddress'
        verbose_name = _("user address")
        verbose_name_plural = _("user addresses")


from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import send_welcome_mail
from django.conf import settings


@receiver(post_save)
def send_welcome_mail_callback(sender, instance, created, **kwargs):
    from django.contrib.auth import get_user_model

    USER_MODEL = get_user_model()
    if getattr(settings, "SEND_WELCOME_MAIL") and \
            isinstance(instance, USER_MODEL) and created:
        if valid_email(instance.email):
            send_welcome_mail(user=instance)
