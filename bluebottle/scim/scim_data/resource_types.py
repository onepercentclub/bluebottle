from django.core.urlresolvers import reverse_lazy

RESOURCE_TYPES = [{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
    "id": "User",
    "name": "User",
    "endpoint": "/Users",
    "description": "User Account",
    "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
    "schemaExtensions": [
        {
            "schema":
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
            "required": True
        }
    ],
    "meta": {
        "location": reverse_lazy('scim-resource-type-detail', args=('User', )),
        "resourceType": "ResourceType"
        }
    }, {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
    "id": "Group",
    "name": "Group",
    "endpoint": "/Groups",
    "description": "Group",
    "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
    "meta": {
        "location": reverse_lazy('scim-resource-type-detail', args=('Group', )),
        "resourceType": "ResourceType"
    }
}]
