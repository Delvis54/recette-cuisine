import os
import sys

# Kivy must be configured before it is imported by any test module. Widget tests
# need a real window provider (run them under xvfb); tests that only exercise the
# non-graphical helpers skip themselves when no window can be created.
os.environ.setdefault("KIVY_AUDIO", "mock")
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_FILELOG", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
