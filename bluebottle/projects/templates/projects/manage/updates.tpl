{% load templatetag_handlebars %}
{% load i18n %}
{% load static %}

{% tplhandlebars "_my_project_tasks_and_updates" %}

    <div class="toolbox">
        <h3 class="toolbox-title">
            <em class="flaticon solid wrench-1"></em>
            {% trans "Crowdsourcing" %}
        </h3>
        <div class="toolbox-content">
            <p>{% trans "Do you need someone to help writing your business plan?" %}</p>
            {{#link-to "projectTaskNew" project.getProject tagName="button" class="btn btn-iconed"}}
                <em class="flaticon solid wrench-1"></em>
                {% trans "Create a new task" %}
            {{/link-to}}
        </div>
    </div>

    <div class="toolbox">
        <h3 class="toolbox-title">
            <em class="flaticon solid megaphone-1"></em>
            {% trans "Project Updates" %}
        </h3>
        <div class="toolbox-content">
            <p>{% trans "Why not? Ask the crowd for feedback on your idea!" %}</p>
            {{#link-to "project" project.getProject tagName="button" class="btn btn-iconed"}}
                <span class="flaticon solid megaphone-1"></span>
                {% trans "Post an Update" %}
            {{/link-to}}
        </div>
    </div>

{% endtplhandlebars %}