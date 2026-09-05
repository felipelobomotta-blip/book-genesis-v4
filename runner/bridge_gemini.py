"""Compatibility name for the Gemini adapter.

The old bridge hard-coded a developer-local executable and placed the full prompt
on argv.  Keep the configuration name stable while delegating to the portable
Antigravity bridge, which streams one NDJSON prompt event on stdin.
"""

from runner.bridge_antigravity import main


if __name__ == "__main__":
    main()
