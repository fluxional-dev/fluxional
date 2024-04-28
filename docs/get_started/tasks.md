```python title="app.py" linenums="1"

from fluxional import Fluxional, TaskEvent, LambdaContext

flux = Fluxional("AwesomeProject")

@flux.run.every(1, "days")
def task_1(event: TaskEvent, context: LambdaContext):
    # Runs every day from deployment

@flux.run.every(1, "hours")
def task_2(event: TaskEvent, context: LambdaContext):
    # Runs every hour from deployment

@flux.run.every(5, "minutes")
def task_3(event: TaskEvent, context: LambdaContext):
    # Runs every 5 minutes from deployment

handler = flux.handler()
```

```python title="app.py" linenums="1"

from fluxional import Fluxional, TaskEvent, LambdaContext

flux = Fluxional("AwesomeProject")

@flx.run.on(hour="3", minute="20")
def task_1(event: TaskEvent, context: LambdaContext):
    # Runs at 3:20 UTC every day

@flx.run.on(hour="3", minute="20", day_of_week="mon")
def task_2(event: TaskEvent, context: LambdaContext):
    # Runs at 3:20 UTC every Monday

handler = flux.handler()
```
