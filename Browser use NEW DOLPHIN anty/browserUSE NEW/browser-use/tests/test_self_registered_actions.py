import pytest
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from browser_use.agent.service import Agent
from browser_use.controller.service import Controller


@pytest.fixture
def llm():
	"""Initialize the language model"""
	return ChatOpenAI(model='gpt-4o')  # Use appropriate model


@pytest.fixture
async def controller():
	"""Initialize the controller with self-registered actions"""
	controller = Controller()

	# Define custom actions without Pydantic models
	@controller.action('Print a message')
	def print_message(message: str):
		print(f'Message: {message}')
		return f'Printed message: {message}'

	@controller.action('Add two numbers')
	def add_numbers(a: int, b: int):
		result = a + b
		return f'The sum is {result}'

	@controller.action('Concatenate strings')
	def concatenate_strings(str1: str, str2: str):
		result = str1 + str2
		return f'Concatenated string: {result}'

	# Define Pydantic models
	class SimpleModel(BaseModel):
		name: str
		age: int

	class Address(BaseModel):
		street: str
		city: str

	class NestedModel(BaseModel):
		user: SimpleModel
		address: Address

	# Add actions with Pydantic model arguments
	@controller.action('Process simple model', param_model=SimpleModel)
	def process_simple_model(model: SimpleModel):
		return f'Processed {model.name}, age {model.age}'

	@controller.action('Process nested model', param_model=NestedModel)
	def process_nested_model(model: NestedModel):
		user_info = f'{model.user.name}, age {model.user.age}'
		address_info = f'{model.address.street}, {model.address.city}'
		return f'Processed user {user_info} at address {address_info}'

	@controller.action('Process multiple models')
	def process_multiple_models(model1: SimpleModel, model2: Address):
		return f'Processed {model1.name} living at {model2.street}, {model2.city}'

	try:
		yield controller
	finally:
		if controller.browser:
			await controller.browser.close(force=True)


# @pytest.mark.skip(reason="Skipping test for now")
@pytest.mark.asyncio
async def test_self_registered_actions_no_pydantic(llm, controller):
	"""Test self-registered actions with individual arguments"""
	agent = Agent(
		task="First, print the message 'Hello, World!'. Then, add 10 and 20. Next, concatenate 'foo' and 'bar'.",
		llm=llm,
		controller=controller,
	)
	history = await agent.run(max_steps=10)
	# Check that custom actions were executed
	actions = [h.model_output.action for h in history if h.model_output and h.model_output.action]
	action_names = [list(action.model_dump(exclude_unset=True).keys())[0] for action in actions]

	assert 'print_message' in action_names
	assert 'add_numbers' in action_names
	assert 'concatenate_strings' in action_names


# @pytest.mark.skip(reason="Skipping test for now")
@pytest.mark.asyncio
async def test_mixed_arguments_actions(llm, controller):
	"""Test actions with mixed argument types"""

	# Define another action during the test
	# Test for async actions
	@controller.action('Calculate the area of a rectangle')
	async def calculate_area(length: float, width: float):
		area = length * width
		return f'The area is {area}'

	agent = Agent(
		task='Calculate the area of a rectangle with length 5.5 and width 3.2.',
		llm=llm,
		controller=controller,
	)
	history = await agent.run(max_steps=5)

	# Check that the action was executed
	actions = [h.model_output.action for h in history if h.model_output and h.model_output.action]
	action_names = [list(action.model_dump(exclude_unset=True).keys())[0] for action in actions]

	assert 'calculate_area' in action_names
	# check result
	correct = 'The area is 17.6'
	assert correct in [h.result.extracted_content for h in history if h.model_output]


@pytest.mark.asyncio
async def test_pydantic_simple_model(llm, controller):
	"""Test action with a simple Pydantic model argument"""
	agent = Agent(
		task="Process a simple model with name 'Alice' and age 30.",
		llm=llm,
		controller=controller,
	)
	history = await agent.run(max_steps=5)

	# Check that the action was executed
	actions = [h.model_output.action for h in history if h.model_output and h.model_output.action]
	action_names = [list(action.model_dump(exclude_unset=True).keys())[0] for action in actions]

	assert 'process_simple_model' in action_names
	correct = 'Processed Alice, age 30'
	assert correct in [h.result.extracted_content for h in history if h.model_output]


@pytest.mark.asyncio
async def test_pydantic_nested_model(llm, controller):
	"""Test action with a nested Pydantic model argument"""
	agent = Agent(
		task="Process a nested model with user name 'Bob', age 25, living at '123 Maple St', 'Springfield'.",
		llm=llm,
		controller=controller,
	)
	history = await agent.run(max_steps=5)

	# Check that the action was executed
	actions = [h.model_output.action for h in history if h.model_output and h.model_output.action]
	action_names = [list(action.model_dump(exclude_unset=True).keys())[0] for action in actions]

	assert 'process_nested_model' in action_names
	correct = 'Processed user Bob, age 25 at address 123 Maple St, Springfield'
	assert correct in [h.result.extracted_content for h in history if h.model_output]


@pytest.mark.asyncio
async def test_pydantic_multiple_models(llm, controller):
	"""Test action with multiple Pydantic model arguments"""
	agent = Agent(
		task="Process models with user name 'Carol', age 28, living at '456 Oak Ave', 'Shelbyville'.",
		llm=llm,
		controller=controller,
	)
	history = await agent.run(max_steps=5)

	# Check that the action was executed
	actions = [h.model_output.action for h in history if h.model_output and h.model_output.action]
	action_names = [list(action.model_dump(exclude_unset=True).keys())[0] for action in actions]

	assert 'process_multiple_models' in action_names
	correct = 'Processed Carol living at 456 Oak Ave, Shelbyville'
	assert correct in [h.result.extracted_content for h in history if h.model_output]


# run this file with:
# pytest tests/test_self_registered_actions.py --capture=no
