
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    import pytest_asyncio
    pytest_plugins = ('pytest_asyncio',)
except ImportError:
    pass

mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
mock_pymongo.errors.ConnectionFailure = Exception
mock_pymongo.errors.DuplicateKeyError = Exception
mock_pymongo.MongoClient = MagicMock()
mock_pymongo.ASCENDING = 1

mock_google = MagicMock()
mock_google.genai = MagicMock()
mock_google.genai.Client = MagicMock()
mock_google.genai.types = MagicMock()
mock_google.genai.types.GenerateContentConfig = MagicMock()
mock_google.genai.errors = MagicMock()
mock_google.genai.errors.ClientError = Exception

mock_aiogram = MagicMock()
mock_aiogram.F = MagicMock()
mock_aiogram.types = MagicMock()
mock_aiogram.types.Message = MagicMock
mock_aiogram.types.User = MagicMock
mock_aiogram.types.CallbackQuery = MagicMock
mock_aiogram.types.InlineKeyboardMarkup = MagicMock
mock_aiogram.types.InlineKeyboardButton = MagicMock
mock_aiogram.fsm = MagicMock()
mock_aiogram.fsm.context = MagicMock()
mock_aiogram.fsm.context.FSMContext = MagicMock

import sys as sys_module
if 'pymongo' not in sys_module.modules:
    sys_module.modules['pymongo'] = mock_pymongo
    sys_module.modules['pymongo.errors'] = mock_pymongo.errors

if 'google' not in sys_module.modules:
    sys_module.modules['google'] = mock_google
    sys_module.modules['google.genai'] = mock_google.genai
    sys_module.modules['google.genai.errors'] = mock_google.genai.errors

if 'aiogram' not in sys_module.modules:
    sys_module.modules['aiogram'] = mock_aiogram
    sys_module.modules['aiogram.types'] = mock_aiogram.types
    sys_module.modules['aiogram.fsm'] = mock_aiogram.fsm
    sys_module.modules['aiogram.fsm.context'] = mock_aiogram.fsm.context

