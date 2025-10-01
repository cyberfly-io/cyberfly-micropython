import os
try:
    # When imported as a package (recommended)
    from .module_base import DeviceModule
except Exception:
    # Fallback for flat copy into modules/ without package context
    from module_base import DeviceModule  # type: ignore


class ModuleRegistry:
    def __init__(self):
        self._mods = {}

    def add(self, *mods):
        for m in mods:
            self._mods[m.id] = m
        return self

    def get(self, module_id):
        return self._mods.get(module_id)

    def all(self):
        return list(self._mods.values())

    # Convenience helpers
    def read(self, module_id):
        m = self.get(module_id)
        return None if not m else m.read()

    def execute(self, module_id, cmd, params=None):
        m = self.get(module_id)
        if not m:
            return {"error": "module_not_found", "id": module_id}
        try:
            return m.execute(cmd, params or {})
        except Exception as e:
            return {"error": "exec_failed", "message": str(e)}

    def register_all(self, packages=("actuators", "sensors")):
        """Auto-discover and register modules from given packages.

        Each module file may either:
        - define a MODULES list of instantiated DeviceModule objects, or
        - expose one or more DeviceModule subclasses with zero-arg constructors.
        """
        for pkg in packages:
            try:
                files = os.listdir(pkg)
            except Exception:
                continue
            for fname in files:
                if not fname.endswith('.py') or fname == '__init__.py':
                    continue
                modname = fname[:-3]
                fqmn = pkg + '.' + modname
                try:
                    try:
                        # Prefer relative import within package
                        top = __import__(__package__ + '.' + fqmn) if __package__ else __import__(fqmn)
                    except Exception:
                        top = __import__(fqmn)
                    comp = fqmn.split('.')
                    mod = top
                    for c in comp[1:]:
                        mod = getattr(mod, c)
                    # Prefer explicit MODULES list
                    if hasattr(mod, 'MODULES'):
                        for m in getattr(mod, 'MODULES') or []:
                            if isinstance(m, DeviceModule):
                                self.add(m)
                        continue
                    # Otherwise, instantiate zero-arg DeviceModule subclasses
                    for attr_name in dir(mod):
                        try:
                            attr = getattr(mod, attr_name)
                            # Check for class-like and subclass of DeviceModule
                            if isinstance(attr, type) and issubclass(attr, DeviceModule) and attr is not DeviceModule:
                                try:
                                    inst = attr()
                                    if isinstance(inst, DeviceModule) and getattr(inst, 'id', None):
                                        self.add(inst)
                                except Exception:
                                    # constructor needs args; skip
                                    pass
                        except Exception:
                            pass
                except Exception:
                    # Failed to import; skip
                    continue
