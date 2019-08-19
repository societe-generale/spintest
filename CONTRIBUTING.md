# Contributing

Here is some guidelines to contribute efficiently to this project.

## Installation


You can easily install the project's development dependencies.

```
$ make install-dev
```

To enter pipenv's shell

```
$ make shell
```

## Source code checking

You can test you code compliancy with this command. It includes the
check of the unit tests's code.

```
$ make lint
```

## Test coverage

You can launch the unit tests and see the test coverage with this
command.

```
$ make test
```

Your pull request will be rejected if the code you propose make the take
coverage percentage drop below 92% it will be rejected.

## Code formating

You can format you code nicely with this command (this may change the
code) :

```
$ make format
```

## Quality assessment

You can run all code quality tools with the following command.

```
$ make quality
```

## Version bumping

You can update the version of the project with this command.

```
$ bumpversion [major | minor | patch]
```
