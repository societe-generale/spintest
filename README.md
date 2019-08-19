# Spintest

Functional scenario interpreter.

Spintest is a library that facilitates the integration and functional test of APIs. It takes a list of URLs in parameter and a list of tasks (also called scenario) that will be executed against the specified URLs.

Each task represents an API call and provides some options in order to validate or react to the response. Indeed, by default the task is in success if the HTTP code returned is between `200` and `299` included, but you can specify the error code or the body you expect. You can also provide a list of rollback tasks (or task references) that is executed if the task fails.

Also, the response of the API call can be stored in order to be used in a future task.

Finally, you can choose to run the task scenario concurrently on each URL.

## Installation

You can install the package using PIP.

```
$ pip install spintest
```

## URLs and tasks definition

The url list is just a list of endpoints. A route added here will not be evaluated because the route definition is set on the task.

```
[
    "https://foo.com",
    "https://bar.com"
]
```

The task definition is a little bit more complex. A scenario is a list of tasks possibly dependent to each other.

A single task follow this schema :

```
{
    "method": str,
    Optional("route", default="/"): str,
    Optional("name"): str,
    Optional("body"): dict,
    Optional(
        "headers",
        default={"Accept": "application/json", "Content-Type": "application/json"},
    ): dict,
    Optional("output"): str,
    Optional("expected"): {
        Optional("code"): int,
        Optional("body"): Or(dict, str),
        Optional("expected_match", default="strict"): Or("partial", "strict"),
    },
    Optional("retry", default=0): int,
    Optional("delay", default=1): int,
    Optional("ignore", default=False): bool,
    Optional("rollback"): [Or(str, dict)],
}
```

- **method** is the HTTP method of the request (GET, POST, DELETE, ...). Only a valid HTTP method is accepted.
- **route** (optional) is the route to test on the endpoint. It will be appended of the current URL (default is "/")
- **name** (optional) is the name of the task. Mandatory if you want to use that task in a rollback.
- **body** (optional) is a request body.
- **header** (optional) is a dictionary of headers. Default is JSON application headers. For Oauth endpoint you don't need to add the appropriate header with the token (if you specify the token).
- **output** (optional) Variable definition where Spintest put the result of the call. This result can be used later in an other task using Jinja syntax.
- **expected** (optional) is an expected HTTP response code or response body.
    - **code** (optional) is the expected HTTP code.
    - **body** (optional) is an expected response body. You can put a value to *null* if you don't want to check the value of a key but you will have to set all keys. It also checks nested list and dictionary unless you put "null" instead.
    - **expected_match** is an option to check partially the keys present on your response body. By default it is set to strict.
- **retry** (optional) is the number of retries if it fails (default is 0).
- **delay** (optional) is the time in second to wait between retries (default is 1).
- **ignore** (optional) is if you want to continue the scenario in case of error of this task.
- **rollback** (optional) is a list of task names or tasks that is triggered in case of failure of the task.


## Usage

A first example with a single route.

```python
from spintest import spintest

urls = ["https://test.com"]
tasks = [
    {
        "method": "GET",
        "route": "test",
    }
]

result = spintest(urls, tasks)
assert True is result
```

This test will perform a GET call into `https://test.com/test` and expect a return code between `200` and `299` included.

Here is another example with an interation between two routes :

```python
from spintest import spintest

urls = ["https://test.com"]
tasks = [
    {
        "method": "POST",
        "route": "test",
        "output": "test_output",
        "body": {"name": "Disk1", "size": 20},
    },
    {
        "method": "DELETE",
        "route": "volumes/{{ test_output['id'] }}",
        "expected": {"code": 204},
    }
]

result = spintest(urls, tasks)
assert True is result
```

As you can see, the first task has a key `output`. This way you can store the output of this first task into a `test_output` variables and be able to use it in following tasks in Jinja templating language.
Morevoer, the second task has a key `expected`. Here we want to check a specific return code `204`.

Finally a last example that show how to run tasks in several task in parallel.

```python
from spintest import spintest

urls = ["https://foo.com", "https://bar.com"]
tasks = [
    {
        "method": "GET",
        "route": "test",
        "expected": {
            "body": {"result": None},
            "expected_match": "partial",
        }
    }
]

result = spintest(urls, tasks, parallel=True)
assert True is result
```

Here we provided two URLS and we have added the option `parallel` in `spintest` function. Without this option, the scenario will be executed iteratively on every URLS.

But with this option, the each task of the scenario will be executed concurrently for every URLS.

One last word on the expected option. Here we want to validate that a certain key (`result`) is present from the output. We don't mind about the value of this key so we just set it to `None`. The option `expected_match` set to `partial` indicates that we don't want to a task failure if there is more key in the API response than expected.

### Token management

You can automatically include Oauth token into the task headers.

- You can directly hard code token

```python
urls = ["http://test.com"]
tasks = []

spintest(urls, tasks, token= 'ABC')
```

- You can give the generate function that create your token :

```python
urls = ["http://test.com"]
tasks = []

spintest(urls, tasks, token=create_token)
```

### Rollback actions

You can specify a list of rollback task that is executed in case of task failure.

```python
from spintest import spintest

urls = ["https://test.com"]
tasks = [
    {
        "method": "POST",
        "route": "test",
        "rollback": [
            {
                "method": "DELETE",
                "route": "test,
            }
        ]
    }
]

spintest(urls, tasks)
```

You can also specify the name of a task to avoid rewriting them.

```python
from spintest import spintest

urls = ["https://test.com"]
tasks = [
    {
        "method": "POST",
        "route": "test",
        "rollback": [
            "test_delete"
        ]
    },
    {
        "name": "test_delete",
        "method": "DELETE",
        "route": "test,
    }
]

spintest(urls, tasks)
```

### Run the tasks one by one


You can also go further to control the flow of the task execution. It can be useful to perform other actions between tasks (clean up, external settings, ...)


```python

import asyncio

from spintest import TaskManager


urls = ["http://test.com"]
tasks = [{"method": "GET", "route": "/test"}]
token = "90b7aa25-870a-4dda-a1fc-b57cf0fbf278"

loop = asyncio.get_event_loop()

manager = TaskManager(urls, tasks, token=token)
result = loop.run_until_complete(manager.next())

assert "SUCCESS" == result["status"]
```


The `next()` method throw a `StopAsyncIteration` if there is no task left to execute.

Note: You can use the method `next()` in parallel mode. In that situation the method returns a list with the result of the task against each URLs.


### Type convertion

Task template evaluation always returns a string, but sometimes the target API expects a non-string value,
it can be useful to convert it to the corresponding type.

Spintest provides a set of json value converters that provide such functionality.

- Int -> Converts value to a `int`
- List -> Converts value to a `list`
- Float -> Converts value to a `float`
- Bool -> Converts value to a `bool`

```python
from spintest import spintest

urls = ["http://test.com"]
tasks = [
    {
        "method": "GET",
        "route": "persons",
        "output": "value",
        # Returns
        # {
        #     "age": 20,
        #     "height": 1.85,
        #     "alive": True,
        # }
    },
    {
        "method": "POST",
        "route": "persons",
        "body": {
            # int convertion
            "age_str": "{{ value.person['age'] }}", # {"age_str": "20"},
            "age": Int("{{ value.person['age'] }}"), # {"age": 20},

            # float convertion
            "height_str": "{{ value.person['height'] }}", # {"height_str": "1.85"},
            "height": Float("{{ value.person['height'] }}"), # {"height": 1.85},

            # bool convertion
            "alive_str": "{{ value.person['alive'] }}", # {"alive_str": "True"},
            "alive": Bool("{{ value.person['alive'] }}"), # {"alive": true},
        }
    }
]

spintest(urls, tasks, token=token_write)
```
