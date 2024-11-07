import py3nvml.py3nvml as nvml
import time
from threading import Thread
from typing import Tuple
import gc


class MyThread(Thread):
    def __init__(self, func, params):
        super(MyThread, self).__init__()
        self.func = func
        self.params = params
        self.result = None

    def run(self):
        self.result = self.func(*self.params)

    def get_result(self):
        return self.result


class GpuMemoryMeasure:
    def __init__(self):
        nvml.nvmlInit()
        self.handle = nvml.nvmlDeviceGetHandleByIndex(0)
        self.gpu_memory_limit = nvml.nvmlDeviceGetMemoryInfo(self.handle).total >> 20

        self.gpu_mem_usage = []

    def start_measure_gpu_mem(self):
        def _get_mem_usage():
            while True:
                self.gpu_mem_usage.append(
                    nvml.nvmlDeviceGetMemoryInfo(self.handle).used >> 20
                )
                time.sleep(0.5)

                if self.stop:
                    break

            return self.gpu_mem_usage

        self.stop = False
        self.thread = MyThread(_get_mem_usage, params=())
        self.thread.start()

    def stop_measure_gpu_mem(self) -> Tuple[float, float]:
        self.stop = True
        self.thread.join()
        max_memory_usage = max(self.gpu_mem_usage)

        return max_memory_usage, self.gpu_memory_limit

    def __del__(self):
        nvml.nvmlShutdown()
        gc.collect()
