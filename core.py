from functools import reduce
from typing import Any, TypeVar, Union, Callable

PassType = TypeVar("PassType", bound="Pass")
FailType = TypeVar("FailType", bound="Fail")
BaseEventType = TypeVar("BaseEventType", bound="BaseEvent")
ConstraintType = TypeVar("ConstraintType", bound="constraint")
BaseConstraintContextType = TypeVar(
    "BaseConstraintContextType", bound="BaseConstraintContext"
)


class Pass:
    PASSED = True
    FAILED = not PASSED

    def __and__(self, other: Union[PassType, FailType]) -> Union[PassType, FailType]:
        return self if other.PASSED else other

    def __or__(self, other: Union[PassType, FailType]) -> Union[PassType, FailType]:
        return self

    def __str__(self) -> str:
        return "Pass()"

    def on_pass(
        self,
        event: BaseEventType,
        constraint_func: ConstraintType,
        context: BaseConstraintContextType,
    ):
        # get the method from the context or just use the event if there is no context
        method = getattr(context, constraint_func.decorated_method_name)
        return method(event)


class Fail:
    PASSED = False
    FAILED = not PASSED

    def __init__(self, field_name: str, reason: str):
        self._errors = None
        self.field_name = field_name
        self.reason = reason

    @property
    def errors(self):
        if not self._errors:
            self._errors = [(self.field_name, self.reason)]
        return self._errors

    def __and__(self, other: Union[PassType, FailType]) -> Union[PassType, FailType]:
        if not other.PASSED:
            self.errors.append((other.field_name, other.reason))
        return self

    def __or__(self, other: Union[PassType, FailType]) -> Union[PassType, FailType]:
        if other.PASSED:
            return other
        else:
            self.errors.append((other.field_name, other.reason))
            return self

    def __bool__(self):
        return False

    def __str__(self) -> str:
        return f"Fail(field_name='{self.field_name}', reason='{self.reason}')"

    def on_pass(self, *_):
        return self


class constraint:
    def __init__(self, method: Callable) -> None:
        self._method = method

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.decorated_method_name}"

    @property
    def decorated_method(self):
        return self._method

    @property
    def decorated_method_name(self):
        return self._method.__name__

    def __call__(
        self, event, *args, context: BaseConstraintContextType = None, **kwargs
    ):
        if context:
            method = getattr(context, self._method)
            return method(event, *args, **kwargs)
        return self._method(event, *args, **kwargs)


class BaseEvent:
    def apply_constraint(self, constraint_func):
        if not isinstance(constraint_func, constraint):
            raise ValueError(
                f"The constraining function {constraint_func.__name__} was not decorated with @constraint"
            )
        return constraint_func(self)

    def constraints(self):
        return {
            getattr(self, func)
            for func in dir(self)
            if not func.startswith("__") and isinstance(getattr(self, func), constraint)
        }

    def validate(self, context: BaseConstraintContextType = None):
        """
        Default validation just "ands" all constraints defined on the object.
        """
        constraint_results = {
            constraint_func(self, context) for constraint_func in self.constraints()
        }
        invalid_results = {
            result
            for result in constraint_results
            if not isinstance(result, (Pass, Fail))
        }
        if invalid_results:
            raise ValueError("Constraint functions must return Pass or Fail")

        return reduce(lambda a, b: a & b, constraint_results, Pass())


class BaseConstraintContext:
    """
    Subclasses provide context (app) specific logic to augment or override constraints defined on the BaseEvent.

    You would use this if you had a rule that accessed a database but the apps use different logic to access the
    database. For example, if you used the event in a Django app that used the Django ORM and a regular Python app
    that used SQLAlchemy or psycopg.
    """

    def __getattr__(self, name):
        """
        This method will allow you to "catch" references to attributes that don't exist in your object.

        In this case, if a method was called as an event as the first argument and the method is not
        implemented on this object, we use double-dispatch to bounce it back to the event. If the method
        was called without any args or the first arg was NOT an event, we follow convention and raise an
        AttributeError to alert the developer that the method is not defined by the object.
        """

        def double_dispatch(*args, **kwargs):
            if not args:
                raise AttributeError(
                    f"{self.__class__.__name__} object has no attribute '{name}'"
                )
            event, *args = args
            if isinstance(event, BaseEvent):
                event_method = getattr(event, name)
                if isinstance(event_method, constraint):
                    return event_method.decorated_method(event, *args, **kwargs)
                return event_method(*args, **kwargs)
            else:
                raise AttributeError(
                    f"{self.__class__.__name__} object has no attribute '{name}'"
                )

        return double_dispatch
