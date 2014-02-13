import os
import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.mail.message import EmailMessage
from django.db import models
from django.db.models import options as options
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import ModificationDateTimeField
from djchoices.choices import DjangoChoices, ChoiceItem
from sorl.thumbnail import ImageField


options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer',)


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
        user = self.model(email=email, is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.generate_username()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


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

    class Availability(DjangoChoices):
        one_to_four_week = ChoiceItem('1-4_hours_week', label=_('1-4 hours per week'))
        five_to_eight_week = ChoiceItem('5-8_hours_week', label=_('5-8 hours per week'))
        nine_to_sixteen_week = ChoiceItem('9-16_hours_week', label=_('9-16 hours per week'))
        one_to_four_month = ChoiceItem('1-4_hours_month', label=_('1-4 hours per month'))
        five_to_eight_month = ChoiceItem('5-8_hours_month', label=_('5-8 hours per month'))
        nine_to_sixteen_month = ChoiceItem('9-16_hours_month', label=_('9-16 hours per month'))
        lots_of_time = ChoiceItem('lots_of_time', label=_('I have all the time in the world. Bring it on :D'))
        depends_on_task = ChoiceItem('depends', label=_('It depends on the content of the tasks. Challenge me!'))

    class UserType(DjangoChoices):
        person = ChoiceItem('person', label=_('Person'))
        company = ChoiceItem('company', label=_('Company'))
        foundation = ChoiceItem('foundation', label=_('Foundation'))
        school = ChoiceItem('school', label=_('School'))
        group = ChoiceItem('group', label=_('Club / association'))

    email = models.EmailField(_('email address'), max_length=254, unique=True, db_index=True)
    username = models.SlugField(_('username'), unique=True)
    is_staff = models.BooleanField(
        _('staff status'), default=False, help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(
        _('active'), default=False,
        help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting '
                    'accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    updated = ModificationDateTimeField()
    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)
    user_type = models.CharField(_('Member Type'), max_length=25, choices=UserType.choices, default=UserType.person)

    # Public Profile
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    website = models.URLField(_('website'), blank=True)
    # TODO Use generate_picture_filename (or something) for upload_to
    picture = ImageField(_('picture'), upload_to='profiles', blank=True)
    about = models.TextField(_('about'), max_length=265, blank=True)
    why = models.TextField(_('why'), max_length=265, blank=True)
    availability = models.CharField(_('availability'), max_length=25, blank=True, choices=Availability.choices)
    # max length is not entirely clear, however over 50 characters throws errors on facebook
    facebook = models.CharField(_('facebook profile'), max_length=50, blank=True)
    # max length: see https://support.twitter.com/articles/14609-changing-your-username
    twitter = models.CharField(_('twitter profile'), max_length=15, blank=True)
    skypename = models.CharField(_('skype profile'), max_length=32, blank=True)

    # Private Settings
    primary_language = models.CharField(
        _('primary language'), max_length=5, help_text=_('Language used for website and emails.'),
        choices=settings.LANGUAGES)
    share_time_knowledge = models.BooleanField(_('share time and knowledge'), default=False)
    share_money = models.BooleanField(_('share money'), default=False)
    newsletter = models.BooleanField(_('newsletter'), help_text=_('Subscribe to newsletter.'), default=False)
    phone_number = models.CharField(_('phone number'), max_length=50, blank=True)
    gender = models.CharField(_('gender'), max_length=6, blank=True, choices=Gender.choices)
    birthdate = models.DateField(_('birthdate'), null=True, blank=True)

    objects = BlueBottleUserManager()

    USERNAME_FIELD = 'email'
    # Only email and password is required to create a user account but this is how you'd require other fields.
    # REQUIRED_FIELDS = ['first_name', 'last_name']

    slug_field = 'username'

    class Meta:
        abstract = True
        verbose_name = _('member')
        verbose_name_plural = _('members')
        # specifying the serializer here allows us to leave the urls/views untouched while
        # modifying the serializer for the user model
        default_serializer = 'bluebottle.accounts.serializers.UserProfileSerializer'

    def update_deleted_timestamp(self):
        """ Automatically set or unset the deleted timestamp."""
        if not self.is_active and self.deleted is None:
            self.deleted = timezone.now()
        elif self.is_active and self.deleted is not None:
            self.deleted = None

    def generate_username(self):
        """ Generate and set a username if it hasn't already been set. """
        if not self.username:
            # Default to something so Django doesn't complain.
            username = 'x'
            if self.first_name or self.last_name:
                # The ideal condition.
                username = slugify((self.first_name + self.last_name).replace(' ', ''))
            elif self.email and '@' in self.email:
                # The best we can do if there's no first or last name.
                email_name, domain_part = self.email.strip().rsplit('@', 1)
                username = slugify(email_name.replace(' ', ''))

            # Strip username depending on max_length attribute of the slug field.
            max_length = self._meta.get_field('username').max_length
            username = username[:max_length]
            original_username = username

            # Exclude the current model instance from the queryset used in finding the next valid slug.
            queryset = self._default_manager.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            # Increase the number while searching for the next valid slug depending on the given slug, clean-up
            next_num = 2
            while queryset.filter(username=username):
                username = original_username
                end = str(next_num)
                end_len = len(end)

                if len(username) + end_len > max_length:
                    username = username[:max_length - end_len]

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
        full_name = '{0} {1}'.format(self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        The user is identified by their email address.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User with content type HTML.
        """
        # It's possible to send multi-part text / HTML email by following these instructions:
        # https://docs.djangoproject.com/en/1.5/topics/email/#sending-alternative-content-types
        msg = EmailMessage(subject, message, from_email, [self.email])
        msg.content_subtype = 'html'  # Main content is now text/html
        msg.send()

    @property
    # For now return the first address found on this user.
    def address(self):
        addresses = self.useraddress_set.all()
        if addresses:
            return addresses[0]
        else:
            return None

    @property
    def short_name(self):
        return self.get_short_name()
