"""
Costume labels for CLIP zero-shot classification.
These are the costume types the system can recognize.
"""

COSTUME_LABELS = [
    # Classic Halloween
    "witch",
    "wizard",
    "ghost",
    "skeleton",
    "zombie",
    "vampire",
    "mummy",
    "werewolf",
    "frankenstein monster",
    "devil",
    "demon",
    "angel",
    "grim reaper",

    # Superheroes & Characters
    "superhero",
    "spider-man",
    "batman",
    "superman",
    "wonder woman",
    "iron man",
    "captain america",
    "black panther",
    "hulk",
    "thor",

    # Fantasy & Storybook
    "princess",
    "prince",
    "fairy",
    "unicorn",
    "mermaid",
    "dragon",
    "knight",
    "pirate",
    "ninja",
    "cowboy",
    "astronaut",
    "robot",

    # Animals
    "cat",
    "dog",
    "dinosaur",
    "lion",
    "tiger",
    "bear",
    "bunny rabbit",
    "spider",
    "bat",

    # Pop Culture
    "clown",
    "doctor",
    "nurse",
    "police officer",
    "firefighter",
    "construction worker",

    # Other
    "pumpkin",
    "scarecrow",
    "alien",
    "monster",
    "person in costume",
    "person in regular clothes",
]

def get_costume_labels():
    """Return the full list of costume labels."""
    return COSTUME_LABELS

def get_formatted_labels():
    """Return labels formatted for CLIP (prefixed with 'a photo of')."""
    return [f"a photo of a person wearing a {label} costume" for label in COSTUME_LABELS]
