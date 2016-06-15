import json
from django.views.generic.base import RedirectView
from django.shortcuts import render, get_object_or_404

from sorl.thumbnail import get_thumbnail

from rest_framework import generics, permissions
from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm


from bluebottle.cms.models import Page
from bluebottle.cms.serializers import PageSerializer
from bluebottle.projects.models import Project


class PageList(generics.ListAPIView):
    serializer_class = PageSerializer

    def get_queryset(self):
        return Page.objects.filter(live=True).all()


class PageDetail(generics.RetrieveAPIView):
    serializer_class = PageSerializer

    def get_queryset(self):
        return Page.objects.filter(live=True).all()


class PageDraftDetail(generics.RetrieveAPIView):
    serializer_class = PageSerializer
    permission_classes = (permissions.IsAdminUser, )

    def get_queryset(self):
        return Page.objects.filter(live=True).all()

    def get_object(self):
        obj = super(PageDraftDetail, self).get_object()
        return obj.get_latest_revision_as_page()


class PreviewPage(RedirectView):

    def get_redirect_url(self):
        import ipdb; ipdb.set_trace()


class PreviewDraftPage(RedirectView):

    def get_redirect_url(self, page_id, **kwargs):
        return '/content-draft/' + page_id


def project_chooser(request):
    projects = Project.objects.order_by('-created')
    is_searching = False

    if 'q' in request.GET or 'p' in request.GET:
        is_searching = True

        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            q = search_form.cleaned_data['q']
            projects = projects.filter(title__icontains=q)

        # Pagination
        paginator, projects = paginate(request, projects, per_page=12)

        return render(request, "cms/chooser/project_results.html", {
            'projects': projects,
            'is_searching': is_searching,
            'search_form': search_form
        })

    paginator, projects = paginate(request, projects, per_page=12)

    return render_modal_workflow(request, 'cms/chooser/project_chooser.html', 'cms/chooser/project_chooser.js', {
        'projects': projects,
        'is_searching': False,
        'search_form': SearchForm()
    })


def project_chosen(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    return render_modal_workflow(
        request, None, 'cms/chooser/project_chosen.js',
        {'project': json.dumps({
            'id': project.id,
            'title': project.title,
            'image': get_thumbnail(project.image, '165x165').url
        })}
    )
