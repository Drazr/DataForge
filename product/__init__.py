"""DataForge product foundation; independent of experimental workflows."""

# The bundled desktop Python does not install the Microsoft runtime globally.
# Add only its sibling runtime directory, or an explicitly configured directory.
import os
import sys
from pathlib import Path

_dll_handle = None
if sys.platform == 'win32':
    _directory = Path(os.getenv('DATAFORGE_DLL_DIRECTORY') or
                      Path(sys.base_prefix).parent / 'native' / 'libheif' / 'libheif' / 'bin')
    if (_directory / 'msvcp140.dll').is_file():
        _dll_handle = os.add_dll_directory(str(_directory))
