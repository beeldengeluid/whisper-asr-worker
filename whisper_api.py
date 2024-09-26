import logging
from typing import Optional
from uuid import uuid4
from fastapi import BackgroundTasks, FastAPI, HTTPException, status, Response
from asr import run
from enum import Enum
from pydantic import BaseModel
from config import (
    model_base_dir,
    w_device,
    w_model,
)
import faster_whisper
from model_download import check_model_availability

logger = logging.getLogger(__name__)
api = FastAPI()

logger.info(f"Loading model on device {w_device}")
# checking if model needs to be downloaded from HF or not
model_location = model_base_dir if check_model_availability() else w_model
model = faster_whisper.WhisperModel(
    model_location,
    device=w_device,
    compute_type=(  # float16 only works on GPU, float32 or int8 are recommended for CPU
        "float16" if w_device == "cuda" else "float32"
    ),
)
logger.info("Model loaded!")


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

current_task: Optional[Task] = None


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
        task.status = Status.PROCESSING
        update_task(task)
        run(task.input_uri, task.output_uri, model)
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
async def create_task(
    task: Task, background_tasks: BackgroundTasks, response: Response
):
    global current_task
    print(current_task)
    if current_task and current_task.status == "PROCESSING":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"msg": "The worker is currently processing a task. Try again later!"}
    background_tasks.add_task(try_whisper, task)
    task.id = str(uuid4())
    task.status = Status.CREATED
    current_task = task
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
