from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    EmptyState,
    ModelStateMachine,
    State,
    Transition,
    register,
)
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings


@register(Initiative)
class ReviewStateMachine(ModelStateMachine):
    field = "status"
    model = Initiative

    draft = State(
        _("Draft"),
        "draft",
        _("The initiative has been created and is being worked on."),
    )
    submitted = State(
        _("Submitted"),
        "submitted",
        _("The initiative has been submitted and is ready to be reviewed."),
    )
    needs_work = State(
        _('Needs work'),
        'needs_work',
        _('The initiative needs changes before it can be approved.')
    )
    rejected = State(
        _('Rejected'),
        'rejected',
        _(
            "The initiative does not align with your program or guidelines. "
            "The initiator will not be able to edit or resubmit it, "
            "and it will not appear on the search page in the front end. "
            "The initiative will still be available in the back office and appear in your reporting."
        )
    )
    cancelled = State(
        _("Cancelled"),
        "cancelled",
        _(
            "The initiative is not executed. "
            "The initiative won't show up on the search page in the front end, "
            "but does count in the reporting. "
            "The initiative cannot be edited by the initiator."
        ),
    )
    deleted = State(
        _("Deleted"),
        "deleted",
        _(
            "The initiative is not visible in the frontend and does not count in the reporting. "
            "The initiative cannot be edited by the initiator."
        ),
    )
    approved = State(
        _("Approved"),
        "approved",
        _(
            "The initiative is visible in the frontend and completed activities are open for contributions."
        ),
    )

    archived = State(
        _("Archived"),
        "archived",
        _(
            "The initiative is no longer visible in the frontend and hidden "
            "in the admin. Activities are still available and contributions still "
            "count in reporting."
        ),
    )

    def is_complete(self):
        """The initiative is complete"""
        if self.instance.organization and list(self.instance.organization.required):
            return False

        if self.instance.organization_contact and list(
            self.instance.organization_contact.required
        ):
            return False

        return not list(self.instance.required)

    def is_valid(self):
        """The initiative is valid"""
        if self.instance.organization and list(self.instance.organization.errors):
            return False

        if self.instance.organization_contact and list(
            self.instance.organization_contact.errors
        ):
            return False

        return not list(self.instance.errors)

    def is_staff(self, user):
        """Check if the user is a staff member"""
        return user.is_staff

    def review_needed(self):
        return InitiativePlatformSettings.load().enable_reviewing

    def no_review_needed(self):
        return not InitiativePlatformSettings.load().enable_reviewing

    initiate = Transition(
        EmptyState(),
        draft,
        name=_("Start"),
        description=_("The initiative will be created."),
    )

    submit = Transition(
        [draft, needs_work],
        submitted,
        name=_("Submit"),
        description=_("The initiative will be submitted for review."),
        conditions=[is_complete, is_valid, review_needed],
        automatic=False,
    )

    publish = Transition(
        [draft, needs_work],
        approved,
        name=_("Publish"),
        description=_("The initiative will be published."),
        conditions=[is_complete, is_valid, no_review_needed],
        automatic=False,
    )

    approve = Transition(
        submitted,
        approved,
        name=_("Approve"),
        description=_(
            "The initiative will be published and visible in the frontend. "
            "All completed activities will be open for contributions. "
            "Crowdfunding campaigns require a separate review."
        ),
        conditions=[is_complete, is_valid],
        automatic=False,
        permission=is_staff,
    )

    request_changes = Transition(
        submitted,
        needs_work,
        name=_('Needs work'),
        description=_(
            "The initiative needs changes before it can be approved. "
            "Inform the initiator of the changes required. "
            "The initiator will then be able to edit and resubmit the initiative."
        ),
        conditions=[],
        automatic=False,
        permission=is_staff,
    )

    reject = Transition(
        [
            draft,
            submitted,
            needs_work,
        ],
        rejected,
        name=_('Reject'),
        description=_(
            "Reject if the initiative does not align with your program or guidelines. "
            "The initiator will not be able to edit or resubmit it, "
            "and it will not appear on the search page in the front end. "
            "The initiative will still be available in the back office and appear in your reporting."
        ),
        automatic=False,
        permission=is_staff,
    )

    cancel = Transition(
        [
            approved,
            submitted,
            draft,
        ],
        cancelled,
        name=_("Cancel"),
        description=_(
            "Cancel if the initiative will not be executed. "
            "The initiator will not be able to edit the initiative and "
            "it won't show up on the search page in the front end. "
            "The initiative will still be available in the back office and appear in your reporting."
        ),
        automatic=False,
        permission=is_staff,
    )

    delete = Transition(
        draft,
        deleted,
        name=_("Delete"),
        description=_(
            "Delete the initiative if you don't want it to appear in your reporting. "
            "The initiative will still be available in the back office."
        ),
        automatic=False,
        hide_from_admin=True,
    )

    restore = Transition(
        [rejected, cancelled, deleted],
        needs_work,
        name=_('Restore'),
        description=_(
            "The status of the initiative is set to 'needs work'. "
            "The initiator can edit and submit the initiative again"
        ),
        automatic=False,
        permission=is_staff,
    )

    archive = Transition(
        [approved],
        archived,
        name=_("Archive"),
        description=_("The initiative will be archived."),
        conditions=[],
        automatic=False,
        permission=is_staff,
    )

    unarchive = Transition(
        [archived],
        approved,
        name=_("Unarchive"),
        description=_("The initiative will be approved again."),
        conditions=[is_complete, is_valid],
        automatic=False,
        permission=[is_staff],
    )
