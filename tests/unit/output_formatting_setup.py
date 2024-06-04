import sys
from mock import Mock


class MockConfig:
    class WHISPER_ASR_SETTINGS:
        WORD_TIMESTAMPS = True


cfg = MockConfig()

module = type(sys)("dane")
module.submodule = type(sys)("config")
module.submodule2 = type(sys)("provenance")
module.submodule.cfg = cfg
module.submodule2.Provenance = None

sys.modules["dane"] = module
sys.modules["dane.config"] = module.submodule
sys.modules["dane.provenance"] = module.submodule2

module2 = type(sys)("io_util")
module2.get_base_output_dir = None
module2.get_output_file_path = None
module2.check_model_availability = None
module2.check_pretrained_model_availability = None

sys.modules["io_util"] = module2
sys.modules["faster_whisper"] = Mock()
