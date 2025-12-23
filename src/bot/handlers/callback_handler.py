import logging
from typing import Dict
from aiogram import F
from aiogram.types import CallbackQuery

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.utils.concert_utils import get_concert_date, get_concert_venue

from src.bot.utils import (
    remove_duplicate_concerts,
    filter_by_city,
    group_by_artist,
    extract_date_sort_key,
    format_concert_message,
    create_city_selection_keyboard,
    create_concert_keyboard
)

logger = logging.getLogger(__name__)


async def handle_city_selection(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    
    if user_id not in user_results:
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    callback_data = callback.data
    
    if callback_data == "city_select":
        results = user_results[user_id]
        available_cities = results.get('available_cities', [])
        if available_cities:
            city_keyboard = create_city_selection_keyboard(available_cities)
            await callback.message.edit_text(
                f"📍 Выберите город для просмотра концертов:",
                reply_markup=city_keyboard
            )
        await callback.answer()
        return
    
    if callback_data == "city_all":
        results = user_results[user_id]
        original_concerts = results['original_concerts']
        
        results['concerts'] = original_concerts.copy()
        results['city_filter'] = None
        results['current_page'] = 0
        
        if results['sort_by'] == 'artist':
            grouped = group_by_artist(results['concerts'])
            sorted_concerts = []
            for artist in sorted(grouped.keys()):
                sorted_concerts.extend(grouped[artist])
            results['concerts'] = remove_duplicate_concerts(sorted_concerts)
        elif results['sort_by'] == 'date':
            sorted_concerts = sorted(results['concerts'], 
                                   key=lambda x: extract_date_sort_key(
                                       get_concert_date(x) or ''
                                   ))
            results['concerts'] = remove_duplicate_concerts(sorted_concerts)
        
        updated_concerts = results['concerts']
        page_size = 10
        start_idx = results['current_page'] * page_size
        concert_text = format_concert_message(updated_concerts, start_idx, page_size, results['sort_by'])
        keyboard = create_concert_keyboard(
            updated_concerts, 
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
        return
    
    if callback_data == "city_change":
        results = user_results[user_id]
        available_cities = results.get('available_cities', [])
        if available_cities:
            city_keyboard = create_city_selection_keyboard(available_cities)
            await callback.message.edit_text(
                f"📍 Выберите город для просмотра концертов:",
                reply_markup=city_keyboard
            )
        await callback.answer()
        return
    
    city_name = callback_data.replace("city_", "")
    results = user_results[user_id]
    original_concerts = results['original_concerts']
    
    filtered = filter_by_city(original_concerts, city_name)
    results['concerts'] = filtered
    results['city_filter'] = city_name
    results['current_page'] = 0
    
    if results['sort_by'] == 'artist':
        grouped = group_by_artist(filtered)
        sorted_concerts = []
        for artist in sorted(grouped.keys()):
            sorted_concerts.extend(grouped[artist])
        results['concerts'] = remove_duplicate_concerts(sorted_concerts)
    elif results['sort_by'] == 'date':
        sorted_concerts = sorted(filtered, 
                               key=lambda x: extract_date_sort_key(
                                   get_concert_date(x) or ''
                               ))
        results['concerts'] = remove_duplicate_concerts(sorted_concerts)
    
    # Обновляем сообщение
    updated_concerts = results['concerts']
    page_size = 10
    start_idx = results['current_page'] * page_size
    concert_text = format_concert_message(updated_concerts, start_idx, page_size, results['sort_by'])
    keyboard = create_concert_keyboard(
        updated_concerts, 
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


async def handle_sort(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    
    if user_id not in user_results:
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    sort_type = callback.data.split("_")[1]
    results = user_results[user_id]
    concerts = results['concerts'].copy()
    
    if sort_type == 'artist':
        grouped = group_by_artist(concerts)
        sorted_concerts = []
        for artist in sorted(grouped.keys()):
            sorted_concerts.extend(grouped[artist])
        results['concerts'] = remove_duplicate_concerts(sorted_concerts)
        results['sort_by'] = 'artist'
    elif sort_type == 'date':
        sorted_concerts = sorted(concerts, 
                               key=lambda x: extract_date_sort_key(
                                   get_concert_date(x) or ''
                               ))
        results['concerts'] = remove_duplicate_concerts(sorted_concerts)
        results['sort_by'] = 'date'
    
    results['current_page'] = 0
    updated_concerts = results['concerts']
    page_size = 10
    start_idx = results['current_page'] * page_size
    concert_text = format_concert_message(updated_concerts, start_idx, page_size, results['sort_by'])
    keyboard = create_concert_keyboard(
        updated_concerts,
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


async def handle_pagination(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    
    if user_id not in user_results:
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    page = int(callback.data.split("_")[1])
    results = user_results[user_id]
    results['current_page'] = page
    
    concerts = results['concerts']
    page_size = 10
    start_idx = page * page_size  # Правильно вычисляем start_idx из номера страницы
    concert_text = format_concert_message(concerts, start_idx, page_size, results['sort_by'])
    keyboard = create_concert_keyboard(
        concerts,
        page,
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


async def handle_reminder(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    
    if user_id not in user_results:
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    try:
        concert_idx = int(callback.data.split("_")[1])
        results = user_results[user_id]
        concerts = results['concerts']
        
        if 0 <= concert_idx < len(concerts):
            concert = concerts[concert_idx]
            title = concert.get('title', 'Концерт')
            date = get_concert_date(concert) or 'дата не указана'
            venue = get_concert_venue(concert) or 'площадка не указана'
            
            await callback.answer(
                f"🔔 Напоминание добавлено для: {title}\n"
                f"📅 {date} в {venue}",
                show_alert=True
            )
        else:
            await callback.answer("Ошибка: концерт не найден")
    except Exception as e:
        logger.error(f"Ошибка добавления напоминания: {e}")
        await callback.answer("Ошибка при добавлении напоминания")


async def handle_recommendations(callback: CallbackQuery, user_results: Dict):
    user_id = callback.from_user.id
    
    if user_id not in user_results:
        await callback.answer("Результаты устарели. Отправьте ссылку на плейлист заново.")
        return
    
    results = user_results[user_id]
    artists = results.get('artists', [])
    city_filter = results.get('city_filter')
    
    if not artists:
        await callback.answer("Нет артистов для рекомендаций", show_alert=True)
        return
    
    await callback.answer("🤖 Анализирую ваши музыкальные предпочтения...")
    
    try:
        from src.services.recommendation_service import RecommendationService
        from src.repositories.concert_repository import ConcertRepository
        
        repository = ConcertRepository()
        
        if city_filter:
            city_map = {
                'Москва': 'moscow',
                'Санкт-Петербург': 'saint-petersburg',
                'Екатеринбург': 'yekaterinburg',
                'Новосибирск': 'novosibirsk',
                'Казань': 'kazan',
                'Нижний Новгород': 'nizhny-novgorod',
                'Челябинск': 'chelyabinsk',
                'Самара': 'samara',
                'Оренбург': 'orenburg'
            }
            city_code = city_map.get(city_filter, city_filter.lower())
        else:
            city_code = ''
        
        recommendation_service = RecommendationService(repository, city=city_code)
        
        if not recommendation_service.enabled:
            await callback.answer(
                "⚠️ Рекомендации отключены. Установите GEMINI_API_KEY в .env",
                show_alert=True
            )
            return
        recommended_concerts = recommendation_service.get_recommendations(
            artists,
            max_recommendations=10
        )
        
        if not recommended_concerts:
            await callback.answer(
                "😔 Не удалось найти рекомендации. Попробуйте позже.",
                show_alert=True
            )
            return
        
        from src.bot.utils import format_concert_message, create_concert_keyboard
        recommended_concerts_with_marker = []
        for concert in recommended_concerts:
            concert_copy = concert.copy()
            concert_copy['is_recommended'] = True
            recommended_concerts_with_marker.append(concert_copy)
        
        concert_text = format_concert_message(recommended_concerts_with_marker, 0, 10, 'date')
        header = "✨ РЕКОМЕНДОВАНО ВАМ\n\n"
        header += "На основе анализа ваших музыкальных предпочтений:\n\n"
        
        keyboard = create_concert_keyboard(
            recommended_concerts_with_marker,
            0,
            10,
            city_filter,
            'date',
            results.get('available_cities', [])
        )
        
        await callback.message.answer(
            f"{header}{concert_text}",
            reply_markup=keyboard
        )
        
        results['recommended_concerts'] = recommended_concerts_with_marker
        
        await callback.answer("✨ Рекомендации отправлены отдельным сообщением")
        repository.close()
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при получении рекомендаций: {e}", exc_info=True)
        try:
            repository.close()
        except:
            pass
        await callback.answer(
            f"❌ Ошибка при получении рекомендаций: {str(e)[:100]}",
            show_alert=True
        )


async def handle_refresh(callback: CallbackQuery, user_results: Dict):
    await callback.answer("Обновление...")
    # Просто обновляем текущую страницу
    user_id = callback.from_user.id
    if user_id in user_results:
        results = user_results[user_id]
        concerts = results['concerts']
        page_size = 10
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

