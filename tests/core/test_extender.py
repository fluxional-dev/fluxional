from fluxional import Fluxional, Extender


def test_extender_register():
    ## API DECORATOR TESTING ##
    flux = Fluxional("Test")

    extender = Extender()

    @extender.api
    def api(event, context):
        return True

    flux.register(extender)

    assert api(event=None, context=None)
    assert flux.handler()(event={"httpMethod": "GET"}, context={})

    ## API INLINE TESTING ##
    extender = Extender()

    def api_2(event, context):
        return "api_2"

    extender.add_api(api_2)

    flux.register(extender)

    assert api_2(event=None, context=None)
    assert flux.handler()(event={"httpMethod": "GET"}, context={}) == "api_2"

    ## WEBSOCKET ##
    @extender.websocket.on_connect
    def connect(event, context):
        return True

    @extender.websocket.on("event")
    def event(event, context):
        return True

    flux.register(extender)

    assert connect(event=None, context=None)
    assert flux.handler()(
        event={"requestContext": {"routeKey": "$connect"}}, context={}
    )
    assert event(event=None, context=None)
    assert flux.handler()(event={"requestContext": {"routeKey": "event"}}, context={})

    ## S3 ##
    extender = Extender()

    @extender.storage.on_upload
    def storage_create(event, context):
        return True

    @extender.storage.on_delete
    def storage_delete(event, context):
        return True

    flux.register(extender)

    assert storage_create(event=None, context=None)
    assert storage_delete(event=None, context=None)
    assert flux.handler()(
        event={
            "Records": [{"eventName": "ObjectCreated:Put", "eventSource": "aws:s3"}]
        },
        context={},
    )

    ## Tasks ##
    extender = Extender()

    @extender.run.every(1, "minutes")
    def task(event, context):
        return True

    @extender.run.on()
    def task_2(event, context):
        return True

    flux.register(extender)

    assert task(event=None, context=None)
    assert task_2(event=None, context=None)
    assert flux.handler()(
        event={"schedule_type": "RateSchedule", "schedule_name": "task"},
        context={},
    )
    assert flux.handler()(
        event={"schedule_type": "CronSchedule", "schedule_name": "task_2"},
        context={},
    )

    ## Events ##
    extender = Extender()

    @extender.event
    def an_event(event, context):
        return True

    flux.register(extender)

    assert an_event(event=None, context=None)
    assert flux.handler()(
        event={
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": '{"event_name":"an_event","data":"hello"}',
                }
            ]
        },
        context={},
    )
