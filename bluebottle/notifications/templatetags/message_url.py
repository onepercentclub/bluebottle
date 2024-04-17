from urllib.parse import parse_qs, ParseResult, urlparse, urlencode

from django import template
from django.db import connection

register = template.Library()


@register.simple_tag(takes_context=True)
def message_url(context, path=""):
    parsed = urlparse(path)

    query = parse_qs(parsed.query)

    query["utm_source"] = "platform-mail"
    query["utm_medium"] = "email"
    if "utm_campaign" in context:
        query["utm_campaign"] = context["utm_campaign"]

    return ParseResult(
        parsed.scheme or "https",
        parsed.netloc or connection.tenant.domain_url,
        parsed.path,
        parsed.params,
        urlencode(query),
        parsed.fragment,
    ).geturl()
