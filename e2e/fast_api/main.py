from fluxional import Fluxional
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()
flux = Fluxional("FluxE2EFastAPI")

flux.settings.development.enable_local = True


@app.get("/test")
def hello_world():
    return "Hello, World2!"


flux.add_api(Mangum(app))

handler = flux.handler()
