```python title="settings.py"

from fluxional import Settings

settings = Settings()

# Your settings ...
```

```python title="main.py"

from fluxional import Fluxional
from settings import settings

flux = Fluxional("AwesomeProject")

flux.set_settings(settings)

handler = flux.handler()

```
