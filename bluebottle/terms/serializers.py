from rest_framework import serializers
from bluebottle.terms.models import Terms, TermsAgreement


class TermsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terms
        fields = ('id', 'date', 'version', 'contents')


class TermsAgreementSerializer(serializers.ModelSerializer):
    # FIXME: returning a primary key should have the format xxx_id for the field name
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    terms = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TermsAgreement
        fields = ('id', 'terms', 'user', 'created')
