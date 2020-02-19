from bluebottle.activities.states import ReviewStateMachine


class FundingReviewStateMachine(ReviewStateMachine):
    approve = ReviewStateMachine.submitted.to(
        ReviewStateMachine.approved,
        conditions=[
            ReviewStateMachine.is_complete,
            ReviewStateMachine.initiative_is_approved
        ]
    )
