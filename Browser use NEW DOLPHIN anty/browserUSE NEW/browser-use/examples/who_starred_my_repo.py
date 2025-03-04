import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel
from browser_use import Agent, Controller, DolphinBrowser

# Load environment variables
load_dotenv()

class StarredPeople(BaseModel):
	usernames: List[str]

async def main():
	try:
		# Initialize Mistral AI model
		llm = ChatMistralAI(
			model="pixtral-large-latest",
			mistral_api_key=os.getenv("MISTRAL_API_KEY"),
			temperature=0.1,
		)

		# Initialize controller and browser
		controller = Controller(keep_open=True)
		browser = DolphinBrowser(keep_open=True)
		
		# Connect to Dolphin profile
		profile_id = os.getenv("DOLPHIN_PROFILE_ID")
		await browser.connect(profile_id)
		controller.set_browser(browser)

		# Initialize the browser agent
		agent = Agent(
			task='Find and save the usernames of people who starred my repository on GitHub',
			llm=llm,
			controller=controller,
			use_vision=True,
		)

		result = await agent.run()
		print("Final Result:", result)

	except Exception as e:
		print(f"Error occurred: {str(e)}")
		raise e
	finally:
		if 'browser' in locals():
			await browser.close(force=True)

if __name__ == "__main__":
	asyncio.run(main())
