Feature: User joins an activity on a date
  As a user I can join an activity
  on a date.

  Scenario: Join activity
    Given A user interacts with the API
    Given There is an activity on a date
    When User joins activity
    Then User is part of the activity