# Event Validation
This is an example of rules processing in a distributed, event driven architecture. The system features multiple event producers (e.g., a Django website, an API, a desktop application, etc.), a message broker, and several event consumer (microservices). For example, if the database only supports a "name" that is 50 character long, producers must ensure that the event's "name" field is no more than 50 characters long. Otherwise, loosely coupled consumers will raise exceptions when writing the "name" field to the database(s).

In this case, all producers and consumers are written in Python and use a common Python package that includes shared logic and event models. Simple validation, such as the length of a field, can be implemented into the models in the shared package. However, complex validation will be context dependent. For example, if an event includes a country code that must match a country code from a Postgres table, how a Django app looks up country codes in Postgres will be different than how a microservice does it using Psycopg. The logic to lookup country codes in a Postgres table is context specific.

In order to accommodate context dependent validations, the rules processing package implements dependency injection so producers can provide their own logic for accessing data in the database to validate events prior to publishing them. This allows the context to override how the rule is applied or to provide a means to apply the rule (for example, if a database connection is required).

## `core.py`
`core.py` includes all of the logic for building event models, defining rules, and validating models. All event models subclass from `BaseEvent`. Rule methods are defined on the event models and decorated with the `@constraint` decorator. They accept an option `context` argument. When the rule is validated, the `@constraint` decorator will redirect to the `context` to validate the rule if the optional `context` argument was passed to the rule. Otherwise, the event definition for the rule will be invoked.

When `validate()` is invoked on an event model, it processes the rules (constraints) and returns either a `Pass` or `Fail` object. By default, `validate()` will gather all of the methods decorated by the `@constraint` decorator and prcess them one by one. Models can override `validate()` to implement more complex validations.

The `Pass` and `Fail` objects provides error accumulation through monadic parsing. You can use `and` and `or` between them like you would with booleans. You can use `on_pass()` to defer execution. At the end of validation, you either get a `Pass` or a `Fail` that has all of the reasons that the event failed.

`BaseConstraintContext` is an abstract base class (although it doesn't have an abstract method). Applications should subclass `BaseConstraintContext` and define any constraints that require application specific logic. The application should pass the context when it does event validation. If the context doesn't implement the constraint, `BaseConstraintContext` simply double dispatches back to the event to apply the constraint.

## `pass_fail_examples.py`
`pass_fail_examples.py` provides examples of using the `Pass` and `Fail` objects.

