Opentelemetry can be enabled by using the following settings:

```python
from fluxional import Settings

settings = Settings()

settings.monitoring.otel.enable = True
settings.monitoring.otel.endpoint = "http://your-endpoint"
settings.monitoring.otel.service_name = "your-service-name"
settings.monitoring.otel.exporter_otlp_headers = "some-headers=here"
```

This will send your traces / metrics to your desired observability platform using the http/protobuf protocol.
