import os
import sys


def test_readme_exists():
    assert os.path.exists("README.md"), "README.md must exist"


def test_env_example_exists():
    assert os.path.exists(".env.example"), ".env.example must exist"


def test_main_exists():
    assert os.path.exists("main.py"), "main.py must exist"


def test_python_version():
    major = sys.version_info.major
    minor = sys.version_info.minor
    assert (major == 3 and minor >= 8) or (major > 3), "Python >= 3.8 required in CI"
