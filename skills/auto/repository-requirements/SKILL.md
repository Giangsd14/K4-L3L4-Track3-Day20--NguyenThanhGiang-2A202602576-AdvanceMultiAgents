---
name: repository-requirements
description: Use when changing code in an existing repository with explicit quality, testing, or documentation requirements.
---
- Read every acceptance rule before editing and turn it into a checklist.
- Inspect the affected modules, public APIs, and existing test and changelog conventions.
- Add parameter and return type annotations to every public function you touch; check whether repository rules require them across the package.
- Write a regression test for each distinct bug fixed, following the project’s test conventions.
- Record every required fix in the specified changelog section and format.
- Run the relevant tests and the full required checks after editing; passing existing tests alone does not verify new requirements.
- Recheck each acceptance rule against the final files before finishing.