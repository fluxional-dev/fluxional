from fluxional import Fluxional, LambdaContext, TaskEvent

flux = Fluxional("FluxE2ETasks")


@flux.run.every(1, "minutes")
def hello(event: TaskEvent, context: LambdaContext):
    print("Run Task Triggered!")
    print(event)


@flux.run.on(hour="0", minute="35")
def hello_2(event: TaskEvent, context: LambdaContext):
    print("On Task Triggered!")
    print(event)


handler = flux.handler()
