import umongo

from . import models


@models.INSTANCE.register
class Team(umongo.Document):
    name = umongo.fields.StringField(required=True, unique=True)


@models.INSTANCE.register
class PlayedTeamMatch(umongo.Document):
    start = umongo.fields.ReferenceField(models.Player)
    end = umongo.fields.ReferenceField(models.MatchResult)
    team = umongo.fields.ReferenceField(Team)


@models.INSTANCE.register
class PlayedMatch(umongo.Document):
    start = umongo.fields.ReferenceField(models.Player)
    end = umongo.fields.ReferenceField(models.MatchResult)
    team = umongo.fields.ReferenceField(Team)
    event = umongo.fields.StringField(required=True)
    number = umongo.fields.IntegerField(allow_none=True)

    @property
    def event_attribute_name(self) -> str:
        return self.event + (
            f"_{self.number}" if self.number is not None else ""
        )

    @property
    def is_home_player(self) -> bool:
        return (
            self.team.fetch().name
            == self.end.fetch().match_date.fetch().home_team()
        )

    @property
    def won(self):
        home_won = getattr(
            self.end.fetch(), self.event_attribute_name
        ).fetch().home_won
        return (
            (home_won and self.is_home_player) or
            (not home_won and not self.is_home_player)
        )


def update_results() -> None:
    """Go through match results and construct the graph."""
    for result in models.MatchResult.find({}):
        update_result_subgraph(result)


def update_result_subgraph(result: models.MatchResult) -> None:
    """Look at one match result and update the subgraph."""
    unique_players: set[tuple[str, str]] = set()
    match_date = result.match_date.fetch()
    for event_name, event in result.event_items:
        away_team_name = match_date.away_team
        away_team = Team.find_one({"name": away_team_name})
        home_team_name = match_date.home_team
        home_team = Team.find_one({"name": home_team_name})
        if not away_team:
            away_team = Team(name=away_team_name)
            away_team.commit()
        if not home_team:
            home_team = Team(name=home_team_name)
            home_team.commit()
        for player in event.players["away"]:
            unique_players.add((player.name, away_team.name))
            if not PlayedMatch.find_one({
                "start": player,
                "end": result,
                "event": event_name[0],
                "number": event_name[1]
            }):
                PlayedMatch(
                    start=player,
                    end=result,
                    team=away_team,
                    event=event_name[0],
                    number=event_name[1]
                ).commit()
        for player in event.players["home"]:
            unique_players.add((player.name, home_team.name))
            if not PlayedMatch.find_one({
                "start": player,
                "end": result,
                "event": event_name[0],
                "number": event_name[1]
            }):
                PlayedMatch(
                    start=player,
                    end=result,
                    team=home_team,
                    event=event_name[0],
                    number=event_name[1]
                ).commit()
    for player_name, team_name in unique_players:
        player = models.Player.find_one({"name": player_name})
        if not PlayedMatch.find_one({"start": player, "end": result}):
            PlayedTeamMatch(
                start=player,
                end=result,
                team=Team.find_one({"name": team_name})
            ).commit()
