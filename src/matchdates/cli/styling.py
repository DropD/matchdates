from .. import queries


def _color_for_severity(severity: queries.MatchClashSeverity) -> str:
    match severity:
        case queries.MatchClashSeverity.UNPLAYABLE:
            return "red"
        case queries.MatchClashSeverity.PROBABLY_INTENTIONAL:
            return "green"
        case _:
            return "yellow"
