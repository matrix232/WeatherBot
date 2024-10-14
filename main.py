import asyncio
import requests
import logging
import sys
import config

from geopy.geocoders import Nominatim
import openmeteo_requests
import pandas as pd

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram import F

dp = Dispatcher()


def get_coordinates(city: str):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(city)

    if location:
        return location.latitude, location.longitude
    else:
        return None, None


def get_weather_forecast(latitude, longitude):
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,windspeed_10m,pressure_msl,relativehumidity_2m,weathercode&timezone=Europe%2FBerlin&past_days=0&forecast_days=1"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()

        temperature_2m = data['hourly']['temperature_2m']
        windspeed_10m = data['hourly']['windspeed_10m']
        pressure_msl = data['hourly']['pressure_msl']
        humidity_2m = data['hourly']['relativehumidity_2m']
        weather_code = data['hourly']['weathercode']

        # Проверяем длину списка
        if len(temperature_2m) >= 24:
            # Интерполяция для 25 часов
            temperature_25h = (temperature_2m[23] + temperature_2m[0]) / 2
            windspeed_25h = (windspeed_10m[23] + windspeed_10m[0]) / 2
            pressure_25h = (pressure_msl[23] + pressure_msl[0]) / 2
            humidity_25h = ((humidity_2m[23] + humidity_2m[0]) / 2) * 0.75
            weather_code_25h = (weather_code[23] + weather_code[0]) // 2

            max_temperature = max(temperature_2m)

            forecast = {
                'temperature_2m': temperature_25h,
                'windspeed_10m': windspeed_25h,
                'pressure_msl': pressure_25h,
                'humidity_2m': humidity_25h,
                'max_temperature': max_temperature,
                'weather_code': weather_code_25h
            }

            return forecast
        else:
            return None
    else:
        return None


@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(
        f"Hello {html.bold(message.from_user.full_name)}. Введи /weather <город> и я тебе покажу погоду!")


@dp.message(F.text, Command("weather"))
async def find_weather(message: Message):
    try:
        city = message.text.split()[1]
        if len(city) != 0:
            latitude, longitude = get_coordinates(city)
            data = get_weather_forecast(latitude, longitude)

            await message.answer(f"""
                        Погода в городе: {city}
Максимальная Температура: {data['max_temperature']}℃
Скорость ветра: {data['windspeed_10m']} м/с
Давление: {data['pressure_msl']} мм рт.ст.
Влажность: {data['humidity_2m']} %
""")
        else:
            await message.answer("LEN < 0")
    except Exception as ex:
        await message.answer("Пожалуйста, введите город!")


async def main() -> None:
    bot = Bot(token=config.TOKEN_BOT, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
