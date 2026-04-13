import asyncio
import sys
import logging
from app.core.groq_analyzer import generate_report2

logging.basicConfig(level=logging.DEBUG)

async def main():
    dummy_files = [
        {"path": "/src/index.js", "content": "console.log('test');"}
    ]
    dummy_classification = {
        "project_type": "Node.js",
        "languages": ["javascript"],
        "frameworks": ["react"]
    }
    print("Running Groq Generator...")
    res = await generate_report2(dummy_files, dummy_classification)
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
