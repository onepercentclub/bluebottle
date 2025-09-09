from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import EffortContribution, Organizer
from bluebottle.fsm.state import (
    AllStates,
    EmptyState,
    ModelStateMachine,
    State,
    Transition,
    register,
)
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.utils.utils import is_back_office


class ActivityStateMachine(ModelStateMachine):
    draft = State(
        _("draft"),
        "draft",
        _(
            "The activity has been created, but not yet completed. An activity manager is still editing the activity."
        ),
    )
    submitted = State(
        _("submitted"),
        "submitted",
        _("The activity has been submitted and is ready to be reviewed."),
    )
    needs_work = State(
        _("needs work"),
        "needs_work",
        _(
            "The activity needs changes before it can be approved."
        ),
    )
    rejected = State(
        _("rejected"),
        "rejected",
        _(
            "The activity does not fit the programme or does not comply with the rules. "
            "The activity does not appear on the platform, but counts in the report. "
            "The activity cannot be edited by an activity manager."
        ),
    )
    deleted = State(
        _("deleted"),
        "deleted",
        _(
            "The activity has been removed. The activity does not appear on "
            "the platform and does not count in the report. "
            "The activity cannot be edited by an activity manager."
        ),
    )
    cancelled = State(
        _("cancelled"),
        "cancelled",
        _(
            "The activity is not executed. The activity does not appear on the platform, "
            "but counts in the report. The activity cannot be edited by an activity manager."
        ),
    )

    expired = State(
        _("expired"),
        "expired",
        _(
            "The activity has ended, but did have any contributions . The activity does not appear on the platform, "
            "but counts in the report. The activity cannot be edited by an activity manager."
        ),
    )
    open = State(_("open"), "open", _("The activity is accepting new contributions."))
    succeeded = State(
        _("succeeded"), "succeeded", _("The activity has ended successfully.")
    )

    def is_complete(self):
        """all required information has been submitted"""
        return not list(self.instance.required)

    def is_back_office(self):
        return is_back_office()

    def is_valid(self):
        """all fields passed validation and are correct"""
        return not list(self.instance.errors)

    def initiative_is_approved(self):
        """the initiative has been approved"""
        if not self.instance.initiative_id:
            return True
        return self.instance.initiative.status == "approved"

    def initiative_is_submitted(self):
        """the initiative has been submitted"""
        return not self.instance.initiative_id or self.instance.initiative.status in (
            "submitted",
            "approved",
        )

    def initiative_is_not_approved(self):
        """the initiative has not yet been approved"""
        return not self.initiative_is_approved()

    def can_publish(self):
        """the activity can be published. Activities can be published if they are reviewed or if reviewing is disabled.
        Funding activities cannot be published"""
        from bluebottle.funding.models import Funding

        if isinstance(self.instance, Funding):
            return False

        if not self.instance.initiative_id:
            if not InitiativePlatformSettings.load().enable_reviewing:
                return True
            return False

        if self.instance.initiative.status == "approved":
            return True

        return False

    def can_submit(self):
        """the activity can be submitted"""
        from bluebottle.funding.models import Funding

        if isinstance(self.instance, Funding):
            if not self.instance.initiative_id:
                return True
            if (
                self.instance.initiative.status == "approved"
                or self.instance.initiative.status == "submitted"
            ):
                return True
            return False
        if not InitiativePlatformSettings.load().enable_reviewing:
            return False
        if InitiativePlatformSettings.load().terms_of_service and not self.instance.tos_accepted:
            return False
        if not self.instance.initiative_id:
            return True
        if self.instance.initiative.status in ["submitted"]:
            return True
        return False

    def is_staff(self, user):
        """user is a staff member"""
        return user.is_staff or user.is_superuser

    def is_owner(self, user):
        """user is the owner"""
        return (
            user in self.instance.owners
            or user.is_superuser
            or user.is_staff
        )

    def should_auto_approve(self):
        """the activity should be approved automatically"""
        return self.instance.auto_approve

    initiate = Transition(
        EmptyState(),
        draft,
        name=_("Create"),
        description=_("The activity will be created."),
    )

    submit = Transition(
        [
            draft,
            needs_work,
        ],
        submitted,
        description=_("The activity will be submitted for review."),
        automatic=False,
        name=_("Submit"),
        permission=is_owner,
        conditions=[is_complete, is_valid, can_submit],
    )

    auto_submit = Transition(
        [
            draft,
            needs_work,
        ],
        submitted,
        description=_("The activity will be submitted for review."),
        automatic=True,
        name=_("Submit"),
        conditions=[is_complete, is_valid],
    )

    reject = Transition(
        AllStates(),
        rejected,
        name=_("Reject"),
        description=_(
            "Reject if the activity does not align with your program or guidelines "
            "The activity manager will not be able to edit or resubmit it, and it will "
            "not appear on the search page in the frontend. The activity will still "
            "be available in the back office and appear in your reporting."
        ),
        automatic=False,
        permission=is_staff,
    )

    publish = Transition(
        [
            submitted,
            draft,
            needs_work,
        ],
        open,
        name=_("Publish"),
        description=_("Your activity will be open to contributions."),
        automatic=False,
        passed_label=_("published"),
        permission=is_owner,
        conditions=[is_complete, is_valid, can_publish],
    )

    auto_publish = Transition(
        [
            submitted,
            draft,
            needs_work,
        ],
        open,
        description=_("Automatically publish activity when initiative is approved"),
        automatic=True,
        name=_("Auto-publish"),
        conditions=[is_complete, is_valid, should_auto_approve],
    )

    auto_approve = Transition(
        [submitted, rejected],
        open,
        name=_("Approve"),
        automatic=True,
        conditions=[is_complete, is_valid, should_auto_approve],
        description=_(
            "The activity will be visible in the frontend and people can apply to "
            "the activity."
        ),
    )

    approve = Transition(
        [
            submitted,
            needs_work,
            draft
        ],
        open,
        name=_("Approve"),
        automatic=False,
        permission=is_staff,
        description=_(
            "The activity will be published and visible in the frontend for people to contribute to,"
        ),
    )

    request_changes = Transition(
        submitted,
        needs_work,
        name=_('Request changes'),
        description=_(
            "The activity needs changes before it can be approved. "
            "Inform the activity manager of the changes required. "
            "The activity manager will then be able to edit and resubmit the activity."
        ),
        conditions=[],
        automatic=False,
        permission=is_staff,
    )

    cancel = Transition(
        [
            open,
            succeeded,
        ],
        cancelled,
        name=_("Cancel"),
        description=_(
            "Cancel if the activity will not be executed. "
            "An activity manager will no longer be able edit the activity "
            "and it won't show up on the search page in the frontend. "
            "The activity will still be visible in the back office "
            "and appear in your reporting."
        ),
        description_front_end=_(
            "The activity ends and people no longer register. All current participants will fail too."
        ),
        permission=is_owner,
        automatic=False,
    )

    restore = Transition(
        [
            rejected,
            cancelled,
            deleted,
            expired
        ],
        needs_work,
        name=_("Restore"),
        description=_(
            "The activity status is changed to 'Needs work'. "
            "Then you can make changes to the activity and submit it again."
        ),
        description_front_end=_(
            "The activity will be set to the status ‘Needs work’. "
            "Then you can make changes to the activity and submit it again."
        ),
        automatic=False,
        permission=is_owner,
    )

    reopen = Transition(
        [
            rejected,
            cancelled,
            deleted,
            expired
        ],
        open,
        name=_("Reopen"),
        description=_(
            "Open the activity again, e.g. when a slot reopens."
        ),
        automatic=True,
    )

    expire = Transition(
        [open, submitted, succeeded],
        expired,
        name=_("Expire"),
        description=_(
            "The activity will be cancelled because no one has signed up for the registration deadline."
        ),
        automatic=True,
    )

    delete = Transition(
        [draft, needs_work],
        deleted,
        name=_("Delete"),
        automatic=False,
        permission=is_owner,
        hide_from_admin=True,
        description=_(
            "Delete the activity if you do not want it to be included in the report. "
            "The activity will no longer be visible on the platform, "
            "but will still be available in the back office."
        ),
        description_front_end=_(
            "Delete the activity. You will not be able to retrieve it afterwards."
        ),
    )

    succeed = Transition(
        [
            open,
            expired
        ],
        succeeded,
        name=_("Succeed"),
        automatic=True,
    )


class ContributorStateMachine(ModelStateMachine):
    new = State(_("New"), "new", _("The user started a contribution"))
    succeeded = State(
        _("Succeeded"), "succeeded", _("The contribution was successful.")
    )
    failed = State(_("Failed"), "failed", _("The contribution failed."))

    def is_user(self, user):
        return self.instance.user == user

    succeed = Transition(
        [new, succeeded, failed],
        succeeded,
        name=_("Succeed"),
        description=_("The contribution was successful."),
    )

    initiate = Transition(
        EmptyState(),
        new,
        name=_("Initiate"),
        description=_("The contribution was created."),
    )

    fail = Transition(
        [new, succeeded, failed],
        failed,
        name=_("Fail"),
        description=_("The contribution failed. It will not be visible in reports."),
    )

    reset = Transition(
        [new, succeeded, failed],
        new,
        name=_("Reset"),
        description=_("Reset the contribution to new."),
    )


class ContributionStateMachine(ModelStateMachine):
    new = State(_("New"), "new", _("The user started a contribution"))
    succeeded = State(
        _("Succeeded"), "succeeded", _("The contribution was successful.")
    )
    failed = State(_("Failed"), "failed", _("The contribution failed."))

    def is_user(self, user):
        return self.instance.user == user

    initiate = Transition(
        EmptyState(),
        new,
        name=_("Initiate"),
        description=_("The contribution was created."),
    )

    fail = Transition(
        [new, succeeded, failed],
        failed,
        name=_("Fail"),
        description=_("The contribution failed. It will not be visible in reports."),
    )

    succeed = Transition(
        [new, succeeded, failed],
        succeeded,
        name=_("Succeed"),
        description=_("The contribution succeeded. It will be visible in reports."),
    )

    reset = Transition(
        [new, succeeded, failed],
        new,
        name=_("Reset"),
        description=_("The contribution is reset."),
    )


@register(Organizer)
class OrganizerStateMachine(ContributorStateMachine):
    succeed = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.succeeded,
            ContributorStateMachine.failed
        ],
        ContributorStateMachine.succeeded,
        name=_("Succeed"),
        description=_("The organizer was successful in setting up the activity."),
    )
    fail = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.succeeded,
            ContributorStateMachine.failed
        ],
        ContributorStateMachine.failed,
        name=_("fail"),
        description=_("The organizer failed to set up the activity."),
    )
    reset = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.succeeded,
            ContributorStateMachine.failed
        ],
        ContributorStateMachine.new,
        name=_("reset"),
        description=_("The organizer is still busy setting up the activity."),
    )


@register(EffortContribution)
class EffortContributionStateMachine(ContributionStateMachine):
    pass
