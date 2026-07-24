"""
Golden Benchmark Dataset for PitWall AI RAG Evaluation.
Curated list of real F1 strategy, telemetry, radio, and undercut queries.
"""

GOLDEN_BENCHMARK_DATASET = [
    {
        "id": "monza_2024_nor_ver_s1",
        "query": "Compare Norris vs Verstappen Sector 1 telemetry and top speed at Monza 2024.",
        "year": 2024,
        "grand_prix": "Monza",
        "driver_code": "NOR",
        "comparison_driver_code": "VER",
        "category": "TELEMETRY_COMPARISON",
        "expected_keywords": ["speed", "sector", "telemetry", "kph", "norris", "verstappen"]
    },
    {
        "id": "monza_2024_ver_undercut",
        "query": "Should Verstappen pit on Lap 18 at Monza for an undercut against Leclerc?",
        "year": 2024,
        "grand_prix": "Monza",
        "driver_code": "VER",
        "comparison_driver_code": "LEC",
        "category": "UNDERCUT_STRATEGY",
        "expected_keywords": ["undercut", "pit", "lap", "gap", "hard", "medium"]
    },
    {
        "id": "bahrain_2023_ham_tyre_deg",
        "query": "What is Hamilton's tyre degradation rate on Medium compound at Bahrain?",
        "year": 2023,
        "grand_prix": "Bahrain",
        "driver_code": "HAM",
        "comparison_driver_code": "VER",
        "category": "TYRE_DEGRADATION",
        "expected_keywords": ["degradation", "tyre", "medium", "cliff", "pace"]
    },
    {
        "id": "silverstone_2024_rain_crossover",
        "query": "Is track condition ready for Intermediates at Silverstone with 1.2 mm/min rain?",
        "year": 2024,
        "grand_prix": "Silverstone",
        "driver_code": "HAM",
        "comparison_driver_code": "NOR",
        "category": "WEATHER_CROSSOVER",
        "expected_keywords": ["intermediate", "rain", "crossover", "slick", "track"]
    },
    {
        "id": "spa_2024_lec_radio",
        "query": "Did Leclerc report front left tyre graining on pit radio during Spa 2024?",
        "year": 2024,
        "grand_prix": "Spa",
        "driver_code": "LEC",
        "comparison_driver_code": "SAI",
        "category": "RADIO_TRANSCRIPT",
        "expected_keywords": ["radio", "transcript", "graining", "tyre", "leclerc"]
    },
    {
        "id": "monaco_2024_pit_stop_loss",
        "query": "What is the net pit lane time loss at Monaco Grand Prix?",
        "year": 2024,
        "grand_prix": "Monaco",
        "driver_code": "LEC",
        "comparison_driver_code": "PIA",
        "category": "UNDERCUT_STRATEGY",
        "expected_keywords": ["pit", "loss", "monaco", "seconds", "lane"]
    },
    {
        "id": "baku_2024_pia_top_speed",
        "query": "What was Piastri's top speed down the main straight at Baku 2024?",
        "year": 2024,
        "grand_prix": "Baku",
        "driver_code": "PIA",
        "comparison_driver_code": "LEC",
        "category": "TELEMETRY_COMPARISON",
        "expected_keywords": ["speed", "baku", "straight", "drs", "kph"]
    },
    {
        "id": "austin_2024_ver_overcut",
        "query": "Is an overcut strategy viable for Verstappen against Norris at COTA Austin?",
        "year": 2024,
        "grand_prix": "Austin",
        "driver_code": "VER",
        "comparison_driver_code": "NOR",
        "category": "UNDERCUT_STRATEGY",
        "expected_keywords": ["overcut", "cota", "austin", "stint", "hard"]
    }
]
