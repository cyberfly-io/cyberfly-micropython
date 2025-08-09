class DeviceModule:
    """Abstract base for sensors/actuators.

    Contract:
    - id: unique string ID to address the module (e.g., "led", "temp1")
    - read() -> value or dict with current state/data
    - execute(cmd: str, params: dict|None) -> result dict or value
    """

    def __init__(self, module_id):
        self.id = module_id

    def read(self):
        return None

    def execute(self, cmd, params=None):
        raise NotImplementedError("execute not implemented")
