"""Research tools (4): live external API calls — weather, currency conversion,
public holidays, Wikipedia summaries. All endpoints are free and keyless."""

import json
from typing import Annotated

import httpx
from agent_framework import tool

_TIMEOUT = 15.0


@tool
def get_weather(
    city: Annotated[str, "City name, e.g. 'Bengaluru' or 'San Francisco'"],
) -> str:
    """Get the current weather for a city (live data from Open-Meteo).
    Call this when the user asks about weather or temperature."""
    try:
        geo = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1}, timeout=_TIMEOUT,
        ).json()
        if not geo.get("results"):
            return f"City '{city}' not found."
        loc = geo["results"][0]
        wx = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": loc["latitude"], "longitude": loc["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"},
            timeout=_TIMEOUT,
        ).json()
        cur = wx.get("current", {})
        return json.dumps({"city": loc["name"], "country": loc.get("country"),
                           "temperature_c": cur.get("temperature_2m"),
                           "humidity_pct": cur.get("relative_humidity_2m"),
                           "wind_kmh": cur.get("wind_speed_10m")})
    except Exception as e:
        return f"Weather service error: {e}"


@tool
def convert_currency(
    amount: Annotated[float, "Amount to convert"],
    from_currency: Annotated[str, "ISO code, e.g. USD"],
    to_currency: Annotated[str, "ISO code, e.g. INR"],
) -> str:
    """Convert an amount between currencies using live exchange rates
    (Frankfurter / ECB data). Call this for any currency conversion question."""
    try:
        r = httpx.get(
            f"https://api.frankfurter.dev/v1/latest",
            params={"base": from_currency.upper(), "symbols": to_currency.upper(),
                    "amount": amount},
            timeout=_TIMEOUT,
        ).json()
        if "rates" not in r:
            return f"Conversion failed: {r}"
        return json.dumps({"amount": amount, "from": from_currency.upper(),
                           "to": to_currency.upper(),
                           "converted": r["rates"].get(to_currency.upper()),
                           "date": r.get("date")})
    except Exception as e:
        return f"Currency service error: {e}"


@tool
def get_public_holidays(
    country_code: Annotated[str, "Two-letter country code, e.g. IN, US, DE"],
    year: Annotated[int, "Year, e.g. 2026"] = 2026,
) -> str:
    """Get the public holidays for a country and year (live data from Nager.Date).
    Call this for questions about upcoming holidays or office closures."""
    try:
        r = httpx.get(
            f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code.upper()}",
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return f"No holiday data for '{country_code}' in {year}."
        rows = [{"date": h["date"], "name": h["name"]} for h in r.json()]
        return json.dumps(rows[:30])
    except Exception as e:
        return f"Holiday service error: {e}"


@tool
def lookup_topic(
    topic: Annotated[str, "A topic, company, technology or person to look up"],
) -> str:
    """Look up a short factual summary of a topic from Wikipedia (live).
    Call this for general-knowledge questions outside company data."""
    try:
        r = httpx.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}",
            timeout=_TIMEOUT, follow_redirects=True,
        )
        if r.status_code != 200:
            return f"No Wikipedia entry found for '{topic}'."
        d = r.json()
        return json.dumps({"title": d.get("title"), "summary": d.get("extract")})
    except Exception as e:
        return f"Lookup service error: {e}"
