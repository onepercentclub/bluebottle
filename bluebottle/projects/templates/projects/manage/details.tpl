{% load templatetag_handlebars %}
{% load i18n %}
{% load static %}

{% tplhandlebars "generic_textarea" %}
    {{bb-text-area label=name valueBinding=value hint=description}}
{% endtplhandlebars %}

{% tplhandlebars "generic_text" %}
    {{bb-text-field label=name valueBinding=value hint=description}}
{% endtplhandlebars %}


{% tplhandlebars "generic_radio" %}
    {{bb-radio label=name valueBinding=value optionsBindings=options hint=description}}
{% endtplhandlebars %}


{% tplhandlebars "generic_select" %}
    {{bb-select label=name valueBinding=value options=options}}
{% endtplhandlebars %}



{% tplhandlebars "my_project_details" %}

    <legend>
        <strong>{% trans "Project details" %}</strong>
    </legend>

    <fieldset>
        <ul>
            {{#each field in fields}}
                {{render 'genericField' field projectBinding=this}}
            {{/each}}
        </ul>

    </fieldset>

    {{#if isDirty}}
        <button {{bindAttr class=":btn :btn-iconed :btn-next"}} {{action updateRecordOnServer}}><span class="flaticon solid right-2"></span>{% trans "Save & Next" %}</button>
    {{else}}
        <button {{bindAttr class=":btn :btn-iconed :btn-next"}} {{action goToNextStep}}><span class="flaticon solid right-2"></span>{% trans "Next" %}</button>
    {{/if}}


{% endtplhandlebars %}
