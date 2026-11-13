# Boundaries: input, SDKs, errors, public surface

Read this before adding an exception class, an SDK import or a sub-package
`__init__.py`. Names below (`orders`, `storage`, `acme_sdk`) are examples.

## 1. Parse input once
Raw data becomes a typed object in the outside-world sub-package that reads
it. Everything inward takes the typed object.

```python
# storage/orders_file.py  (outside world)
def read_orders(path: Path) -> list[Order]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [Order(id=row["id"], total=Decimal(row["total"])) for row in rows]
```

A missing or malformed field fails here, with the file and row in the message,
not three calls later.

## 2. One home per SDK
Import a third-party SDK in one outside-world sub-package only. Add a contract
to `pyproject.toml` so the rule is enforced:

```toml
[tool.importlinter]
root_package = "<package>"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Only <package>.storage imports acme_sdk"
type = "forbidden"
source_modules = ["<package>.orders", "<package>.cli"]  # every sub-package except its home
forbidden_modules = ["acme_sdk"]
allow_indirect_imports = true  # the entry may import storage, which imports the SDK
```

Without `allow_indirect_imports`, the contract also fails for any sub-package
that imports the SDK's home. When a new sub-package is added, add it to
`source_modules`.

Pydantic gets the same kind of contract, with the subject-logic sub-packages
as `source_modules` and `forbidden_modules = ["pydantic"]`: models live in the
outside world and settings, and are converted to dataclasses there
(`references/code-shapes.md`, section 3).

## 3. Errors
```python
# errors.py, or the package __init__.py
class PackageError(Exception):
    """Base class for every error this package raises on purpose."""


class OrderNotFoundError(PackageError): ...
```

- Subject logic raises the package's own errors, with the values needed to
  understand the failure in the message.
- Outside-world code translates, keeping the cause:

  ```python
  try:
      blob = client.download(name)
  except acme_sdk.NotFound as exc:
      raise OrderNotFoundError(name) from exc
  ```

- Use cases let errors pass through unless they can do something specific
  about them.
- The entry is the only place that catches `PackageError` broadly, to report
  the failure and set the exit code.
- Do not write `except Exception:` to log and carry on, return `None` to
  signal failure, or use an error to steer normal control flow.

## 4. Public surface
```python
# storage/__init__.py
"""Reading and writing orders on disk."""

from ._orders_file import read_orders, write_orders

__all__ = ["read_orders", "write_orders"]
```

- Other sub-packages write `from <package>.storage import read_orders`, never
  `from <package>.storage._orders_file import ...`.
- `__init__.py` holds re-exports only, no logic.
- Moving or renaming an internal module then changes one `__init__.py`, not
  every caller.
