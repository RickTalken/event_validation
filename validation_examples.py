from core import (
    Pass,
    Fail,
    constraint,
    BaseEvent,
    BaseConstraintContext,
    BaseConstraintContextType,
)


#
# This is an example that just use the default validate().
#
class PersonEvent(BaseEvent):
    def __init__(self, name=None, age=None) -> None:
        self.name = name
        self.age = age

    @constraint
    def name_constraint(self, context: BaseConstraintContextType = None):
        return (
            Pass()
            if self.name is not None
            else Fail(field_name="NAME", reason="Name is required!")
        )

    @constraint
    def age_constraint(self, context: BaseConstraintContextType = None):
        return (
            Pass()
            if isinstance(self.age, int)
            else Fail(field_name="AGE", reason="Age must be numeric!")
        )


person_event = PersonEvent()
result = person_event.validate()
if result.PASSED:
    print("Blank person should have failed but it passed!")
else:
    print(f"Result of blank person is a Fail: {result.errors}")
# >> Result of blank person is a Fail: [('NAME', 'Name is required!'), ('AGE', 'Age must be numeric!')]

person_event = PersonEvent(name="Tom Brady")
result = person_event.validate()
if result.PASSED:
    print("Name only person should have failed but it passed!")
else:
    print(f"Result of person with just a name is a Fail: {result.errors}")
# >> Result of person with just a name is a Fail: [('AGE', 'Age must be numeric!')]

person_event = PersonEvent(age=46)
result = person_event.validate()
if result.PASSED:
    print("Age only person should have failed but it passed!")
else:
    print(f"Result of person with just an age is a Fail: {result.errors}")
# >> Result of person with just an age is a Fail: [('NAME', 'Name is required!')]

person_event = PersonEvent(name="Tom Brady", age=46)
print(f"Result of a fully materialized person is: {person_event.validate()}")
# >> Result of a fully materialized person is: Pass()


#
# This is an example that overrides the base validate() to provide custom rule application.
#
class PetEvent(BaseEvent):
    def __init__(self, name=None, nickname=None) -> None:
        self.name = name
        self.nickname = nickname

    @constraint
    def name_constraint(self, context: BaseConstraintContextType = None):
        return (
            Pass()
            if self.name is not None
            else Fail(field_name="NAME", reason="Name not provided!")
        )

    @constraint
    def nickname_constraint(self, context: BaseConstraintContextType = None):
        return (
            Pass()
            if self.nickname is not None
            else Fail(field_name="NICKNAME", reason="Nickname not provided!")
        )

    def validate(self, context: BaseConstraintContextType = None):
        """
        This validation overides the default. It requires the pet to have either or both a name or nickname.
        """
        return self.apply_constraint(self.name_constraint) | self.apply_constraint(
            self.nickname_constraint
        )


pet_event = PetEvent()
result = pet_event.validate()
if result.PASSED:
    print("Nameless pet should have failed but it passed!")
else:
    print(f"Result of nameless pet is a Fail: {result.errors}")
# >> Result of nameless pet is a Fail: [('NAME', 'Name not provided!'), ('NICKNAME', 'Nickname not provided!')]

pet_event = PetEvent(name="Deuce")
result = pet_event.validate()
print(f"Result of a pet with name but no nickname is: {result}")
# >> Result of a pet with name but no nickname is: Pass()


#
# In this example, the credit card must have a name and number. Also, the number must be an integer.
# It is an example of where you might do simple validation first and then if that pass, do more expensive
# validation like querying a database.
#
class CreditCardEvent(BaseEvent):
    def __init__(self, name=None, cc_number=None) -> None:
        self.name = name
        self.cc_number = cc_number

    @constraint
    def name_constraint(self, context: BaseConstraintContextType = None):
        return (
            Pass()
            if self.name is not None
            else Fail(field_name="NAME", reason="Name not provided!")
        )

    @constraint
    def cc_number_required_constraint(self, context: BaseConstraintContextType = None):
        return (
            Pass()
            if self.cc_number is not None
            else Fail(
                field_name="CREDIT CARD NUMBER",
                reason="Credit card number not provided!",
            )
        )

    @constraint
    def cc_number_is_integer_constraint(
        self, context: BaseConstraintContextType = None
    ):
        """This would probably be something that goes to a database rather than this simple example."""
        raise NotImplementedError("This should be implemented in the context")

    def validate(self, context: BaseConstraintContextType = None):
        """
        This validation overides the default. It requires the credit card to have either or both a name or nickname.
        """
        return (
            self.apply_constraint(self.name_constraint)
            & self.apply_constraint(self.cc_number_required_constraint)
        ).on_pass(self, self.cc_number_is_integer_constraint, context)


class DjangoAppContext(BaseConstraintContext):
    """
    This example is just checking if the credit card number is an integer but in a more realistic implementation,
    this would probably use the Django ORM to get some information from the database (e.g. does the cc exist).

    The DjangoAppContext would include Django logic and probably a connection verses another application context
    that might use a psycopg connection to look something up in the database.
    """

    @constraint
    def cc_number_is_integer_constraint(
        self, context: BaseConstraintContextType = None
    ):
        return (
            Pass()
            if isinstance(self.cc_number, int)
            else Fail(
                field_name="CREDIT CARD NUMBER",
                reason="Credit card number must be a integer!",
            )
        )


credit_card_event = CreditCardEvent(name="Rick")
django_context = DjangoAppContext()

result = credit_card_event.validate(context=django_context)
if result.PASSED:
    print("Credit card without number should have failed but it passed!")
else:
    print(f"Result of credit card without number is a Fail: {result.errors}")
# >> Result of credit card without number is a Fail: [('CREDIT CARD NUMBER', 'Credit card number not provided!')]

credit_card_event = CreditCardEvent(name="Rick", cc_number="Not a Number")
result = credit_card_event.validate(context=django_context)
if result.PASSED:
    print("Credit card without number should have failed but it passed!")
else:
    print(f"Result of credit card with non-integer number is a Fail: {result.errors}")
# >> Result of credit card with non-integer number is a Fail: [('CREDIT CARD NUMBER', 'Credit card number must be a integer!')]

credit_card_event = CreditCardEvent(name="Rick", cc_number=1234)
print(
    f"Result of a correctly materialized credit card is: {credit_card_event.validate(context=django_context)}"
)
# >> Result of a correctly materialized credit card is: Pass()
