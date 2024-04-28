from fluxional import Fluxional
from settings import settings
from services import flux as services

flux = Fluxional("FluxE2EMultiFileProject")
flux.register(services)
flux.set_settings(settings)
flux.configure(dependencies=["services.py", "settings.py"])
handler = flux.handler()
