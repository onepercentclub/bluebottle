from surveygizmo import SurveyGizmo


class BaseAdapter(object):

    def get_surveys(self):
        raise NotImplementedError()

    def update_surveys(self):
        for survey in self.get_surveys():



class SurveyGizmoAdapter(BaseAdapter):

    def __init__(self):
        self.client = SurveyGizmo(
            api_version='v4',
            api_token = "E4F796932C2743FEBF150B421BE15EB9",
            api_token_secret = "A9fGMkJ5pJF1k"
        )

    def get_surveys(self):
        return self.client.api.survey.list()