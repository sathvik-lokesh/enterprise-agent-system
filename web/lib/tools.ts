/**
 * Research tools (4): live external API calls — weather, currency conversion,
 * public holidays, Wikipedia summaries. All endpoints are free and keyless.
 *
 * Faithful TypeScript port of tools/research_tools.py from the Python repo
 * (https://github.com/sathvik-lokesh/enterprise-agent-system). Same endpoints,
 * same arguments, same returned JSON shapes.
 */

const TIMEOUT_MS = 15_000;

async function getJson(url: string): Promise<any> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(url, {
      signal: ctrl.signal,
      headers: { "User-Agent": "enterprise-agent-demo/1.0" },
    });
    return { status: r.status, ok: r.ok, body: await r.json() };
  } finally {
    clearTimeout(t);
  }
}

function qs(params: Record<string, string | number>): string {
  return Object.entries(params)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
}

/** Get the current weather for a city (live data from Open-Meteo). */
export async function getWeather(args: { city: string }): Promise<string> {
  const city = args.city;
  try {
    const geo = await getJson(
      `https://geocoding-api.open-meteo.com/v1/search?${qs({ name: city, count: 1 })}`,
    );
    const results = geo.body?.results;
    if (!results || results.length === 0) return `City '${city}' not found.`;
    const loc = results[0];
    const wx = await getJson(
      `https://api.open-meteo.com/v1/forecast?${qs({
        latitude: loc.latitude,
        longitude: loc.longitude,
        current: "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
      })}`,
    );
    const cur = wx.body?.current ?? {};
    return JSON.stringify({
      city: loc.name,
      country: loc.country,
      temperature_c: cur.temperature_2m,
      humidity_pct: cur.relative_humidity_2m,
      wind_kmh: cur.wind_speed_10m,
    });
  } catch (e: any) {
    return `Weather service error: ${e?.message ?? e}`;
  }
}

/** Convert an amount between currencies using live exchange rates (Frankfurter / ECB). */
export async function convertCurrency(args: {
  amount: number;
  from_currency: string;
  to_currency: string;
}): Promise<string> {
  const { amount } = args;
  const from = args.from_currency.toUpperCase();
  const to = args.to_currency.toUpperCase();
  try {
    const r = await getJson(
      `https://api.frankfurter.dev/v1/latest?${qs({ base: from, symbols: to, amount })}`,
    );
    if (!r.body?.rates) return `Conversion failed: ${JSON.stringify(r.body)}`;
    return JSON.stringify({
      amount,
      from,
      to,
      converted: r.body.rates[to],
      date: r.body.date,
    });
  } catch (e: any) {
    return `Currency service error: ${e?.message ?? e}`;
  }
}

/** Get the public holidays for a country and year (live data from Nager.Date). */
export async function getPublicHolidays(args: {
  country_code: string;
  year?: number;
}): Promise<string> {
  const year = args.year ?? 2026;
  const cc = args.country_code.toUpperCase();
  try {
    const r = await getJson(`https://date.nager.at/api/v3/PublicHolidays/${year}/${cc}`);
    if (r.status !== 200) return `No holiday data for '${cc}' in ${year}.`;
    const rows = (r.body as any[]).map((h) => ({ date: h.date, name: h.name }));
    return JSON.stringify(rows.slice(0, 30));
  } catch (e: any) {
    return `Holiday service error: ${e?.message ?? e}`;
  }
}

/** Look up a short factual summary of a topic from Wikipedia (live). */
export async function lookupTopic(args: { topic: string }): Promise<string> {
  const topic = args.topic.replace(/ /g, "_");
  try {
    const r = await getJson(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topic)}`,
    );
    if (r.status !== 200) return `No Wikipedia entry found for '${args.topic}'.`;
    return JSON.stringify({ title: r.body?.title, summary: r.body?.extract });
  } catch (e: any) {
    return `Lookup service error: ${e?.message ?? e}`;
  }
}

/** OpenAI-compatible tool schemas advertised to the model. */
export const TOOL_SCHEMAS = [
  {
    type: "function" as const,
    function: {
      name: "get_weather",
      description:
        "Get the current weather for a city (live data from Open-Meteo). Call this when the user asks about weather or temperature.",
      parameters: {
        type: "object",
        properties: {
          city: { type: "string", description: "City name, e.g. 'Bengaluru' or 'San Francisco'" },
        },
        required: ["city"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "convert_currency",
      description:
        "Convert an amount between currencies using live exchange rates (Frankfurter / ECB data). Call this for any currency conversion question.",
      parameters: {
        type: "object",
        properties: {
          amount: { type: "number", description: "Amount to convert" },
          from_currency: { type: "string", description: "ISO code, e.g. USD" },
          to_currency: { type: "string", description: "ISO code, e.g. INR" },
        },
        required: ["amount", "from_currency", "to_currency"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "get_public_holidays",
      description:
        "Get the public holidays for a country and year (live data from Nager.Date). Call this for questions about upcoming holidays or office closures.",
      parameters: {
        type: "object",
        properties: {
          country_code: { type: "string", description: "Two-letter country code, e.g. IN, US, DE" },
          year: { type: "integer", description: "Year, e.g. 2026" },
        },
        required: ["country_code"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "lookup_topic",
      description:
        "Look up a short factual summary of a topic from Wikipedia (live). Call this for general-knowledge questions outside company data.",
      parameters: {
        type: "object",
        properties: {
          topic: { type: "string", description: "A topic, company, technology or person to look up" },
        },
        required: ["topic"],
      },
    },
  },
];

export type ToolName = "get_weather" | "convert_currency" | "get_public_holidays" | "lookup_topic";

export const TOOL_IMPLS: Record<ToolName, (args: any) => Promise<string>> = {
  get_weather: getWeather,
  convert_currency: convertCurrency,
  get_public_holidays: getPublicHolidays,
  lookup_topic: lookupTopic,
};
