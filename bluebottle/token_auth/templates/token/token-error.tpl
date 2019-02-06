{% extends 'token/base.tpl' %}
{% load i18n %}

{% block content %}
    <h1>
        {% trans "Error logging in" %}
    </h1>
    {{message}}
{% endblock %}