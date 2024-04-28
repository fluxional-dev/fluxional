from fluxional.dev.runner import FunctionEngine, build_launcher, build_runner_image, run


def test_function_engine():
    # Should no longer check for credentials
    engine = FunctionEngine()
    engine.setup_credentials()


def test_build_launcher():
    assert (
        build_launcher("test.test")
        == "from test import test\\nfrom fluxional.dev.client import DevClient\\nimport os\\nimport json\\nclient = DevClient()\\nclient.connect()\\nevent = json.loads(os.environ.get('EVENT'))\\nevent_id = os.environ.get('EVENT_ID')\\nprint('EVENT_ID: ', event_id)\\nsubscriber_id = os.environ.get('SUBSCRIBER_ID')\\nprint('Acknowledging event...')\\nx = client.publish(f'fluxional/acknowledge/{event_id}', {'subscriber_id': subscriber_id})\\nx.result(timeout=5)\\nprint('Event acknowledged')\\ntry:\\n    result = test(event, None)\\nexcept Exception as e:\\n    print('ERROR:', e)\\n    result = {'statusCode': 500, 'body': 'Internal Server Error'}\\nprint(result)\\nprint('Sending response...')\\nx = client.publish(f'fluxional/response/{event_id}', {'subscriber_id': subscriber_id, 'response': result})\\nx.result(timeout=5)\\nprint('Response sent')\\nclient.disconnect()"
    )


def test_build_runner_image():
    class MockEngine:
        def __init__(self, *args, **kwargs):
            pass

        def build_image(self, *args, **kwargs):
            pass

    build_runner_image("test", "test.test", engine_provider=MockEngine)


def test_run():
    class MockEngine:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, *args, **kwargs):
            pass

        def image_exists(self, *args, **kwargs):
            return True

        def run_container(self, *args, **kwargs):
            pass

    run("test", "test.test", engine_provider=MockEngine)
