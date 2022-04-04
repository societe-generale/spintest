# Spintest

Functional scenario interpreter.

Spintest is a library that facilitates the integration and functional test of APIs. It takes as parameters a list of URLs and a list of tasks (also called scenarios) that will be executed against the specified URLs.

Each task represents an API call and provides some options in order to validate or react to the response. By default the task is a success if the HTTP code returned is `2XX` (200 to 299 included), but it is possible to specify the error code or the body that are expected. It is also possible to provide a list of rollback tasks (or task references) that are executed should the task fail.<br/>
The response of the API calls can be stored in order to be used in a future task.
The task scenarios can also be run concurrently in each URL.

## Installation

The package can be installed using PIP.

```
$ pip install spintest
```

## URLs and tasks definition

The url list is a list of endpoints. A route added here will not be evaluated because the route definition is set on the task.

```
[
    "https://foo.com",
    "https://bar.com"
]
```

The task definition is a little bit more detailed.<br />A scenario is a list of tasks possibly dependent to each other.

A single task follows the following schema :

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
    Optional("fail_on"): [{
        Optional("code"): int,
        Optional("body"): Or(dict, str),
        Optional("expected_match", default="strict"): Or("partial", "strict"),
    }],
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
- **header** (optional) is a dictionary of headers. Default is JSON application headers. For Oauth endpoint it is not necessary to add the appropriate header with the token (if the token is specified).
- **output** (optional) Variable definition where Spintest puts the result of the call. This result can be used later in another task using Jinja syntax.
- **expected** (optional) is an expected HTTP response code or response body.
    - **code** (optional) is the expected HTTP code.
    - **body** (optional) is an expected response body. You can put a value to *null* if you don't want to check the value of a key but you will have to set all keys. It also checks nested list and dictionary unless you put "null" instead.
    - **expected_match** is an option to check partially the keys present on your response body. By default it is set to strict.
- **fail_on** (optional) is a list of error HTTP response code or response body. Once one of these error occurs, the test fails without retries.
    - **code** (optional) is the expected HTTP code.
    - **body** (optional) is an expected response body. You can put a value to *null* if you don't want to check the value of a key but you will have to set all keys. It also checks nested list and dictionary unless you put "null" instead.
    - **expected_match** is an option to check partially the keys present on your response body. By default it is set to strict.
- **retry** (optional) is the number of retries if it fails (default is 0).
- **delay** (optional) is the time in second to wait between retries (default is 1).
- **ignore** (optional) is to allow to continue the scenario in case of error of the task.
- **rollback** (optional) is a list of task names or tasks that are triggered should the task fail.


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

Here is another example with an interaction between two routes :

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

As seen here, the first task has a key `output`. This way it is possible to store the output of this first task into a `test_output` variables and be able to use it in following tasks in Jinja templating language.
Moreover, the second task has a key `expected`. The specific return code `204` is expected.

Finally here is a last example that shows how to run tasks in parallel.

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

Here two URLS are provided and the option `parallel` wad added in the `spintest` function.<br/>
Without this option, the scenario will be executed iteratively on every URLS.

But with this option, the each task of the scenario will be executed concurrently for every URLS.

One last word on the expected option. Here we want to validate that a certain key (`result`) is present from the output. We don't mind about the value of this key so we just set it to `None`. The option `expected_match` set to `partial` indicates that we don't want to a task failure if there is more key in the API response than expected.

### Token management

Oauth token can be automatically included into the task headers.

- Tokens can be directly hard coded

```python
urls = ["http://test.com"]
tasks = []

spintest(urls, tasks, token= 'ABC')
```

- A method that generates a token can be given instead of a token

```python
urls = ["http://test.com"]
tasks = []

spintest(urls, tasks, token=create_token)
```

### Rollback actions

A list of rollback tasks that are executed in case of a task failure can be specified.

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

The name of a task can be specified in order to prevent rewriting them

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
        "route": "test",
    }
]

spintest(urls, tasks)
```

### Run the tasks one by one

It is also possible to further control the flow of the task execution to perform additional actions between tasks ( clean up / additional settings / ... )


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


The `next()` method throws a `StopAsyncIteration` if there are no tasks left to execute.

Note: The method `next()` can be used in parallel mode. In this case the method returns a list with the result of the task against each URLs.



### Type convertion

Task template evaluation always returns a string, but sometimes the target API expects a non-string value.<br/>
It is possible to convert it a the corresponding type if needed

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

### Generate report

Since the version 0.3.0 of spintest, generating reports of test execution is possible.

The report will contain all information that were written [here](https://github.com/societe-generale/spintest#urls-and-tasks-definition), and on each tasks the return payload and the execution time are attached.<br/>
At the end of the report the total execution time of the tests is indicated.

To use this functionality use this piece of code :

```
from spintest import spintest

urls = ["https://test.com"]
tasks = [
    {
        "method": "GET",
        "route": "test",
    }
]

result = spintest(urls, tasks, generate_report="report_name")
assert True is result
```

A report with the name "report_name" will be create.<br/>
To avoid to creating multiple "report_name", this report will be overwrote on each test execution.

### Raise to avoid long test execution

The test no longer retries and fails immediately once one of the "fail_on" definition is met.


```
from spintest import spintest
urls = ["https://test.com"]

tasks = [
    {
        "method": "GET",
        "route": "test",
        "expected": {
            "body": {"result": "Success"},
            "expected_match": "partial",
        },
        "fail_on": [
            {
                "code": 409,
            },
            {
                "body": {"result": "Failed"},
                "match": "partial",
            },
            {
                "body": {"result": "Error"},
                "match": "partial",
            },
        ],
        "retry": 15,
    }
]

result = spintest(urls, tasks, generate_report="report_name")
assert True is result
```
