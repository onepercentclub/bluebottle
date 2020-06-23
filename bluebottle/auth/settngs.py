cms_permissions = [
    'cms.add_activitiescontent',
    'cms.add_categoriescontent',
    'cms.add_contentlink',
    'cms.add_greeting',
    'cms.add_homepage',
    'cms.add_homepage',
    'cms.add_link',
    'cms.add_linkgroup',
    'cms.add_linkpermission',
    'cms.add_linkscontent',
    'cms.add_locationscontent',
    'cms.add_logo',
    'cms.add_logoscontent',
    'cms.add_metric',
    'cms.add_metricscontent',
    'cms.add_projectimagescontent',
    'cms.add_projects',
    'cms.add_projectscontent',
    'cms.add_projectsmapcontent',
    'cms.add_quote',
    'cms.add_quotes',
    'cms.add_quotescontent',
    'cms.add_resultpage',
    'cms.add_shareresultscontent',
    'cms.add_sitelinks',
    'cms.add_siteplatformsettings',
    'cms.add_slide',
    'cms.add_slidescontent',
    'cms.add_stat',
    'cms.add_stats',
    'cms.add_statscontent',
    'cms.add_step',
    'cms.add_stepscontent',
    'cms.add_supportertotalcontent',
    'cms.add_surveycontent',
    'cms.add_taskscontent',
    'cms.add_welcomecontent',
    'cms.api_add_homepage',
    'cms.api_add_resultpage',
    'cms.api_change_homepage',
    'cms.api_change_resultpage',
    'cms.api_delete_homepage',
    'cms.api_delete_resultpage',
    'cms.change_activitiescontent',
    'cms.change_categoriescontent',
    'cms.change_contentlink',
    'cms.change_greeting',
    'cms.change_homepage',
    'cms.change_homepage',
    'cms.change_link',
    'cms.change_linkgroup',
    'cms.change_linkpermission',
    'cms.change_linkscontent',
    'cms.change_locationscontent',
    'cms.change_logo',
    'cms.change_logoscontent',
    'cms.change_metric',
    'cms.change_metricscontent',
    'cms.change_projectimagescontent',
    'cms.change_projects',
    'cms.change_projectscontent',
    'cms.change_projectsmapcontent',
    'cms.change_quote',
    'cms.change_quotes',
    'cms.change_quotescontent',
    'cms.change_resultpage',
    'cms.change_shareresultscontent',
    'cms.change_sitelinks',
    'cms.change_siteplatformsettings',
    'cms.change_slide',
    'cms.change_slidescontent',
    'cms.change_stat',
    'cms.change_stats',
    'cms.change_statscontent',
    'cms.change_step',
    'cms.change_stepscontent',
    'cms.change_supportertotalcontent',
    'cms.change_surveycontent',
    'cms.change_taskscontent',
    'cms.change_welcomecontent',
    'cms.delete_activitiescontent',
    'cms.delete_categoriescontent',
    'cms.delete_contentlink',
    'cms.delete_greeting',
    'cms.delete_homepage',
    'cms.delete_homepage',
    'cms.delete_link',
    'cms.delete_linkgroup',
    'cms.delete_linkpermission',
    'cms.delete_linkscontent',
    'cms.delete_locationscontent',
    'cms.delete_logo',
    'cms.delete_logoscontent',
    'cms.delete_metric',
    'cms.delete_metricscontent',
    'cms.delete_projectimagescontent',
    'cms.delete_projects',
    'cms.delete_projectscontent',
    'cms.delete_projectsmapcontent',
    'cms.delete_quote',
    'cms.delete_quotes',
    'cms.delete_quotescontent',
    'cms.delete_resultpage',
    'cms.delete_shareresultscontent',
    'cms.delete_sitelinks',
    'cms.delete_siteplatformsettings',
    'cms.delete_slide',
    'cms.delete_slidescontent',
    'cms.delete_stat',
    'cms.delete_stats',
    'cms.delete_statscontent',
    'cms.delete_step',
    'cms.delete_stepscontent',
    'cms.delete_supportertotalcontent',
    'cms.delete_surveycontent',
    'cms.delete_taskscontent',
    'cms.delete_welcomecontent',
    'django_summernote.add_attachment',
    'django_summernote.change_attachment',
    'django_summernote.delete_attachment',
    'fluent_contents.add_contentitem',
    'fluent_contents.add_placeholder',
    'fluent_contents.change_contentitem',
    'fluent_contents.change_placeholder',
    'fluent_contents.delete_contentitem',
    'fluent_contents.delete_placeholder',
    'oembeditem.add_oembeditem',
    'oembeditem.change_oembeditem',
    'oembeditem.delete_oembeditem',
    'pages.add_actionitem',
    'pages.add_columnsitem',
    'pages.add_documentitem',
    'pages.add_imagetextitem',
    'pages.add_imagetextrounditem',
    'pages.add_page',
    'pages.api_add_page',
    'pages.api_change_page',
    'pages.api_delete_page',
    'pages.change_actionitem',
    'pages.change_columnsitem',
    'pages.change_documentitem',
    'pages.change_imagetextitem',
    'pages.change_imagetextrounditem',
    'pages.change_page',
    'pages.change_page',
    'pages.delete_actionitem',
    'pages.delete_columnsitem',
    'pages.delete_documentitem',
    'pages.delete_imagetextitem',
    'pages.delete_imagetextrounditem',
    'pages.delete_page',
    'pages.delete_page',
    'quotes.add_quote',
    'quotes.change_quote',
    'quotes.delete_quote',
    'rawhtml.add_rawhtmlitem',
    'rawhtml.change_rawhtmlitem',
    'rawhtml.delete_rawhtmlitem',
    'slides.add_slide',
    'slides.change_slide',
    'slides.delete_slide',
    'text.add_textitem',
    'text.change_textitem',
    'text.delete_textitem',
]

cms_models = [
    perm.replace('add_', '')
    for perm in cms_permissions
    if 'add_' in perm and perm not in [
        'pages.add_page',
        'cms.add_resultpage',
        'cms.add_homepage',
    ]
]
