from datetime import datetime
from uuid import uuid4, UUID

from pytz import UTC
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import BaseFuzzyAttribute, FuzzyInteger, FuzzyDateTime

from action_man import models


class FuzzyUuid(BaseFuzzyAttribute):
    def fuzz(self) -> UUID:
        return uuid4()


class Action(SQLAlchemyModelFactory):
    class Meta:
        model = models.Action

    id = FuzzyUuid()
    experiment_id = FuzzyUuid()
    variant_id = FuzzyUuid()
    reward = FuzzyInteger(0, 1)
    context = {}
    last_modified = FuzzyDateTime(datetime.now(tz=UTC))
