"""Live demo presets shared by the Gradio app and API."""

LIVE_DEMO_PRESET_GROUPS = [
    {
        "group": "High-motion trailers from start",
        "items": [
            {
                "label": "Mission Impossible trailer from start",
                "url": "https://www.youtube.com/watch?v=avz06PDqDbM",
                "clip_top3": 0.333,
                "adqa_score": 1.0,
                "start_label": "t=0",
            },
            {
                "label": "John Wick 4 trailer from start",
                "url": "https://www.youtube.com/watch?v=qEVUtrk8_B4",
                "clip_top3": 0.332,
                "adqa_score": 1.0,
                "start_label": "t=0",
            },
            {
                "label": "Top Gun Maverick trailer from start",
                "url": "https://www.youtube.com/watch?v=giXco2jaZ_4",
                "clip_top3": 0.340,
                "adqa_score": 2 / 3,
                "start_label": "t=0",
            },
            {
                "label": "Dune Part Two trailer from start",
                "url": "https://www.youtube.com/watch?v=Way9Dexny3w",
                "clip_top3": 0.329,
                "adqa_score": 2 / 3,
                "start_label": "t=0",
            },
            {
                "label": "Spider-Man trailer from start",
                "url": "https://www.youtube.com/watch?v=JfVOs4VSpmA",
                "clip_top3": 0.317,
                "adqa_score": 1.0,
                "start_label": "t=0",
            },
            {
                "label": "The Batman trailer from start",
                "url": "https://www.youtube.com/watch?v=mqqft2x_Aa4",
                "clip_top3": 0.305,
                "adqa_score": 1.0,
                "start_label": "t=0",
            },
        ],
    },
    {
        "group": "High-motion action windows",
        "items": [
            {
                "label": "Top Gun trailer action segment",
                "url": "https://www.youtube.com/watch?v=giXco2jaZ_4&t=55s",
                "clip_top3": 0.394,
                "adqa_score": 1.0,
                "start_label": "55s",
            },
            {
                "label": "Dune Part Two trailer action segment",
                "url": "https://www.youtube.com/watch?v=Way9Dexny3w&t=82s",
                "clip_top3": 0.328,
                "adqa_score": 1.0,
                "start_label": "82s",
            },
            {
                "label": "The Batman trailer action segment",
                "url": "https://www.youtube.com/watch?v=mqqft2x_Aa4&t=75s",
                "clip_top3": 0.304,
                "adqa_score": 1.0,
                "start_label": "75s",
            },
            {
                "label": "Spider-Man trailer action segment",
                "url": "https://www.youtube.com/watch?v=JfVOs4VSpmA&t=80s",
                "clip_top3": 0.280,
                "adqa_score": 1.0,
                "start_label": "80s",
            },
            {
                "label": "Mission Impossible trailer action segment",
                "url": "https://www.youtube.com/watch?v=avz06PDqDbM&t=70s",
                "clip_top3": 0.265,
                "adqa_score": 1.0,
                "start_label": "70s",
            },
            {
                "label": "John Wick 4 trailer action segment",
                "url": "https://www.youtube.com/watch?v=qEVUtrk8_B4&t=78s",
                "clip_top3": 0.197,
                "adqa_score": 1.0,
                "start_label": "78s",
            },
        ],
    },
    {
        "group": "Earlier live-tested clips",
        "items": [
            {
                "label": "Indoor diving platform",
                "url": "https://www.youtube.com/watch?v=3P5sjWImRqA&t=10s",
                "clip_top3": 0.379,
                "adqa_score": 1.0,
                "start_label": "10s",
            },
            {
                "label": "Waterfall",
                "url": "https://www.youtube.com/watch?v=VMbJTgzMhKE&t=30s",
                "clip_top3": 0.323,
                "adqa_score": 1.0,
                "start_label": "30s",
            },
            {
                "label": "Martial arts board break",
                "url": "https://www.youtube.com/watch?v=frZUEXzWE5Q&t=180s",
                "clip_top3": 0.315,
                "adqa_score": 1.0,
                "start_label": "180s",
            },
            {
                "label": "Girl cooks eggs",
                "url": "https://www.youtube.com/watch?v=B0EKYDSv_yQ&t=2s",
                "clip_top3": 0.310,
                "adqa_score": 1.0,
                "start_label": "2s",
            },
            {
                "label": "Fishing boat at sunset",
                "url": "https://www.youtube.com/watch?v=FC8gpdOevrg&t=30s",
                "clip_top3": 0.301,
                "adqa_score": 1.0,
                "start_label": "30s",
            },
            {
                "label": "Burger eating challenge",
                "url": "https://www.youtube.com/watch?v=058y9xGmmTQ&t=206s",
                "clip_top3": 0.278,
                "adqa_score": 2 / 3,
                "start_label": "206s",
            },
            {
                "label": "Spinach salad prep",
                "url": "https://www.youtube.com/watch?v=PbGvLf7HvXQ&t=63s",
                "clip_top3": 0.408,
                "adqa_score": 1 / 3,
                "start_label": "63s",
            },
        ],
    },
    {
        "group": "Held-out VATEX windows",
        "items": [
            {
                "label": "Beer pour held-out test",
                "url": "https://www.youtube.com/watch?v=FtBS6OZSGMI&t=28s",
                "clip_top3": 0.357,
                "adqa_score": 1.0,
                "start_label": "28s",
            },
            {
                "label": "Barn horse bucket held-out test",
                "url": "https://www.youtube.com/watch?v=NMIAhI8oF9s&t=1s",
                "clip_top3": 0.363,
                "adqa_score": 1.0,
                "start_label": "1s",
            },
        ],
    },
]


def _full_label(item: dict) -> str:
    yes = round(float(item["adqa_score"]) * 3)
    return (
        f"{item['label']} - CLIP {item['clip_top3']:.3f}, "
        f"ADQA {yes}/3"
    )


LIVE_DEMO_PRESETS = {
    _full_label(item): item["url"]
    for group in LIVE_DEMO_PRESET_GROUPS
    for item in group["items"]
}

LIVE_DEMO_DEFAULT = next(iter(LIVE_DEMO_PRESETS))

