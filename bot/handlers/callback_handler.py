import logging
from typing import Dict
from aiogram import F
from aiogram.types import CallbackQuery

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.utils.concert_utils import get_concert_date

from bot.utils import (
    remove_duplicate_concerts,
    filter_by_city,
    group_by_artist,
    extract_date_sort_key,
    format_concert_message,
    create_city_selection_keyboard,
    create_concert_keyboard
)

logger = logging.getLogger(__name__)

PAGE_SIZE = 10


def _check_user_results(user_id, user_results):
    if user_id not in user_results:
        return False
    return True


def _apply_sorting(concerts, sort_by):
    if sort_by == 'artist':
        grouped = group_by_artist(concerts)
        sorted_concerts = []
        for artist in sorted(grouped.keys()):
            sorted_concerts.extend(grouped[artist])
        return remove_duplicate_concerts(sorted_concerts)
    elif sort_by == 'date':
        sorted_concerts = sorted(concerts, 
                               key=lambda x: extract_date_sort_key(
                                   get_concert_date(x) or ''
                               ))
        return remove_duplicate_concerts(sorted_concerts)
    return concerts


async def _update_concert_message(callback, results):
    concerts = results['concerts']
    page_size = PAGE_SIZE
    start_idx = results['current_page'] * page_size
    concert_text = format_concert_message(concerts, start_idx, page_size, results['sort_by'])
    keyboard = create_concert_keyboard(
        concerts,
        results['current_page'],
        page_size,
        results['city_filter'],
        results['sort_by'],
        results.get('available_cities', [])
    )
    await callback.message.edit_text(
        f"✅ Готово! Вот список концертов по вашим интересам:\n\n{concert_text}",
        reply_markup=keyboard
    )
    await callback.answer()


async def handle_city_selection(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    if not _check_user_results(user_id, user_results):
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    callback_data = callback.data
    results = user_results[user_id]
    
    if callback_data == "city_select":
        available_cities = results.get('available_cities', [])
        if available_cities:
            await callback.message.edit_text(
                "📍 Выберите город для просмотра концертов:",
                reply_markup=create_city_selection_keyboard(available_cities)
            )
        await callback.answer()
        return
    
    if callback_data == "city_all":
        results['concerts'] = results['original_concerts'].copy()
        results['city_filter'] = None
        results['current_page'] = 0
        results['concerts'] = _apply_sorting(results['concerts'], results['sort_by'])
        await _update_concert_message(callback, results)
        return
    
    if callback_data == "city_change":
        available_cities = results.get('available_cities', [])
        if available_cities:
            await callback.message.edit_text(
                "📍 Выберите город для просмотра концертов:",
                reply_markup=create_city_selection_keyboard(available_cities)
            )
        await callback.answer()
        return
    
    city_name = callback_data.replace("city_", "")
    filtered = filter_by_city(results['original_concerts'], city_name)
    results['concerts'] = _apply_sorting(filtered, results['sort_by'])
    results['city_filter'] = city_name
    results['current_page'] = 0
    await _update_concert_message(callback, results)


async def handle_sort(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    if not _check_user_results(user_id, user_results):
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    sort_type = callback.data.split("_")[1]
    results = user_results[user_id]
    results['concerts'] = _apply_sorting(results['concerts'].copy(), sort_type)
    results['sort_by'] = sort_type
    results['current_page'] = 0
    await _update_concert_message(callback, results)


async def handle_pagination(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    if not _check_user_results(user_id, user_results):
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    results = user_results[user_id]
    results['current_page'] = int(callback.data.split("_")[1])
    await _update_concert_message(callback, results)


async def handle_recommendations(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    if not _check_user_results(user_id, user_results):
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    results = user_results[user_id]
    artists = results.get('artists', [])
    if not artists:
        await callback.answer("Нет артистов для рекомендаций", show_alert=True)
        return
    
    await callback.answer("🤖 Анализирую ваши музыкальные предпочтения...")
    
    city_map = {
        'Москва': 'moscow', 'Санкт-Петербург': 'saint-petersburg',
        'Екатеринбург': 'yekaterinburg', 'Новосибирск': 'novosibirsk',
        'Казань': 'kazan', 'Нижний Новгород': 'nizhny-novgorod',
        'Челябинск': 'chelyabinsk', 'Самара': 'samara', 'Оренбург': 'orenburg'
    }
    city_code = city_map.get(results.get('city_filter'), '') if results.get('city_filter') else ''
    
    repository = None
    try:
        from src.services.recommendation_service import RecommendationService
        from src.repositories.concert_repository import ConcertRepository
        
        repository = ConcertRepository()
        recommendation_service = RecommendationService(repository, city=city_code)
        
        if not recommendation_service.enabled:
            await callback.answer("⚠️ Рекомендации отключены. Установите GEMINI_API_KEY в .env", show_alert=True)
            return
        
        recommended_concerts = recommendation_service.get_recommendations(artists, max_recommendations=10)
        if not recommended_concerts:
            await callback.answer("😔 Не удалось найти рекомендации. Попробуйте позже.", show_alert=True)
            return
        
        from bot.utils import format_concert_message, create_concert_keyboard
        
        recommended_concerts_with_marker = [
            {**c.copy(), 'is_recommended': True} for c in recommended_concerts
        ]
        
        concert_text = format_concert_message(recommended_concerts_with_marker, 0, PAGE_SIZE, 'date')
        keyboard = create_concert_keyboard(
            recommended_concerts_with_marker, 0, PAGE_SIZE,
            results.get('city_filter'), 'date', results.get('available_cities', [])
        )
        
        await callback.message.answer(
            f"✨ РЕКОМЕНДОВАНО ВАМ\n\nНа основе анализа ваших музыкальных предпочтений:\n\n{concert_text}",
            reply_markup=keyboard
        )
        results['recommended_concerts'] = recommended_concerts_with_marker
        await callback.answer("✨ Рекомендации отправлены отдельным сообщением")
        
    except Exception as e:
        logger.error(f"Ошибка при получении рекомендаций: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка при получении рекомендаций: {str(e)[:100]}", show_alert=True)
    finally:
        if repository:
            try:
                repository.close()
            except:
                pass