import logging
from uuid import uuid4
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from asr import run
from enum import Enum
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)
api = FastAPI()


class Status(Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"


class Task(BaseModel):
    input_uri: str
    output_uri: str
    status: Status = Status.CREATED
    id: str | None = None


all_tasks = [
    {
        "input_uri": "http://modelhosting.beng.nl/whisper-asr.mp3",
        "output_uri": "http://modelhosting.beng.nl/assets/whisper-asr",
        "id": "test1",
    }
]


def get_task_by_id(task_id: str) -> Optional[dict]:
    tasks_with_id = list(filter(lambda t: t.get("id", "") == task_id, all_tasks))
    return tasks_with_id[0] if tasks_with_id else None


def get_task_index(task_id: str) -> int:
    for index, task in enumerate(all_tasks):
        if task.get("id", "") == task_id:
            return index
    return -1


def delete_task(task_id) -> bool:
    task_index = get_task_index(task_id)
    if task_index == -1:
        return False
    del all_tasks[task_index]
    return True


def update_task(task: Task) -> bool:
    if not task or not task.id:
        logger.warning("Tried to update task without ID")
        return False
    task_index = get_task_index(task.id)
    if task_index == -1:
        return False
    all_tasks[task_index] = task.dict()
    return True


def try_whisper(task: Task):
    logger.info(f"Trying to call Whisper for task {task.id}")
    try:
        run(task.input_uri, task.output_uri)
        task.status = Status.DONE
    except Exception:
        logger.exception("Failed to run whisper")
        task.status = Status.ERROR
    update_task(task)
    logger.info(f"Done running Whisper for task {task.id}")


@api.get("/tasks")
def get_all_tasks():
    return {"data": all_tasks}


@api.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(task: Task, background_tasks: BackgroundTasks):
    background_tasks.add_task(try_whisper, task)
    task.id = str(uuid4())
    task_dict = task.dict()
    all_tasks.append(task_dict)
    return {"data": task_dict, "msg": "Successfully added task", "task_id": task.id}


@api.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
    return {"data": task}


@api.delete("/tasks/{task_id}")
async def remove_task(task_id: str):
    success = delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
    return {
        "msg": (
            f"Successfully deleted task {task_id}"
            if success
            else f"Failed to delete task {task_id}"
        ),
        "task_id": task_id,
    }


@api.get("/ping")
async def ping():
    return "pong"


if __name__ == "__main__":
    import sys
    import uvicorn
    from argparse import ArgumentParser
    from base_util import LOG_FORMAT

    # first read the CLI arguments
    parser = ArgumentParser(description="whisper-api")
    parser.add_argument("--port", action="store", dest="port", default="5333")
    parser.add_argument("--log", action="store", dest="loglevel", default="INFO")
    args = parser.parse_args()

    # initialises the root logger
    logging.basicConfig(
        stream=sys.stdout,  # configure a stream handler only for now (single handler)
        format=LOG_FORMAT,
    )

    # setting the loglevel
    log_level = args.loglevel.upper()
    logger.setLevel(log_level)
    logger.info(f"Logger initialized (log level: {log_level})")
    logger.info(f"Got the following CMD line arguments: {args}")

    port = 5333
    try:
        port = int(args.port)
    except ValueError:
        logger.error(
            f"--port must be a valid integer, starting with default port {port}"
        )

    uvicorn.run(api, port=port, host="0.0.0.0")