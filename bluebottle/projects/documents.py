from django_elasticsearch_dsl import DocType, Index
from bluebottle.projects.models import  Project

# The name of your index
project = Index('projects')
# See Elasticsearch Indices API reference for available settings
project.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@project.doc_type
class ProjectDocument(DocType):
    class Meta:
        model = Project
        fields = [
            'title',
            'story',
            'pitch',
        ]
