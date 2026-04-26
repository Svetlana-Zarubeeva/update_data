import logging
from datetime import date, timedelta
from typing import Any, Optional
from pipelines.pipeline import Pipeline


class Runner:
    _pipeline: Pipeline

    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline

    def run_until_result(self, result: Any) -> None:
        while self._pipeline.run() != result:
            continue

    def run_in_daterange(
        self,
        from_date: date | str,
        to_date: Optional[date | str] = None,
        *,
        days_per_run: int = 1,
    ) -> None:
        if isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)
        if isinstance(to_date, str):
            to_date = date.fromisoformat(to_date)

        if to_date is None:
            if from_date > date.today():
                logging.info(
                    "Pipeline execution skipped 'cause start date `%s` are greater than today's date.", from_date
                )
                return
        else:
            if from_date > to_date:
                logging.info(
                    "Pipeline execution skipped 'cause start date `%s` are greater than end date `%s`.", from_date, to_date
                )
                return

        current_dates = [from_date]

        while True:
            if to_date is None:
                is_last_run = current_dates[-1] >= date.today()
            else:
                is_last_run = to_date >= current_dates[-1]

            if (len(current_dates) >= days_per_run) or is_last_run:
                self._pipeline.run(current_dates, is_last_run)
                current_dates = [current_dates[-1] + timedelta(days=1)]
                if is_last_run:
                    return
            else:
                current_dates.append(current_dates[-1] + timedelta(days=1))
