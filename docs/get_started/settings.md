```python title="settings.py"

from fluxional import Settings

settings = Settings()

# Your settings ...
settings.build.api_lambda.memory = 128
```

```python title="main.py"

from fluxional import Fluxional
from settings import settings

flux = Fluxional("AwesomeProject")

flux.configure(
    dependencies=["settings.py"] # include the settings file
)
flux.set_settings(settings) # register the settings

handler = flux.handler()

```
