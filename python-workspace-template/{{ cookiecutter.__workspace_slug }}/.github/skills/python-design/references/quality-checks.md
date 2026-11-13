# Quality checks

Use these checks; do not use the words as goals.
- **Modular:** the import contract passes and has no cycles.
- **Reusable:** subject logic imports no file, network or SDK code, and its
  tests need no patching.
- **Maintainable:** a typical change touches few files; functions stay under
  the linter's size limits.
- **Efficient:** only where the owner set a budget; then a timed test on a
  fixed input.
- **Production-ready:** all gates pass, the built package installs and its
  entry point runs, external calls have timeouts, no `print` in library code.
