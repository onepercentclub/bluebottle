{% extends 'token/base.tpl' %}
{% load static %}

{% block content %}
    <div id="not-logged-in">
        <img src="{% static 'images/site_alt.svg' %}" />
        <h1>Welcome to {{settings.siteName}}</h1>
        <p>It seems your authentication token has expired.
        Please login to use the {{settings.siteName}} Platform</p>

        <a class="btn btn-sec donate-btn" id="sso-login-link"
        href="{{ssoUrl}}?url={{url}}">Login</a>

        <p class="subtext">More text</p>
    </div>
{% endblock %}
