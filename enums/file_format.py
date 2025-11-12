from enum import Enum
import inspect
import enums.file as file_pkg

_file_members = {}

for attr_name in dir(file_pkg):
    try:
        attr = getattr(file_pkg, attr_name)
    except Exception:
        continue
    if inspect.isclass(attr) and issubclass(attr, Enum) and attr is not Enum:
        for m in attr:
            _file_members[m.name] = m.value

FileFormat = Enum('FileFormat', _file_members)