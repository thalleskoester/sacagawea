# Packaging Contract - V1

The project must remain a `uv` Python project and use the existing setuptools backend family already referenced by `pyproject.toml`.

The package layout is:

```text
src/
  sacagawea/
    __init__.py
```

Package discovery must use setuptools `src` layout discovery:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

The old empty package declarations must not remain active:

```toml
[tool.setuptools]
packages = []
py-modules = []
```

The package name remains `sacagawea`. The package root exports are defined in `public-api.md`.

The project metadata references `README.md`, so Phase 00001 must add a minimal README before packaging checks run.
