Here is an example of implementing a DynamoDB table using Fluxional.

```python title="app.py" linenums="1"

from fluxional import Fluxional

flux = Fluxional("AwesomeProject")

flux.add_dynamodb(
    remove_on_delete=True, # When destroying the stack, the table will be deleted
    partition_key={"key_name": "pk", "key_type": "string"},
    sort_key={"key_name": "sk", "key_type": "number"},
    local_secondary_indexes=[
        {
            "index_name": "local_index",
            "sort_key": {"key_name": "local_sk", "key_type": "string"},
        }
    ],
    global_secondary_indexes=[
        {
            "index_name": "global_index",
            "partition_key": {"key_name": "global_pk", "key_type": "string"},
            "sort_key": {"key_name": "global_sk", "key_type": "string"},
        }
    ],
)
```
