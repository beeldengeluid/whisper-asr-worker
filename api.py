import logging
from typing import Optional
from uuid import uuid4
from fastapi import BackgroundTasks, FastAPI, HTTPException, status, Response
import asyncio
from contextlib import asynccontextmanager
from asr import run
from whisper import load_model
from enum import Enum
from pydantic import BaseModel
from config import (
    MODEL_BASE_DIR,
    W_DEVICE,
    W_MODEL,
)

logger = logging.getLogger(__name__)
shutdown_current_task_done = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the Whisper model
    global model
    logger.info(f"Loading model on device {W_DEVICE}")
    model = load_model(MODEL_BASE_DIR, W_MODEL, W_DEVICE)
    # Run the API
    yield
    # Shutdown call
    global current_task
    # If there is a task still being processed at shutdown time
    if current_task and current_task.status == Status.PROCESSING:
        global shutdown_current_task_done
        shutdown_current_task_done = False
        # Wait until the task is complete
        while not shutdown_current_task_done:
            await asyncio.sleep(0.1)
    # Clean up
    logger.info("Current task is done. Shutting down...")
    del model

api = FastAPI(lifespan=lifespan)


class Status(Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"


StatusToHTTP = {
    Status.CREATED: status.HTTP_201_CREATED,
    Status.PROCESSING: status.HTTP_202_ACCEPTED,
    Status.DONE: status.HTTP_200_OK,
    Status.ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


class Task(BaseModel):
    input_uri: str
    output_uri: str = ""
    status: Status = Status.CREATED
    id: str | None = None
    error_msg: str | None = None
    response: dict | None = None


all_tasks: dict[str, Task] = {}

current_task: Optional[Task] = None


def delete_task(task_id):
    try:
        del all_tasks[task_id]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )


def update_task(task: Task):
    if not task or not task.id:
        raise Exception("Tried to update task without task or ID")
    all_tasks[task.id] = task


def try_whisper(task: Task):
    logger.info(f"Trying to call Whisper for task {task.id}")

    try:
        task.status = Status.PROCESSING
        update_task(task)
        outputs = run(task.input_uri, task.output_uri, model)
        if outputs:
            task.status = Status.DONE
            task.response = outputs
            logger.info(f"Successfully transcribed task {task.id}")
    except Exception as e:
        logger.error("Failed to run Whisper")
        logger.exception(e)
        task.status = Status.ERROR
        task.error_msg = str(e)
    update_task(task)
    logger.info(f"Task {task.id} has been updated")
    # In case the application is shutting down
    global shutdown_current_task_done
    shutdown_current_task_done = True


@api.get("/tasks")
def get_all_tasks():
    return {"data": all_tasks}


@api.get("/status")
def get_status(response: Response):
    global current_task

    if current_task and current_task.status == Status.PROCESSING:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"msg": "The worker is currently processing a task. Try again later!"}

    response.status_code = status.HTTP_200_OK
    return {"msg": "The worker is available!"}


@api.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: Task, background_tasks: BackgroundTasks, response: Response
):
    global current_task
    if current_task and current_task.status == Status.PROCESSING:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"msg": "The worker is currently processing a task. Try again later!"}
    background_tasks.add_task(try_whisper, task)
    task.id = str(uuid4())
    task.status = Status.CREATED
    current_task = task
    task_dict = task.dict()
    all_tasks["task_id"] = task
    return {"data": task_dict, "msg": "Successfully added task", "task_id": task.id}


@api.get("/tasks/{task_id}")
async def get_task(task_id: str, response: Response):
    try:
        task = all_tasks[task_id]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
    response.status_code = StatusToHTTP[task.status]
    return {"data": task}


@api.delete("/tasks/{task_id}")
async def remove_task(task_id: str):
    try:
        delete_task(task_id)
        return {
            "msg": f"Successfully deleted task {task_id}",
            "task_id": task_id,
        }
    except HTTPException as e:
        logger.error(e)
        return {
            "msg": f"Failed to delete task {task_id}",
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
