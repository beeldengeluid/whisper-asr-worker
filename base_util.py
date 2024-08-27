import logging
import ntpath
import os
import subprocess
from typing import Tuple
from config import output_base_dir


LOG_FORMAT = "%(asctime)s|%(levelname)s|%(process)d|%(module)s|%(funcName)s|%(lineno)d|%(message)s"
logger = logging.getLogger(__name__)


# the file name without extension is used as asset ID
def get_asset_info(input_file: str) -> Tuple[str, str]:
    file_name = ntpath.basename(input_file)
    asset_id, extension = os.path.splitext(file_name)
    logger.info(f"working with this asset ID {asset_id}")
    return asset_id, extension


# i.e. {output_base_dir}/output/{input_filename_without_extension}
def asr_output_dir(input_path):
    return os.path.join(output_base_dir, "output", get_asset_info(input_path)[0])


# used by asr.py and transcode.py
def run_shell_command(cmd: str) -> bool:
    logger.info(cmd)
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,  # needed to support file glob
        )

        stdout, stderr = process.communicate()
        logger.info(stdout)
        logger.error(stderr)
        logger.info(f"Process is done: return code {process.returncode}")
        return process.returncode == 0
    except subprocess.CalledProcessError:
        logger.exception("CalledProcessError")
        return False
    except Exception:
        logger.exception("Exception")
        return False
