from django.core.urlresolvers import reverse_lazy

SERVICE_PROVIDER_CONFIG = {
    "schemas":
    ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
    "patch": {
        "supported": False
        },
    "bulk": {
        "supported": False,
        },
    "filter": {
        "supported": False,
        "maxResults": 1000
        },
    "changePassword": {
        "supported": False
        },
    "sort": {
        "supported": False
        },
    "etag": {
        "supported": False
        },
    "authenticationSchemes": [
        {
            "name": "OAuth Bearer Token",
            "description":
            "Authentication scheme using the OAuth Bearer Token Standard",
            "specUri": "http://www.rfc-editor.org/info/rfc6750",
            "type": "oauthbearertoken",
            "primary": True
            },
        ],
    "meta": {
        "location": reverse_lazy('scim-service-provider-config'),
        "resourceType": "ServiceProviderConfig",
        "created": "2010-01-23T04:56:22Z",
        "lastModified": "2011-05-13T04:42:34Z",
        "version": "W\/\"3694e05e9dff594\""
        }
    }
