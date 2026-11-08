"""Initialize Brian2 on the main thread before Streamlit starts its script thread."""

from pathlib import Path
import sys


def main():
    import brian2  # noqa: F401 -- installs Brian2's signal handler on the main thread
    from streamlit.web import cli
    app = Path(__file__).resolve().with_name("app.py")
    sys.argv = ["streamlit", "run", str(app), *sys.argv[1:]]
    return cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
