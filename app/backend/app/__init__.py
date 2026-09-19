"""maxveryMAX backend — API афиши (поиск, фильтры, ранжирование, избранное, клики)."""

import os
import sys

# Обеспечиваем импортируемость `shared/` (корень app/) при запуске из backend/
# локально; в Docker это делает PYTHONPATH=/app.
_APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

__version__ = "0.1.0"
