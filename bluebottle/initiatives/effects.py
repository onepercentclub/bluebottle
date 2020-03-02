from bluebottle.fsm.effects import Effect


class ApproveActivity(Effect):
    post_save = True
    conditions = []

    def execute(self):
        for activity in self.instance.activities.filter(review_status='submitted'):
            activity.review_states.approve()
            activity.save()
