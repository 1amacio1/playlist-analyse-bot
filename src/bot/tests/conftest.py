"""Конфигурация для тестов бота"""
import pytest
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Настройка тестового окружения"""
    # Здесь можно добавить общую настройку для всех тестов
    yield
    # Очистка после тестов

