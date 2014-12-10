from rest_framework import viewsets
from bluebottle.bb_follow.models import Follow
from bluebottle.bb_follow.serializers import FollowSerializer

class FollowViewSet(viewsets.ModelViewSet):
	""" This viewset automatically provides 'list' and 'detail' actions for the Follow model"""
	queryset = Follow.objects.all()
	serializer_class = FollowSerializer