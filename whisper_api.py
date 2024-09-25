import logging
from uuid import uuid4
from fastapi import BackgroundTasks, FastAPI
from asr import run

# from typing import Optional
from pydantic import BaseModel
from base_util import LOG_FORMAT

logger = logging.getLogger(__name__)
api = FastAPI()


class Task(BaseModel):
    input_uri: str
    output_uri: str
    id: str | None = None


all_tasks = []


def try_whisper(task: Task):
    logger.info(f"Trying to call Whisper for task {task.id}")
    try:
        run(task.input_uri, task.output_uri)
    except Exception:
        logger.exception("Failed to run whisper")
    logger.info(f"Successfully ran Whisper for task {task.id}")


@api.post("/tasks")
async def create_task(task: Task, background_tasks: BackgroundTasks):
    background_tasks.add_task(try_whisper, task)
    task.id = str(uuid4())
    task_dict = task.dict()
    all_tasks.append(task_dict)
    return {"data": task_dict, "msg": "Successfully added task", "task_id": task.id}


if __name__ == "__main__":
    import sys
    import uvicorn

    logging.basicConfig(
        stream=sys.stdout,
        level="INFO",
        format=LOG_FORMAT,
    )
    uvicorn.run(api, port=8081, host="0.0.0.0")
