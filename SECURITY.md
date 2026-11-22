# Security policy

## Supported versions

VesperUI is pre-1.0. Security fixes are applied to the latest release and to
the `main` branch.

| Version | Supported |
| --- | --- |
| 0.1.x | Yes |
| < 0.1 | No |

## Reporting a vulnerability

Please report security issues privately through GitHub Security Advisories:

https://github.com/GiuseppeCigala/vesperui/security/advisories/new

Do not open a public issue for a vulnerability. Include:

- A description of the issue and its potential impact.
- Steps to reproduce, or a minimal proof of concept.
- Affected Windows and Python versions.
- Any suggested mitigation.

You can expect an acknowledgement within a few days and a status update after
the report has been reviewed. Please allow time for a fix and a coordinated
release before disclosing the issue publicly.

## Scope

VesperUI calls Win32 APIs directly through `ctypes`. Relevant classes of
issues include:

- Memory-safety problems in ctypes structure or buffer handling.
- Unsafe file or path handling in the dialog helpers.
- Incorrect ownership or lifetime management of GDI or User32 handles.
- Crashes triggered by untrusted input passed to a widget.

Issues in Windows itself, in Python's `ctypes`, or in third-party software
should be reported to the respective maintainers instead.

## Safe usage notes

- VesperUI is a desktop UI library and is not a security boundary.
- Do not pass untrusted data to dialogs or file APIs without validating it in
  your application.
- Applications that load plugins or remote content should apply their own
  sandboxing and validation.
