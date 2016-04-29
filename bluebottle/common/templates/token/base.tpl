{% load i18n %}
{% load bb_ember %}
{% load compress %}
{% load static %}
{% load frontend_static %}

<!DOCTYPE HTML>
<html lang="{{ LANGUAGE_CODE }}">

<head>
    <meta charset="utf-8" />
    <meta content="IE=edge,chrome=1" http-equiv="X-UA-Compatible">
    <meta name="viewport" content="width=device-width" />

    <title>{% trans "Bluebottle" %}</title>

    {% block defaults_js %}
        <script type="text/javascript">
            var default_title = '{% blocktrans %}Bluebottle - Share a little. Change the world{%  endblocktrans %}';
            var default_description = '{% blocktrans %}Bluebottle is the global crowdfunding and crowdsourcing platform where you can share a little and change the world, in your very own way. Pick any project you like, support it with 1% of your knowledge, money or time and follow the progress online.{% endblocktrans %}';
            var default_keywords = '{% blocktrans %}crowdfunding, crowdsourcing, platform, developing countries, time, skills, money, doneren, international cooperation, charity{% endblocktrans %}';
        </script>
    {% endblock defaults_js %}

    {% block meta %}
        <meta name="description" content="{% blocktrans %}Bluebottle is the global crowdfunding and crowdsourcing platform where you can share a little and change the world, in your very own way. Pick any project you like, support it with 1% of your knowledge, money or time and follow the progress online.{% endblocktrans %}" />
        <meta name="author" content="{% blocktrans %}Bluebottle{% endblocktrans %}" />
        <meta name="keywords" content="{% blocktrans %}crowdfunding, crowdsourcing, platform, developing countries, time, skills, money, doneren, international cooperation, charity{% endblocktrans %}" />
        <link rel="shortcut icon" href="{% static 'favicon.ico' %}">
    {% endblock %}

    {# Stylesheets #}
	{% block screen_css %}
        <link rel="stylesheet" href="{% frontend_static 'css/main.css' %}" media="screen" />
	{% endblock %}
</head>
<body id="body">
    {% block content %}
        Token
    {% endblock %}
</body>
</html>
