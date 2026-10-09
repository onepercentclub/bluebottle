from urllib.parse import urlparse

import inflection

from django.contrib.contenttypes.models import ContentType
from django.db import models, connection
from django.urls import reverse, resolve
from django.utils.translation import gettext_lazy as _

from polymorphic.models import PolymorphicManager, PolymorphicModel

from bluebottle.activity_pub.utils import is_local
from bluebottle.files.models import Image as BluebottleImage


class ActivityPubManager(PolymorphicManager):
    def get_queryset(self):
        qs = self.queryset_class(self.model, using=self._db, hints=self._hints)
        return qs

    def from_iri(self, iri):
        if iri:
            if is_local(iri):
                resolved = resolve(urlparse(iri).path)
                return self.filter(pk=resolved.kwargs['pk']).first()
            else:
                return self.filter(iri=iri).first()


class ActivityPubModel(PolymorphicModel):
    def __init__(self, *args, **kwargs):
        ContentType.objects.clear_cache()
        super().__init__(*args, **kwargs)

    iri = models.URLField(null=True, unique=True)

    objects = ActivityPubManager()

    @property
    def is_local(self):
        return self.iri is None

    @property
    def pub_url(self):
        if self.iri:
            return self.iri
        else:
            model_name = self.__class__.__name__
            return connection.tenant.build_absolute_url(
                reverse(
                    'json-ld:resource',
                    args=(
                        inflection.dasherize(inflection.underscore(model_name)),
                        str(self.pk),
                    )
                )
            )

    class Meta:
        verbose_name = _("GoodUp Connect object")
        verbose_name_plural = _("GoodUp Connect objects")


class Image(ActivityPubModel):
    name = models.CharField(max_length=1000, null=True)
    url = models.URLField(null=True)

    origin = models.OneToOneField(
        BluebottleImage,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_model'
    )

    adopted = models.OneToOneField(
        BluebottleImage,
        null=True,
        on_delete=models.CASCADE,
        related_name='origin'
    )
