{% extends 'token/base.tpl' %}
{% load i18n %}

{% block content %}
    <h1>
        {% trans "Logout" %}
    </h1>
    {{error}}
{% endblock %}
