"""Age-based service routing for SafeHaven low-barrier intake.

Age determines the service pathway, never whether a person may request help.
Actual placement, safeguarding, and clinical decisions remain human/provider
decisions.
"""


def age_route(approximate_age: int | None) -> str:
    """Return the appropriate service pathway for an intake."""
    if approximate_age is None:
        return "age_unknown"

    if isinstance(approximate_age, bool) or not isinstance(approximate_age, int):
        raise TypeError("approximate_age must be an integer or None")

    if not 0 <= approximate_age <= 120:
        raise ValueError("approximate_age must be between 0 and 120")

    if approximate_age < 18:
        return "minor_safeguarding"

    if approximate_age <= 24:
        return "tay"

    return "adult_referral"
