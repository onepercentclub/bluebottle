from django.db import models
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.conf import settings
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from sorl.thumbnail import ImageField
from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete as TaggableManager
from django.template.defaultfilters import slugify


class ProjectTheme(models.Model):
    """ Themes for Projects. """

    # The name is marked as unique so that users can't create duplicate theme names.
    name = models.CharField(_("name"), max_length=100, unique=True)
    name_nl = models.CharField(_("name"), max_length=100, unique=True)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    description = models.TextField(_("description"), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _("project theme")
        verbose_name_plural = _("project themes")


class ProjectManager(models.Manager):

    def order_by(self, field):

        if field == 'deadline':
            qs = self.get_query_set()
            qs = qs.order_by('projectcampaign__deadline')
            return qs

        if field == 'newest':
            qs = self.get_query_set()
            qs = qs.order_by('projectcampaign__money_needed')
            return qs

        qs = super(ProjectManager, self).order_by(field)
        return qs


class Project(models.Model):
    """ The base Project model. """

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("initiator"), help_text=_("Project owner"), related_name="owner")

    created = CreationDateTimeField(_("created"), help_text=_("When this project was created."))
    updated = ModificationDateTimeField(_('updated'))

    phase = models.CharField(max_length=30, choices=settings.PROJECT_PHASES)

    # Basics
    title = models.CharField(_("title"), max_length=255, unique=True)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    pitch = models.TextField(_("pitch"), blank=True, help_text=_("Pitch your smart idea in one sentence"))

    tags = TaggableManager(blank=True, verbose_name=_("tags"), help_text=_("Add tags"))

    # Extended Description
    description = models.TextField(_("why, what and how"), help_text=_("Blow us away with the details!"), blank=True)
    reach = models.PositiveIntegerField(_("Reach"), help_text=_("How many people do you expect to reach?"), blank=True, null=True)

    # Location
    latitude = models.DecimalField(_("latitude"), max_digits=21, decimal_places=18, null=True, blank=True)
    longitude = models.DecimalField(_("longitude"), max_digits=21, decimal_places=18, null=True, blank=True)
    country = models.ForeignKey('geo.Country', blank=True, null=True)

    # Media
    image = ImageField(_("image"), max_length=255, blank=True, upload_to='project_images/', help_text=_("Main project picture"))
    video_url = models.URLField(_("video"), max_length=100, blank=True, null=True, default='', help_text=_("Do you have a video pitch or a short movie that explains your project. Cool! We can't wait to see it. You can paste the link to the YouTube or Vimeo video here"))

    # Crowd funding
    currency = models.CharField(max_length="10", default='EUR')

    # For convenience and performance we also store money donated and needed here.
    money_asked = models.PositiveIntegerField(default=0, null=True)
    money_donated = models.PositiveIntegerField(default=0, null=True)
    money_needed = models.PositiveIntegerField(default=0, null=True)

    organization = models.ForeignKey('organizations.Organization', null=True, blank=True)

    objects = ProjectManager()

    def __unicode__(self):
        if self.title:
            return self.title
        return self.slug

    @models.permalink
    def get_absolute_url(self):
        """ Get the URL for the current project. """
        return 'project-detail', (), {'slug': self.slug}

    def get_absolute_frontend_url(self):
        url = self.get_absolute_url()
        # insert the hashbang, after the language string
        bits = url.split('/')
        url = "/".join(bits[:2] + ['#!'] + bits[2:])
        return url

    def get_meta_title(self, **kwargs):
        return u"%(name_project)s |  %(country)s" % {
            'name_project': self.title,
            'country': self.country.name if self.country else '',
        }

    def get_fb_title(self, **kwargs):
        title = _(u"{name_project} in {country}").format(
                    name_project = self.title,
                    country = self.country.name if self.country else '',
                )
        return title

    def get_tweet(self, **kwargs):
        """ Build the tweet text for the meta data """
        request = kwargs.get('request')
        if request:
            lang_code = request.LANGUAGE_CODE
        else:
            lang_code = 'en'
        twitter_handle = settings.TWITTER_HANDLES.get(lang_code, settings.DEFAULT_TWITTER_HANDLE)

        title = urlquote(self.get_fb_title())

        # {URL} is replaced in Ember to fill in the page url, avoiding the
        # need to provide front-end urls in our Django code.
        tweet = _(u"{title} {{URL}} via @{twitter_handle}").format(
                    title=title, twitter_handle=twitter_handle
                )

        return tweet

    @property
    def editable(self):
        if self.phase in ('plan-new', 'plan-needs-work', 'plan-approved', 'campaign-running'):
            return True
        return False


    class Meta:
        ordering = ['title']
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.title)
            counter = 2
            qs = Project.objects
            while qs.filter(slug = original_slug).exists():
                original_slug = '%s-%d' % (original_slug, counter)
                counter += 1
            self.slug = original_slug

        if not self.phase:
            self.phase = 'plan-new'
        super(Project, self).save(*args, **kwargs)

