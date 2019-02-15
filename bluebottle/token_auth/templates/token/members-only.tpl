{% extends 'token/base.tpl' %}
{% load i18n %}

{% block content %}
    <h1>
        {% trans "This site is for authenticated members only" %}
    </h1>
{% endblock %}
