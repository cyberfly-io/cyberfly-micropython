try:
    from ..platform_compat import Pin
except ImportError:
    try:
        from platform_compat import Pin
    except ImportError:
        try:
            import machine
            Pin = machine.Pin
        except ImportError:
            Pin = None

try:
    from ..module_base import DeviceModule
except Exception:
    from module_base import DeviceModule  # fallback when not used as a package


class LedModule(DeviceModule):
    def __init__(self, module_id="led", pin=2, active_high=True):
        super().__init__(module_id)
        self.pin_no = pin
        self.active_high = active_high
        self._pin = Pin(pin, Pin.OUT) if Pin else None

    def _set_state(self, on: bool):
        if not self._pin:
            return
        val = 1 if on else 0
        if not self.active_high:
            val ^= 1
        self._pin.value(val)

    def read(self):
        if not self._pin:
            return {"on": False}
        val = self._pin.value()
        on = bool(val if self.active_high else (val ^ 1))
        return {"on": on}

    def execute(self, cmd, params=None):
        params = params or {}
        cmd = (cmd or "").lower()
        if cmd == "on":
            self._set_state(True)
            return self.read()
        if cmd == "off":
            self._set_state(False)
            return self.read()
        if cmd == "toggle":
            cur = self.read().get("on", False)
            self._set_state(not cur)
            return self.read()
        return {"error": "unknown_cmd", "cmd": cmd}
