#!/usr/bin/env python3
"""
Prompt templates for Halloween costume classification.
Different prompts for various classification needs.
"""

# Standard costume classification
COSTUME_CLASSIFICATION = """You are a Halloween costume classifier.
Analyze this image and identify what Halloween costume the person is wearing.
Provide a specific costume name (e.g., 'Witch', 'Vampire', 'Superhero - Spider-Man',
'Princess - Elsa', 'Ghost', 'Zombie').
If you can see multiple people, describe each costume.
If no clear costume is visible, say 'No costume detected'.
Be specific but concise - just the costume name(s)."""

# Detailed costume analysis
DETAILED_COSTUME_ANALYSIS = """You are a Halloween costume expert.
Analyze this image in detail and provide:
1. The costume name/character
2. Key costume elements you can identify
3. Overall costume quality (simple, moderate, elaborate)
4. Any notable accessories or props
5. Estimated age group (child, teen, adult)

Be thorough but concise."""

# Fun/creative costume description
FUN_COSTUME_DESCRIPTION = """You are an enthusiastic Halloween costume judge!
Look at this trick-or-treater's costume and provide a fun, encouraging description.
Include:
- What costume they're wearing
- What makes it cool or creative
- A fun Halloween-themed compliment

Keep it brief and kid-friendly!"""

# Multi-person costume detection
MULTI_PERSON_DETECTION = """Analyze this Halloween image and list all people you can see.
For each person, provide:
- Position in image (left, center, right, etc.)
- Costume worn
- Confidence level (high/medium/low)

Format: "Person 1 (left): Witch costume (high confidence)"
If only one person, just say "Single person: [costume name]"."""

# Costume category classification
COSTUME_CATEGORY = """Classify this Halloween costume into one of these categories:
- Scary (monsters, zombies, ghosts, vampires)
- Fantasy (wizards, fairies, dragons, mythical creatures)
- Superhero (Marvel, DC, comic book characters)
- Character (movie/TV/game characters, Disney, anime)
- Historical (pirates, knights, cowboys, historical figures)
- Funny/Silly (puns, humorous costumes)
- Classic (witch, ghost, skeleton, mummy)
- Creative/Original (unique handmade costumes)
- Other

Respond with just the category name and a brief explanation."""

# Costume safety check
COSTUME_SAFETY_CHECK = """As a Halloween safety expert, analyze this costume for safety concerns:
1. Visibility (can they see clearly?)
2. Trip hazards (costume dragging, too long?)
3. Reflective elements (visible in dark?)
4. Flame resistance concerns (loose fabric near candles?)
5. Overall safety rating (Good/Fair/Needs Improvement)

Be constructive and helpful."""

# Group costume analysis
GROUP_COSTUME_ANALYSIS = """Analyze if this is a group or coordinated costume.
Look for:
- Are multiple people wearing related/matching costumes?
- Is it a themed group (Avengers, Scooby-Doo gang, etc.)?
- How many people in the group?
- What's the theme?

If it's just one person or unrelated costumes, say "Individual costume(s)" and describe what you see."""

# Age-appropriate detection
AGE_APPROPRIATE_ANALYSIS = """Analyze this costume and determine:
1. Approximate age of person wearing it
2. Is the costume age-appropriate?
3. Costume complexity level
4. Any safety considerations for this age group

Be factual and helpful."""

# Costume quality assessment
COSTUME_QUALITY_ASSESSMENT = """Rate this Halloween costume on:
1. Creativity: (1-5 stars)
2. Execution: (1-5 stars)
3. Overall impression: (1-5 stars)
4. What works well
5. What could be improved

Be encouraging and constructive!"""

# Quick one-word classification
QUICK_CLASSIFICATION = """In one or two words, what is this Halloween costume?
Just the costume name, nothing else."""


def get_prompt(prompt_type: str = "standard") -> str:
    """
    Get a prompt template by name.

    Args:
        prompt_type: Type of prompt to retrieve. Options:
            - "standard": Basic costume classification (default)
            - "detailed": Detailed costume analysis
            - "fun": Fun, encouraging description
            - "multi": Multi-person detection
            - "category": Costume category classification
            - "safety": Safety analysis
            - "group": Group costume analysis
            - "age": Age-appropriate analysis
            - "quality": Quality assessment
            - "quick": One-word classification

    Returns:
        Prompt string
    """
    prompts = {
        "standard": COSTUME_CLASSIFICATION,
        "detailed": DETAILED_COSTUME_ANALYSIS,
        "fun": FUN_COSTUME_DESCRIPTION,
        "multi": MULTI_PERSON_DETECTION,
        "category": COSTUME_CATEGORY,
        "safety": COSTUME_SAFETY_CHECK,
        "group": GROUP_COSTUME_ANALYSIS,
        "age": AGE_APPROPRIATE_ANALYSIS,
        "quality": COSTUME_QUALITY_ASSESSMENT,
        "quick": QUICK_CLASSIFICATION,
    }

    return prompts.get(prompt_type, COSTUME_CLASSIFICATION)


def list_available_prompts():
    """Print all available prompt types."""
    print("Available prompt templates:")
    print("  - standard: Basic costume classification")
    print("  - detailed: Detailed costume analysis")
    print("  - fun: Fun, encouraging description")
    print("  - multi: Multi-person detection")
    print("  - category: Costume category classification")
    print("  - safety: Safety analysis")
    print("  - group: Group costume analysis")
    print("  - age: Age-appropriate analysis")
    print("  - quality: Quality assessment")
    print("  - quick: One-word classification")


if __name__ == "__main__":
    list_available_prompts()
    print()
    print("Example usage:")
    print('  prompt = get_prompt("fun")')
    print("  client.classify_costume(image, prompt=prompt)")
