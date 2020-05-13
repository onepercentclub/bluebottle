from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine

from bluebottle.assignments.models import Assignment, Applicant


class AssignmentStateMachine(ActivityStateMachine):
    model = Assignment


class ApplicantStateMachine(ContributionStateMachine):
    model = Applicant
