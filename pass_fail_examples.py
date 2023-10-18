from core import Pass, Fail

# In a real example, you would have a rule that returns either a Pass object or a Fail object. Here, I just create them.
passed_rule = Pass()


print(f"Pass & Pass: {passed_rule & passed_rule}")
# >> Pass & Pass: Pass()
print(f"Pass | Pass: {passed_rule | passed_rule}")
# >> Pass | Pass: Pass()

# These are monanic so you have to create a new one each test to avoid them continually building on each other
failed_name_rule = Fail(field_name="NAME", reason="Name is required!")
failed_age_rule = Fail(field_name="AGE", reason="Age must be numeric!")
result = failed_name_rule & failed_age_rule
print(f"Fail & Fail: {result}")
print(f"Failed because: {result.errors}")
# >> Fail & Fail: Fail(field_name='NAME', reason='Name is required!')
# >> Failed because: [('NAME', 'Name is required!'), ('AGE', 'Age must be numeric!')]

# These are monanic so you have to create a new one each test or this example will build on the results of the previous
failed_name_rule = Fail(field_name="NAME", reason="Name is required!")
failed_age_rule = Fail(field_name="AGE", reason="Age must be numeric!")
result = failed_name_rule | failed_age_rule
print(f"Fail | Fail: {result}")
print(f"Failed because: {result.errors}")
# >> Fail | Fail: Fail(field_name='NAME', reason='Name is required!')
# >> Failed because: [('NAME', 'Name is required!'), ('AGE', 'Age must be numeric!')]

failed_name_rule = Fail(field_name="NAME", reason="Name is required!")
result = passed_rule & failed_name_rule
print(f"Pass & Fail: {result}")
print(f"Failed because: {result.errors}")
# >> Pass & Fail: Fail(field_name='NAME', reason='Name is required!')
# >> Failed because: [('NAME', 'Name is required!')]

failed_name_rule = Fail(field_name="NAME", reason="Name is required!")
result = passed_rule | failed_name_rule
print(f"Pass | Fail: {result}")
# >> Pass | Fail: Pass()
