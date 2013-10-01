Templatetags
============

This section discusses the usage of the custom templatetags required
for integration of Handlebars templates in Django templates.

Introduction
------------

Handlebars syntax uses {{variable/or/action}} to bind variables or control
structures to HTML elements, which clashes with Django's template syntax.

A possible solution is Django 1.5's {% verbatim %} tag, which renders the
contents of the block 'as they are'. However, this prevents tags like
{% trans "" %} to work.

To overcome this and allow template inheritance with blocks, `django-templatetag-handlebars`_ was used as base and modified
to accomodate these needs.

.. _django-templatetag-handlebars: https://github.com/makinacorpus/django-templatetag-handlebars


Available tags
--------------
  {% verbatim %}: Django's own tag, ignores all variables and tags.
  
  {% bb_verbatim %}: ignores variables, but renders tags like {% trans %}
  and {% url %}. Caution: does not work with blocks.
  
  {% block_verbatim %}: combination of {% block %} and {% bb_verbatim %}.
  If you need to evaluate a context variable in the template within a block_verbatim block, use a normal {% block %} inside the block_verbatim.