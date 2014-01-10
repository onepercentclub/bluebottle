{% load templatetag_handlebars %}
{% load i18n %}
{% load static %}

{% tplhandlebars "my_project_list" %}

    <div class="l-section" id="project-dashboard">

    	{{partial "my_project_top"}}

        <div class="l-wrapper">
            {{#if isLoading}}
                <div class="is-loading-big"><img src="{% get_static_prefix %}images/loading.gif" /> <strong>{% trans "Loading projects" %}</strong></div>
            {{else}}
                <div class="l-content">
                    <header class="l-page-header">
                        <h1>{% trans "Create new project" %}</h1>
                        <p></p>
                    </header>

                    {{#link-to "myProject" 'new' tagName="button" class="btn btn-primary btn-iconed"}}
                        <span class="flaticon solid lightbulb-3"></span>
                        {% trans "Pitch a new smart idea" %}
                    {{/link-to}}
                </div>
            {{/if}}

            <div class="l-content">
	            <ul class="project-list">
	            	{{#each project in controller}}
	                <li class="project-list-item">

                        <span class="project-header">
                            <figure class="project-image">
                                <img {{bindAttr src="project.image.square" alt="project.pitch.title"}} />
                            </figure>
                            <h2 class="project-title">
                                {{ project.title }}
                                {{#if project.isPublic}}
                                    <a {{action "showProject" project.id href=true}} class="project-preview">
    	                                <span class="flaticon solid eye-1"></span>
    	                                {% trans "View public page" %}
    	                            </a>
                                {{/if}}
                            </h2>
                        </span>

				        <div class="project-actions">
				        	{% trans "Phase" %}: <strong>{{ project.phase }}</strong>
                            <br/>
	                        {{#if project.editable}}
	                            {{#link-to "myProject" project tagName="a" class="btn btn-iconed right"}}
	                                <span class="flaticon solid pencil-3"></span>
	                                {% trans "Edit" %}
	                            {{/link-to}}

                            {{else}}
	                                <span class="flaticon solid lock-1"></span>
	                                {% trans "Project is locked" %}
	                        {{/if}}

				        </div>
				    </li>
					{{/each}}
	            </ul>
			</div>
        </div>
    </div>

{% endtplhandlebars %}
