import asyncio
from telethon.errors import FloodWaitError
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import (
    ChannelParticipantsSearch,
    ChannelParticipantsRecent,
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
    ChannelParticipantsContacts
)
from telethon.tl.types import User, Channel, Chat, MessageMediaPhoto, MessageMediaDocument, ChannelParticipantAdmin, \
    ChannelParticipantCreator
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

env_path = Path('pz.env')
load_dotenv(dotenv_path=env_path)


class TelegramChannelParser:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = int(api_id) if api_id else None
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient(f'session_{phone_number}', self.api_id, self.api_hash)
        self.stats_history = {}  # Для отслеживания истории
        self.participants_collected = {}  # Для отслеживания собранных участников

    async def connect(self):
        try:
            await self.client.start(phone=self.phone_number)
            print("✅ Успешно подключено к Telegram")
            # Проверяем авторизацию
            me = await self.client.get_me()
            print(f"👤 Авторизован как: {me.first_name} (@{me.username})")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            raise
        ...

    async def safe_request(self, coro):
        """
        Защита от FloodWait
        """
        try:
            return await coro
        except FloodWaitError as e:
            print(f"⏳ FloodWait {e.seconds} сек — ждём...")
            await asyncio.sleep(e.seconds + 1)
            return await coro

    async def get_channel_info(self, channel_link):
        try:
            entity = await self.client.get_entity(channel_link)

            # Проверяем тип сущности (канал, чат или группа)
            entity_type = "Неизвестно"
            if isinstance(entity, Channel):
                entity_type = "Канал"
                if entity.megagroup:
                    entity_type = "Супергруппа"
            elif isinstance(entity, Chat):
                entity_type = "Чат"

            # Получаем username с @ в начале
            username = getattr(entity, 'username', '')
            formatted_username = f"@{username}" if username else ""

            return {
                'id': entity.id,
                'title': getattr(entity, 'title', ''),
                'username': formatted_username,  # Теперь с @ в начале
                'raw_username': username,  # Сохраняем также без @ для внутреннего использования
                'participants_count': getattr(entity, 'participants_count', 0),
                'description': getattr(entity, 'about', ''),
                'date_created': getattr(entity, 'date', None),
                'type': entity_type,
                'verified': getattr(entity, 'verified', False),
                'restricted': getattr(entity, 'restricted', False),
                'scam': getattr(entity, 'scam', False),
                'access_hash': getattr(entity, 'access_hash', '')
            }
        except Exception as e:
            print(f"Ошибка при получении информации о канале: {e}")
            return None

    async def get_total_participants_count(self, channel_link):
        """
        Получение общего количества участников канала
        """
        try:
            entity = await self.client.get_entity(channel_link)
            full_chat = await self.client(GetFullChannelRequest(channel=entity))
            total_count = getattr(full_chat.full_chat, 'participants_count', 0)

            if total_count:
                print(f"📊 Всего участников в канале: {total_count}")
                return total_count
            else:
                # Если не можем получить точное количество, пробуем оценить
                print("⚠️ Не удалось получить точное количество участников")
                return None

        except Exception as e:
            print(f"❌ Ошибка получения общего количества участников: {e}")
            return None

    async def get_channel_admins(self, channel_link):
        """
        Получение списка администраторов канала/чата
        """
        try:
            entity = await self.client.get_entity(channel_link)

            admins = []
            admin_ids = set()

            print(f"\n👑 Получение списка администраторов...")

            try:
                # Получаем администраторов через специальный фильтр
                participants = await self.client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsAdmins(),
                    offset=0,
                    limit=200,
                    hash=0
                ))

                for participant in participants.participants:
                    if hasattr(participant, 'user_id'):
                        user_id = participant.user_id

                        # Находим информацию о пользователе
                        for user in participants.users:
                            if user.id == user_id:
                                username = user.username or ''
                                formatted_username = f"@{username}" if username else ''

                                # Определяем тип администратора
                                admin_type = "Админ"
                                if isinstance(participant, ChannelParticipantCreator):
                                    admin_type = "Создатель"

                                admins.append({
                                    'id': user_id,
                                    'username': formatted_username,
                                    'raw_username': username,
                                    'admin_type': admin_type
                                })
                                admin_ids.add(user_id)
                                break

                print(f"✅ Найдено администраторов: {len(admins)}")

            except Exception as e:
                print(f"⚠️ Не удалось получить администраторов через фильтр: {e}")

                # Альтернативный метод через iter_participants
                try:
                    async for participant in self.client.iter_participants(entity, filter=ChannelParticipantsAdmins()):
                        if isinstance(participant, User):
                            username = participant.username or ''
                            formatted_username = f"@{username}" if username else ''

                            admins.append({
                                'id': participant.id,
                                'username': formatted_username,
                                'raw_username': username,
                                'admin_type': "Админ"  # Определить точный тип сложнее без полной информации
                            })
                            admin_ids.add(participant.id)

                    print(f"✅ Найдено администраторов (альтернативный метод): {len(admins)}")

                except Exception as e2:
                    print(f"⚠️ Не удалось получить администраторов альтернативным методом: {e2}")

            return admin_ids, admins

        except Exception as e:
            print(f"❌ Ошибка получения администраторов: {e}")
            return set(), []

    async def parse_all_participants(self, channel_link, delay=1.5):
        """
        Парсинг ВСЕХ участников канала/чата (сохраняет username, bot и определяет админов)
        """
        participants_data = []
        collected_ids = set()  # Для отслеживания уникальных ID

        # Получаем список администраторов
        admin_ids, admins_list = await self.get_channel_admins(channel_link)
        print(f"👑 ID администраторов: {len(admin_ids)}")

        try:
            # Получаем сущность канала/чата
            entity = await self.client.get_entity(channel_link)
            channel_id = entity.id

            # Получаем общее количество участников для информации
            total_count = await self.get_total_participants_count(channel_link)

            print(f"\n🔄 Начинаем сбор ВСЕХ участников...")
            if total_count:
                print(f"📊 Всего участников для сбора: {total_count}")
            else:
                print(f"📊 Собираем участников до тех пор, пока они не закончатся...")

            print(f"⚠️ Процесс может занять некоторое время")
            print(f"⚠️ Для сбора ВСЕХ участников требуются права администратора")

            offset = 0
            batch_counter = 0
            no_new_participants_counter = 0

            # Бесконечный цикл для сбора всех участников
            while True:
                try:
                    batch_counter += 1
                    print(f"\n📦 Пакет #{batch_counter} | Собрано: {len(participants_data)} участников")

                    # Запрашиваем участников партиями
                    participants = await self.client(GetParticipantsRequest(
                        channel=entity,
                        filter=ChannelParticipantsRecent(),  # Берем недавних участников
                        offset=offset,
                        limit=200,  # Максимальный лимит за запрос
                        hash=0
                    ))

                    if not participants or not participants.users:
                        print("✅ Больше участников не найдено")
                        break

                    # Счетчик новых участников в этом пакете
                    new_in_batch = 0

                    # Обрабатываем каждого пользователя
                    for user in participants.users:
                        if isinstance(user, User):
                            # Проверяем, не собирали ли уже этого участника
                            if user.id in collected_ids:
                                continue

                            # Форматируем username с @ в начале
                            username = user.username or ''
                            formatted_username = f"@{username}" if username else ''

                            # Определяем статус администратора
                            is_admin = user.id in admin_ids
                            admin_status = "(Админ)" if is_admin else ""

                            # Формируем username с информацией об администраторе
                            username_with_admin = formatted_username
                            if is_admin:
                                username_with_admin = f"{formatted_username} {admin_status}"

                            # Сохраняем username с информацией об админе, bot и отдельное поле для админа
                            user_data = {
                                'username': username_with_admin,  # Username с информацией об админе
                                'raw_username': formatted_username,  # Оригинальный username без скобок
                                'bot': user.bot,
                                'is_admin': is_admin  # Отдельное поле для фильтрации
                            }
                            participants_data.append(user_data)
                            collected_ids.add(user.id)
                            new_in_batch += 1

                    print(f"   В этом пакете собрано: {new_in_batch} новых участников")
                    print(
                        f"   Из них администраторов: {sum(1 for p in participants_data[-new_in_batch:] if p['is_admin'])}")

                    # Если в пакете не было новых участников, увеличиваем счетчик
                    if new_in_batch == 0:
                        no_new_participants_counter += 1
                        print(f"   ⚠️ В пакете не найдено новых участников (повтор #{no_new_participants_counter})")
                    else:
                        no_new_participants_counter = 0

                    # Если несколько пакетов подряд не содержат новых участников, завершаем
                    if no_new_participants_counter >= 3:
                        print("⚠️ Несколько пакетов подряд не содержат новых участников")
                        print("✅ Вероятно, собраны все доступные участники")
                        break

                    offset += len(participants.users)

                    # Проверяем, достигли ли мы общего количества (если известно)
                    if total_count and len(participants_data) >= total_count:
                        print(f"✅ Собрано {len(participants_data)} участников из {total_count}")
                        print("✅ Достигнуто общее количество участников")
                        break

                    # Делаем паузу между запросами для избежания блокировки
                    print(f"   ⏳ Ждем {delay} секунд перед следующим запросом...")
                    await asyncio.sleep(delay)

                    # Если получено меньше 200 пользователей, значит достигли конца списка
                    if len(participants.users) < 200:
                        print("✅ Достигнут конец списка участников")
                        break

                except Exception as e:
                    print(f"❌ Ошибка при запросе участников: {e}")
                    # Пробуем продолжить с другим смещением
                    offset += 200
                    print(f"   Пробуем смещение: {offset}")
                    await asyncio.sleep(delay * 2)  # Увеличиваем задержку при ошибке

            print(f"\n🎉 СБОР ЗАВЕРШЕН!")
            print(f"✅ Всего собрано уникальных участников: {len(participants_data)}")

            # Статистика по администраторам
            admin_count = sum(1 for p in participants_data if p['is_admin'])
            print(f"👑 Собрано администраторов: {admin_count}")

            if total_count:
                coverage = (len(participants_data) / total_count) * 100
                print(f"📊 Покрытие: {coverage:.1f}% от общего количества")

            return participants_data

        except Exception as e:
            print(f"❌ Критическая ошибка при парсинге участников: {e}")
            import traceback
            traceback.print_exc()
            return participants_data  # Возвращаем то, что успели собрать

    async def parse_all_participants_with_iter(self, channel_link):
        """
        Альтернативный метод сбора всех участников через iter_participants
        Сохраняет username, bot и определяет админов
        """
        participants_data = []
        collected_ids = set()

        # Получаем список администраторов
        admin_ids, admins_list = await self.get_channel_admins(channel_link)

        try:
            entity = await self.client.get_entity(channel_link)

            print(f"\n🔄 Используем метод iter_participants для сбора ВСЕХ участников...")

            # Получаем общее количество участников
            total_count = await self.get_total_participants_count(channel_link)

            if total_count:
                print(f"📊 Ожидаемое количество участников: {total_count}")

            # Используем iter_participants без лимита
            # Внимание: для больших каналов это может занять много времени!
            collected = 0
            batch_size = 100

            try:
                async for participant in self.client.iter_participants(entity, aggressive=True):
                    if isinstance(participant, User):
                        if participant.id in collected_ids:
                            continue

                        # Форматируем username с @ в начале
                        username = participant.username or ''
                        formatted_username = f"@{username}" if username else ''

                        # Определяем статус администратора
                        is_admin = participant.id in admin_ids
                        admin_status = "(Админ)" if is_admin else ""

                        # Формируем username с информацией об администраторе
                        username_with_admin = formatted_username
                        if is_admin:
                            username_with_admin = f"{formatted_username} {admin_status}"

                        # Сохраняем username с информацией об админе, bot и отдельное поле для админа
                        user_data = {
                            'username': username_with_admin,  # Username с информацией об админе
                            'raw_username': formatted_username,  # Оригинальный username без скобок
                            'bot': participant.bot,
                            'is_admin': is_admin  # Отдельное поле для фильтрации
                        }
                        participants_data.append(user_data)
                        collected_ids.add(participant.id)
                        collected += 1

                        if collected % batch_size == 0:
                            print(f"   Собрано: {collected} участников...")
                            admin_in_batch = sum(1 for p in participants_data[-batch_size:] if p['is_admin'])
                            if admin_in_batch > 0:
                                print(f"   Из них администраторов в последней партии: {admin_in_batch}")

                            # Делаем небольшую паузу каждые batch_size участников
                            await asyncio.sleep(0.5)

                print(f"\n✅ Собрано {collected} участников через iter_participants")

                # Статистика по администраторам
                admin_count = sum(1 for p in participants_data if p['is_admin'])
                print(f"👑 Собрано администраторов: {admin_count}")

            except Exception as e:
                print(f"⚠️ Ошибка при итерации участников: {e}")
                print(f"📊 Успели собрать: {collected} участников")

            return participants_data

        except Exception as e:
            print(f"❌ Ошибка упрощенного метода: {e}")
            return []

    async def parse_participants_by_filter(self, channel_link, filter_type='all', delay=1):
        """
        Парсинг участников с использованием разных фильтров
        Сохраняет username, bot и определяет админов
        """
        participants_data = []
        collected_ids = set()

        # Получаем список администраторов
        admin_ids, admins_list = await self.get_channel_admins(channel_link)

        try:
            entity = await self.client.get_entity(channel_link)

            print(f"\n🔄 Сбор участников с фильтром: {filter_type}")

            # Выбираем фильтр в зависимости от типа
            if filter_type == 'recent':
                filter_obj = ChannelParticipantsRecent()
            elif filter_type == 'admins':
                filter_obj = ChannelParticipantsAdmins()
            elif filter_type == 'bots':
                filter_obj = ChannelParticipantsBots()
            elif filter_type == 'contacts':
                filter_obj = ChannelParticipantsContacts()
            else:
                filter_obj = ChannelParticipantsSearch('')  # Все участники

            offset = 0
            batch_counter = 0

            while True:
                batch_counter += 1

                try:
                    participants = await self.client(GetParticipantsRequest(
                        channel=entity,
                        filter=filter_obj,
                        offset=offset,
                        limit=200,
                        hash=0
                    ))

                    if not participants or not participants.users:
                        print(f"✅ Фильтр '{filter_type}': участники закончились")
                        break

                    new_in_batch = 0
                    for user in participants.users:
                        if isinstance(user, User) and user.id not in collected_ids:
                            # Форматируем username с @ в начале
                            username = user.username or ''
                            formatted_username = f"@{username}" if username else ''

                            # Определяем статус администратора
                            is_admin = user.id in admin_ids
                            admin_status = "(Админ)" if is_admin else ""

                            # Формируем username с информацией об администраторе
                            username_with_admin = formatted_username
                            if is_admin:
                                username_with_admin = f"{formatted_username} {admin_status}"

                            # Сохраняем username с информацией об админе, bot и отдельное поле для админа
                            user_data = {
                                'username': username_with_admin,  # Username с информацией об админе
                                'raw_username': formatted_username,  # Оригинальный username без скобок
                                'bot': user.bot,
                                'is_admin': is_admin  # Отдельное поле для фильтрации
                            }
                            participants_data.append(user_data)
                            collected_ids.add(user.id)
                            new_in_batch += 1

                    print(
                        f"   Пакет #{batch_counter}: {new_in_batch} новых участников | Всего: {len(participants_data)}")

                    # Показываем сколько администраторов в этом пакете
                    admin_in_batch = sum(1 for p in participants_data[-new_in_batch:] if p['is_admin'])
                    if admin_in_batch > 0:
                        print(f"   Администраторов в этом пакете: {admin_in_batch}")

                    offset += len(participants.users)

                    if len(participants.users) < 200:
                        break

                    # Пауза между запросами
                    await asyncio.sleep(delay)

                except Exception as e:
                    print(f"❌ Ошибка в пакете #{batch_counter}: {e}")
                    offset += 200
                    await asyncio.sleep(delay * 2)

            print(f"\n✅ Фильтр '{filter_type}': собрано {len(participants_data)} участников")

            # Статистика по администраторам для этого фильтра
            admin_count = sum(1 for p in participants_data if p['is_admin'])
            print(f"👑 Администраторов в фильтре: {admin_count}")

            return participants_data

        except Exception as e:
            print(f"❌ Ошибка при парсинге с фильтром: {e}")
            return []

    async def collect_all_participants_comprehensive(self, channel_link):
        """
        ⚡ Максимально быстрый сбор участников Telegram
        Реальный предел скорости API
        """

        entity = await self.client.get_entity(channel_link)

        # Получаем админов ОДИН РАЗ
        admin_ids, _ = await self.get_channel_admins(channel_link)

        participants = []
        collected_ids = set()

        print("\n🚀 FAST MODE x1.5")
        print("⚠️ Скорость ограничена Telegram API")

        start = datetime.now()
        counter = 0

        async for user in self.client.iter_participants(
                entity,
                aggressive=True
        ):
            if not isinstance(user, User):
                continue

            if user.id in collected_ids:
                continue

            collected_ids.add(user.id)

            username = user.username or ""
            formatted = f"@{username}" if username else ""

            is_admin = user.id in admin_ids

            participants.append({
                "username": f"{formatted} (Админ)" if is_admin else formatted,
                "raw_username": formatted,
                "bot": user.bot,
                "is_admin": is_admin
            })

            counter += 1

            if counter % 1000 == 0:
                elapsed = (datetime.now() - start).seconds or 1
                speed = counter // elapsed
                print(f"⚡ {counter} | {speed}/сек")

            # микро-пауза против FloodWait
            if counter % 3000 == 0:
                await asyncio.sleep(0.3)

        print(f"\n✅ ГОТОВО")
        print(f"👥 Всего: {len(participants)}")

        return participants

    async def get_participants_count(self, channel_link, update_from_api=True):
        """
        Получение точного количества участников канала/чата
        """
        try:
            entity = await self.client.get_entity(channel_link)

            if update_from_api:
                # Получаем свежие данные из API
                full_chat = await self.client(GetFullChannelRequest(channel=entity))
                participants_count = getattr(full_chat.full_chat, 'participants_count', 0)

                print(f"✅ Актуальное количество участников: {participants_count}")
                return participants_count if participants_count else 0
            else:
                # Используем кэшированные данные
                count = getattr(entity, 'participants_count', 0)
                if count and count > 0:
                    print(f"📊 Количество участников (кэш): {count}")
                    return count
                else:
                    # Если в кэше нет данных, запрашиваем из API
                    return await self.get_participants_count(channel_link, update_from_api=True)

        except Exception as e:
            print(f"❌ Ошибка при получении количества участников: {e}")
            return 0

    async def get_detailed_stats(self, channel_link):
        """
        Получение подробной статистики канала
        """
        try:
            entity = await self.client.get_entity(channel_link)
            full_chat = await self.client(GetFullChannelRequest(channel=entity))

            # Получаем username с @ в начале
            username = getattr(entity, 'username', '')
            formatted_username = f"@{username}" if username else ""

            stats = {
                'total_participants': getattr(full_chat.full_chat, 'participants_count', 0) or 0,
                'online_count': getattr(full_chat.full_chat, 'online_count', 0) or 0,
                'admins_count': len(
                    full_chat.full_chat.admin_rights) if hasattr(full_chat.full_chat, 'admin_rights') else 0,
                'kicked_count': getattr(full_chat.full_chat, 'kicked_count', 0) or 0,
                'banned_count': getattr(full_chat.full_chat, 'banned_count', 0) or 0,
                'read_inbox_max_id': getattr(full_chat.full_chat, 'read_inbox_max_id', 0) or 0,
                'read_outbox_max_id': getattr(full_chat.full_chat, 'read_outbox_max_id', 0) or 0,
                'unread_count': getattr(full_chat.full_chat, 'unread_count', 0) or 0,
                'migrated_from_chat_id': getattr(full_chat.full_chat, 'migrated_from_chat_id', None),
                'can_view_participants': getattr(full_chat.full_chat, 'can_view_participants', False),
                'can_set_username': getattr(full_chat.full_chat, 'can_set_username', False),
                'can_set_stickers': getattr(full_chat.full_chat, 'can_set_stickers', False),
                'has_link': getattr(full_chat.full_chat, 'has_link', False),
                'has_geo': getattr(full_chat.full_chat, 'has_geo', False),
                'slowmode_seconds': getattr(full_chat.full_chat, 'slowmode_seconds', 0) or 0,
                'linked_chat_id': getattr(full_chat.full_chat, 'linked_chat_id', None),
            }

            print("\n📈 Детальная статистика канала:")
            print(f"   Всего участников: {stats['total_participants']}")
            print(f"   Онлайн сейчас: {stats['online_count']}")
            print(f"   Администраторов: {stats['admins_count']}")
            print(f"   Заблокировано: {stats['banned_count']}")
            print(f"   Исключено: {stats['kicked_count']}")
            print(f"   Можно просматривать участников: {'✅' if stats['can_view_participants'] else '❌'}")
            print(f"   Есть ссылка на приглашение: {'✅' if stats['has_link'] else '❌'}")
            print(f"   Режим медленной отправки: {stats['slowmode_seconds']} сек")

            return stats

        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return None

    async def analyze_participants(self, participants):
        """Анализ собранных участников (username, bot и админы)"""
        if not participants:
            print("Нет данных участников для анализа")
            return

        print("\n📊 Анализ участников:")
        print(f"Всего участников: {len(participants)}")

        # Статистика по ботам
        bots = sum(1 for p in participants if p.get('bot') == True)
        if participants:
            bots_percentage = (bots / len(participants)) * 100
            print(f"Ботов: {bots} ({bots_percentage:.1f}%)")
        else:
            print("Ботов: 0 (0%)")

        # Статистика по администраторам
        admins = sum(1 for p in participants if p.get('is_admin') == True)
        if participants:
            admins_percentage = (admins / len(participants)) * 100
            print(f"Администраторов: {admins} ({admins_percentage:.1f}%)")
        else:
            print("Администраторов: 0 (0%)")

        # Статистика по username
        has_username = sum(1 for p in participants if p.get('raw_username', '').strip())
        if participants:
            username_percentage = (has_username / len(participants)) * 100
            print(f"С username: {has_username} ({username_percentage:.1f}%)")
        else:
            print("С username: 0 (0%)")

        # Боты-администраторы
        bot_admins = sum(1 for p in participants if p.get('bot') == True and p.get('is_admin') == True)
        if admins > 0:
            bot_admins_percentage = (bot_admins / admins) * 100 if admins > 0 else 0
            print(f"Ботов-администраторов: {bot_admins} ({bot_admins_percentage:.1f}% от всех админов)")

    async def save_participants_with_progress(self, participants, filename_prefix):
        """
        Сохранение участников с прогрессом (CSV с username и bot)
        """
        if not participants:
            print("⚠️ Нет данных участников для сохранения")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Сохраняем в CSV
        csv_filename = f'{filename_prefix}_all_participants_{timestamp}.csv'
        print(f"\n💾 Сохраняем участников в CSV: {csv_filename}")

        df = pd.DataFrame(participants)

        # Сохраняем только колонки username и bot (без is_admin)
        if 'username' in df.columns and 'bot' in df.columns:
            # Создаем финальный DataFrame с нужными колонками
            final_df = df[['username', 'bot']].copy()

            # Заменяем True/False на более понятные значения
            final_df['bot'] = final_df['bot'].map({True: 'Да', False: 'Нет'})

            # Переименовываем колонки для удобства
            final_df.columns = ['Username (с статусом админа)', 'Бот']

            final_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"✅ CSV сохранен: {csv_filename}")
            print(f"   Записей: {len(final_df)}")
            print(f"   Колонки: Username (с статусом админа), Бот")
        else:
            print("❌ Ошибка: В данных отсутствуют необходимые колонки")

        # Создаем сводный отчет TXT
        report_filename = f'{filename_prefix}_participants_report_{timestamp}.txt'
        print(f"\n📊 Создаем сводный отчет: {report_filename}")

        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ОТЧЕТ ПО СОБРАННЫМ УЧАСТНИКАМ\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата сбора: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего участников: {len(participants)}\n\n")

            # Статистика
            f.write("СТАТИСТИКА:\n")
            f.write("-" * 40 + "\n")

            # Боты
            bots = sum(1 for p in participants if p.get('bot') == True)
            f.write(f"Ботов: {bots} ({(bots / len(participants) * 100):.1f}%)\n")

            # Администраторы
            admins = sum(1 for p in participants if p.get('is_admin') == True)
            f.write(f"Администраторов: {admins} ({(admins / len(participants) * 100):.1f}%)\n")

            # С username
            has_username = sum(1 for p in participants if p.get('raw_username', '').strip())
            f.write(f"С username: {has_username} ({(has_username / len(participants) * 100):.1f}%)\n")

            # Боты-администраторы
            bot_admins = sum(1 for p in participants if p.get('bot') == True and p.get('is_admin') == True)
            if admins > 0:
                f.write(f"Ботов-администраторов: {bot_admins} ({(bot_admins / admins * 100):.1f}% от всех админов)\n")

            # Список администраторов
            if admins > 0:
                f.write("\nСПИСОК АДМИНИСТРАТОРОВ:\n")
                f.write("-" * 40 + "\n")
                admin_counter = 0
                for participant in participants:
                    if participant.get('is_admin'):
                        admin_counter += 1
                        username = participant.get('username', 'Нет username')
                        bot_status = " (Бот)" if participant.get('bot') else ""
                        f.write(f"{admin_counter}. {username}{bot_status}\n")

            # Пример первых 10 участников
            f.write("\nПЕРВЫЕ 10 УЧАСТНИКОВ:\n")
            f.write("-" * 40 + "\n")
            for i, participant in enumerate(participants[:10], 1):
                username = participant.get('username', 'Нет username')
                bot_status = "Бот" if participant.get('bot') else "Человек"
                admin_status = "Админ" if participant.get('is_admin') else "Обычный"
                f.write(f"{i}. {username} ({bot_status}, {admin_status})\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("ФАЙЛЫ:\n")
            f.write(f"CSV файл со всеми участниками: {csv_filename}\n")
            f.write(f"Отчет: {report_filename}\n")
            f.write("=" * 60 + "\n")

        print(f"✅ Отчет сохранен: {report_filename}")

        return csv_filename, report_filename

    async def close(self):
        if self.client.is_connected():
            await self.client.disconnect()
            print("🔌 Соединение закрыто")


async def main():
    # Конфигурация
    API_ID = os.getenv('TELEGRAM_API_ID')
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        print("❌ Ошибка: Не все переменные окружения установлены!")
        print("Убедитесь, что файл .env существует и содержит:")
        print("TELEGRAM_API_ID=ваш_id")
        print("TELEGRAM_API_HASH=ваш_hash")
        print("TELEGRAM_PHONE=ваш_номер")
        return

    try:
        API_ID = int(API_ID)
    except ValueError:
        print("❌ Ошибка: API_ID должен быть числом!")
        return

    # Создаем парсер
    parser = TelegramChannelParser(
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER
    )

    try:
        # Подключаемся
        await parser.connect()

        # Список каналов для парсинга
        channels_to_parse = [
            'https://t.me/onsiteshop56',
            # Добавьте другие каналы при необходимости
        ]

        print(f"\n{'=' * 80}")
        print("🔍 ПАРСИНГ ВСЕХ УЧАСТНИКОВ ТЕЛЕГРАМ КАНАЛОВ")
        print('=' * 80)
        print("⚠️ Будут сохранены username с пометкой админов и информация о ботах")
        print('=' * 80)

        for channel in channels_to_parse:
            print(f"\n📊 Анализ канала: {channel}")
            print('=' * 50)

            # 1. Получаем базовую информацию о канале
            channel_info = await parser.get_channel_info(channel)
            if channel_info:
                print(f"\n📋 Информация о канале:")
                print(f"   Название: {channel_info['title']}")
                print(f"   Username: {channel_info['username']}")
                print(f"   Тип: {channel_info['type']}")
                print(f"   Участников: {channel_info['participants_count']}")
                print(f"   Описание: {channel_info['description'][:100]}..." if channel_info[
                    'description'] else "   Описание: нет")

                # 2. Получаем детальную статистику
                stats = await parser.get_detailed_stats(channel)

                # 3. Собираем всех участников (комплексный метод)
                print(f"\n{'=' * 50}")
                print("👥 СБОР ВСЕХ УЧАСТНИКОВ")
                print('=' * 50)

                participants = await parser.collect_all_participants_comprehensive(channel)

                if participants:
                    # 4. Анализируем участников
                    await parser.analyze_participants(participants)

                    # 5. Сохраняем результаты
                    channel_name = channel_info['raw_username'] or channel_info['title'].replace(' ', '_')
                    await parser.save_participants_with_progress(
                        participants,
                        f"parsed_data/{channel_name}"
                    )

                    # Создаем папку parsed_data если её нет
                    os.makedirs("parsed_data", exist_ok=True)

                else:
                    print(f"\n⚠️ Не удалось собрать участников канала {channel}")

            else:
                print(f"❌ Не удалось получить информацию о канале {channel}")

            print(f"\n✅ Завершен анализ канала: {channel}")
            print('=' * 50)

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем соединение
        await parser.close()


if __name__ == "__main__":
    # Создаем папку для данных если её нет
    os.makedirs("parsed_data", exist_ok=True)

    # Запускаем асинхронную функцию
    asyncio.run(main())