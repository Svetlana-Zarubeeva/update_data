import logging
from typing import Optional, Any
from pipelines.interfaces import ExtractType, LoadType, IExtractor, ITransformer, ILoader, IMetrics, IConnector


class Pipeline:

    def __init__(
        self,
        extractor: IExtractor[ExtractType],
        transformer: ITransformer[ExtractType, LoadType],
        loader: ILoader[LoadType],
        metrics_logger: Optional[IMetrics[ExtractType]] = None
    ):
        self._extractor = extractor
        self._transformer = transformer
        self._loader = loader
        self._metrics_logger = metrics_logger

    def run(self, *args: Any) -> Any:
        logging.info("%s execution started.", str(self))

        extracted_data = self._extractor.extract(*args)

        if self._metrics_logger:
            self._metrics_logger.log_pre_run_metrics(extracted_data)

        transformed_data = self._transformer.transform(extracted_data)
        result = self._loader.load(transformed_data)

        if self._metrics_logger:
            self._metrics_logger.log_post_run_metrics(transformed_data)

        logging.info("%s execution finished.", str(self))
        return result

    def __str__(self) -> str:
        transformer_name = self._transformer.__class__.__name__

        extractor_name = self._extractor.__class__.__name__
        if len(connectors := [attr for attr in self._extractor.__dict__.values() if isinstance(attr, IConnector)]) > 0:
            extractor_name += ("(" + ",".join(connector.__class__.__name__.replace("Connector", "") for connector in connectors) + ")")

        loader_name = self._loader.__class__.__name__
        if len(connectors := [attr for attr in self._loader.__dict__.values() if isinstance(attr, IConnector)]) > 0:
           loader_name += ("(" + ",".join(connector.__class__.__name__.replace("Connector", "") for connector in connectors) + ")")

        return f"Pipeline[{extractor_name}->{transformer_name}->{loader_name}]"
