{% extends 'token/base.tpl' %}

{% block content %}
    <h1>Error loging in</h1>

    Server said: {{message}}

    <br />
    <br />
    Go back to <a href='{{TENANT_MAIL_PROPERTIES.website}}'>{{TENANT_MAIL_PROPERTIES.website}}</a> and try to log in again.
{% endblock %}