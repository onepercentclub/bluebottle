from rest_framework import serializers

from bluebottle.pages.models import Page
from bluebottle.terms.models import Terms, TermsAgreement


class TermsSerializer(serializers.ModelSerializer):
    page = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Page.objects.all()
    )

    class Meta:
        model = Terms
        fields = ('id', 'date', 'version', 'page', 'contents')


class TermsAgreementSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    terms = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TermsAgreement
        fields = ('id', 'terms', 'user', 'created')
