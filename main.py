from dotenv import load_dotenv

load_dotenv()
import asyncio
from Retrival_Pipline.Graph.graph import app

async def main():
    inputs = {"question": "what is sexual  memory?"}
    result = await app.ainvoke(input=inputs)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())