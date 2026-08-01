import asyncio
from typing import cast

from dotenv import load_dotenv

load_dotenv()

from Retrival_Pipline.Graph.graph import app
from Retrival_Pipline.Graph.state import GraphState


async def main() -> None:
    inputs = cast(
        GraphState,
        {"question": "what is sexual memory?", "documents": [], "generation": "", "web_search": False},
    )
    result = await app.ainvoke(inputs)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())


    