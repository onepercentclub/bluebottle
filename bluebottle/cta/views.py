from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import bluebottle.cta.types  # noqa: F401
from bluebottle.cta.framework import dismiss, get_actions

CONTENT_TYPE = 'application/vnd.api+json'


class RawJSONAPIParser(JSONParser):
    media_type = CONTENT_TYPE


class RawJSONAPIRenderer(JSONRenderer):
    media_type = CONTENT_TYPE
    format = 'vnd.api+json'


def serialize(item):
    return {
        'type': 'cta/actions',
        'id': item.id,
        'attributes': {
            'actionType': item.type,
            'group': item.group,
            'severity': item.severity,
            'title': item.title,
            'message': item.message,
            'count': item.count,
            'url': item.url,
            'created': item.created,
            'isDemo': item.is_demo,
            'snoozedUntil': item.snoozed_until,
        },
    }


class ActionList(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (RawJSONAPIRenderer, JSONRenderer)

    def get(self, request):
        include_snoozed = request.query_params.get('filter[snoozed]') == '1'
        items = get_actions(request.user, include_snoozed=include_snoozed)
        active = [item for item in items if not item.snoozed_until]
        counts = {}
        for item in active:
            counts[item.type] = counts.get(item.type, 0) + 1

        return Response(
            {
                'data': [serialize(item) for item in items],
                'meta': {
                    'count': len(active),
                    'counts': counts,
                    'pagination': {'page': 1, 'pages': 1, 'count': len(items)},
                },
            },
            content_type=CONTENT_TYPE,
        )


class ActionDetail(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (RawJSONAPIParser, JSONParser)
    renderer_classes = (RawJSONAPIRenderer, JSONRenderer)

    def delete(self, request, pk):
        if not dismiss(request.user, pk):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        attributes = request.data.get('data', {}).get('attributes', {})
        value = next(
            (attributes[key] for key in ('snoozeDays', 'snooze-days', 'snooze_days') if key in attributes), 0
        )
        try:
            days = int(value)
        except (TypeError, ValueError):
            days = 0
        if days < 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not dismiss(request.user, pk, snooze_until=timezone.now() + timedelta(days=days)):
            return Response(status=status.HTTP_404_NOT_FOUND)
        item = next(
            (item for item in get_actions(request.user, include_snoozed=True) if item.id == pk), None
        )
        data = serialize(item) if item else {'type': 'cta/actions', 'id': pk}
        return Response({'data': data}, content_type=CONTENT_TYPE)
