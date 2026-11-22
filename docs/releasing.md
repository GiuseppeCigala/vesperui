# Releasing

This page describes how to cut a release of VesperUI and publish it to GitHub
and PyPI.

## 1. Prepare the version

The version lives in one place, `vesperui/__init__.py`:

```python
__version__ = "0.1.0"
```

`pyproject.toml` reads it dynamically, so there is nothing else to bump.
VesperUI follows [Semantic Versioning](https://semver.org/): bump the minor
version for new widgets or API additions, the patch version for fixes, and the
major version for breaking changes.

## 2. Update the changelog

Move the unreleased entries in [CHANGELOG.md](../CHANGELOG.md) under a new
version heading with today's date.

## 3. Validate locally

From a clean clone on Windows:

```bash
python -m pip install -e ".[dev]"
python run_tests.py -v
python showcase_common.py --check
python showcase_audio.py --check
```

All tests must pass and both showcases must build without errors before you
tag a release.

## 4. Build and inspect the distributions

```bash
python -m build
python -m twine check dist/*
```

This produces `dist/vesperui-<version>-py3-none-any.whl` and
`dist/vesperui-<version>.tar.gz`. The wheel should contain only the
`vesperui` package; the sdist also contains tests, docs and the showcases.
Confirm the metadata with:

```bash
python -m zipfile -l dist/vesperui-<version>-py3-none-any.whl
```

## 5. Tag and push

```bash
git add .
git commit -m "Release 0.1.0"
git tag v0.1.0
git push origin main
git push origin v0.1.0
```

## 6. Publish to PyPI

The repository ships with `.github/workflows/publish.yml`, which builds the
distributions and uploads them with
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) when a
GitHub release is published. No API token is stored in the repository.

One-time setup:

1. Create the project on PyPI (or configure a pending trusted publisher).
2. In the PyPI project settings, add a trusted publisher with:
   - owner: `GiuseppeCigala`
   - repository: `vesperui`
   - workflow: `publish.yml`
   - environment: `pypi`
3. In the GitHub repository, create an environment named `pypi` (Settings →
   Environments).

Then create a GitHub release from the tag. The workflow builds the artifacts,
runs `twine check`, and publishes them.

For a dry run, configure the same trusted publisher on
[TestPyPI](https://test.pypi.org/) and temporarily point the publish action at
`https://test.pypi.org/legacy/` with `repository-url`.

## 7. Verify the install

In a fresh environment:

```bash
python -m pip install --upgrade vesperui
python -c "import vesperui; print(vesperui.__version__)"
```

## Repository settings checklist

These cannot be created from the source tree, so set them once on GitHub:

- Add a short description: “Native Windows widgets with an evening glow.”
- Add topics such as `python`, `windows`, `gui`, `win32`, `ctypes`,
  `widgets`, `dark-theme`.
- Enable the `main` branch protection rule and require the `Tests` workflow.
- Enable GitHub Discussions if you want a place for questions.
- Replace the placeholder repository slug in `pyproject.toml`, the README
  badges, `CITATION.cff` and the workflows if you publish under a different
  owner or name.

## TestPyPI notes

TestPyPI does not host dependencies. If you install from TestPyPI for a check,
use:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ vesperui
```
