from fluxional import Fluxional, LambdaContext, StorageEvent

flux = Fluxional("FluxE2EStorage")

# If not using reactive functions
# flux.settings.storage.enable = True
# Settings
# flux.settings.storage.remove_on_delete = False


@flux.storage.on_upload
def on_upload(event: StorageEvent, context: LambdaContext):
    print("ON Upload")
    print(event)


@flux.storage.on_delete
def on_delete(event: StorageEvent, context: LambdaContext):
    print("ON Delete")
    print(event)


handler = flux.handler()
