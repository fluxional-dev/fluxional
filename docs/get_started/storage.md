```python title="app.py" linenums="1"

from fluxional import Fluxional, StorageEvent, LambdaContext

flux = Fluxional("Backend")

@flux.storage.on_upload
def upload_event(event: StorageEvent, context: LambdaContext):
    ...

@flux.storage.on_delete
def delete_event(event: StorageEvent, context: LambdaContext):
    ...

handler = flux.handler()

```

If you are not using the reactive functions, you need to enable the storage explicitly to create
a storage.

```python title="app.py" linenums="1"

from fluxional import Fluxional, Storage, Environment

flux = Fluxional("Backend")
env = Environment()

# Enable storage
flux.settings.storage.enable = True

# Access bucket name at deployment time
bucket_name = env.storage_bucket_name

handler = flux.handler()

```
