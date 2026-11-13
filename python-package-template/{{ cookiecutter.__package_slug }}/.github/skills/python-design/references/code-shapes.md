# Code shapes: functions, classes, interfaces, patterns

Read this before adding a class, an interface, a named pattern or any
metaprogramming. Default remains: small functions and frozen dataclasses.

## 1. When a class is justified
Add a class only when one of these is observed, and name the trigger:

| Observed | Shape |
|---|---|
| Data with rules that must always hold | dataclass that validates in `__post_init__`, with methods for its rules |
| The same 3+ values passed through several functions | one object holding them, built once |
| A test needs `monkeypatch` or `mock.patch` to replace I/O | pass the dependency in as a parameter typed by a `Protocol`; the test passes a fake |
| A second implementation of the same job appears | `Protocol`, one class per implementation |
| `if kind == ...` on the same field in 2+ places | one class per kind behind a `Protocol` |
| Something opened must be closed | context manager |

Composition over inheritance; inherit only to implement an interface. A class
with only `__init__` and one method is a function.

## 2. Which kind of type

| Need | Use | Not |
|---|---|---|
| One behavior passed in (a single method) | a plain function parameter typed with `Callable` | a one-method class or interface |
| Several methods a caller depends on, implementations unrelated | `Protocol`, defined next to the code that uses it | `ABC` |
| Implementations share real code, with a few steps that vary | `ABC`: shared code in the base, `@abstractmethod` for the varying steps | copying the shared code into each class |
| A missing method must fail when the object is created, not when it is called | `ABC` | `Protocol` |
| A fixed, closed set of choices | `Enum` or `Literal` | subclasses |
| The shape of JSON passed straight to or from `json` | `TypedDict` | a class |
| Data that crosses module boundaries | frozen `dataclass` | a bare `dict` or tuple |

- No interface of either kind until there is a second implementation or a
  test needs a fake.
- A `Protocol` belongs to its consumer. An implementation does not inherit
  from it.
- Do not use `@runtime_checkable` with `isinstance` as validation: it checks
  that methods exist, not their signatures.

## 3. Data and behaviour (parameter objects)
A class that does work takes its data as one object, not as a long list of
arguments. The data object holds and checks values; the class trusts it.

- **Trigger:** 3 or more related values passed to `__init__`, or the same
  values travelling together through several calls. With one or two values,
  keep plain arguments.
- **Collaborators stay separate:** a client, rate source or repository the
  class *uses* is its own `__init__` parameter, never a field of the data
  object.
- **No I/O in data objects:** small derived properties are fine; reading
  files or calling networks is not.

| The data | Use |
|---|---|
| Comes from outside: file, JSON, env vars, CLI, HTTP | Pydantic `BaseModel` with `ConfigDict(frozen=True, extra="forbid")`, in the outside-world or settings sub-package |
| Built by your own code, already typed | `@dataclass(frozen=True, slots=True)` |
| Has a rule types cannot express (`start <= end`) | the dataclass checks it in `__post_init__` |
| Holds arrays, data frames, tensors or callables | dataclass with `eq=False` (generated `__eq__`/`__hash__` fail on arrays) |
| Is created thousands of times in a loop | dataclass (Pydantic validates on every creation) |

Subject logic does not import Pydantic: the edge validates and converts to a
dataclass once. Enforce it like an SDK (`references/boundaries.md`, section 2).

```python
@dataclass(frozen=True, slots=True)
class ReportSettings:  # data: checked once
    month: YearMonth
    base_currency: str

    def __post_init__(self) -> None:
        if len(self.base_currency) != 3:
            raise ValueError(f"currency must be 3 letters: {self.base_currency!r}")


class ReportBuilder:  # behaviour: trusts the data
    def __init__(self, settings: ReportSettings, rates: RateSource) -> None:
        self._settings, self._rates = settings, rates
```

Do not:
- check data inside the behaviour class (`if settings.x <= 0: raise ...`);
  the check belongs to the data object;
- leave a data object mutable; `frozen` stops reassigning fields, not
  changing a list or array inside one;
- wrap one or two arguments in a data object just to follow this section.

## 4. Patterns
A named pattern needs a visible problem. State the problem, the pattern and the
simpler option you rejected. Wait for the third duplicate before abstracting.
Remove a pattern that did not make the code easier to change.

| Pattern | Python form |
|---|---|
| Strategy | a callable parameter |
| Factory | a dict of callables, or a `classmethod` constructor |
| Decorator | a function using `functools.wraps` |
| Adapter, Repository | a class implementing a `Protocol` |
| Template method | a function that takes the varying steps as callables; an `ABC` only when variants share real state |
| State | `Enum` with `match`; one class per state only when each state carries behavior |
| Observer | a list of callbacks |

## 5. Metaprogramming
Off by default. The type checker and a text search must both be able to find
where a name is defined.

- **Allowed without asking:** `dataclass`, `functools` helpers, simple
  decorators with `functools.wraps`, context managers, `Enum`.
- **Allowed with a stated reason:** `__init_subclass__` for a plugin
  registry; a descriptor for a validated field reused in 3 or more places.
- **Not without the owner's approval:** metaclasses; `__getattr__` or
  `setattr` to create attributes dynamically; `exec` and `eval`; import
  hooks; building classes with `type(...)`; patching objects at runtime
  outside tests.

Whatever is used needs its own test.
