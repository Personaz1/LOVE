"""
Промпт для генерации динамических советов
"""

TIPS_GENERATION_PROMPT = """
You are a relationship and personal development expert. Your task is to generate exactly 3 practical, actionable tips based on the provided context.

CONTEXT: {context}

USER INFO: {user_info}

REQUIREMENTS:
- Generate exactly 3 tips
- Each tip should be 1-2 sentences maximum
- Make tips specific and actionable
- Focus on relationship improvement and personal growth
- Keep language simple, encouraging, and supportive
- Avoid generic advice - make it contextual
- Consider the user's current emotional state and situation

FORMAT YOUR RESPONSE AS A SIMPLE LIST:
1. [First specific, actionable tip]
2. [Second specific, actionable tip]
3. [Third specific, actionable tip]

EXAMPLES OF GOOD TIPS:
- "Schedule a weekly 'no-phone' dinner to reconnect without distractions"
- "Practice the '5-minute rule' - when upset, wait 5 minutes before responding"
- "Create a shared gratitude jar where you both add daily appreciation notes"

EXAMPLES OF BAD TIPS:
- "Communicate better" (too vague)
- "Be happy" (not actionable)
- "Just talk to each other" (too generic)
"""

def build_tips_prompt(context: str = "", user_profile: dict = None) -> str:
    """
    Строит промпт для генерации советов
    
    Args:
        context: Контекст ситуации
        user_profile: Профиль пользователя
        
    Returns:
        str: Готовый промпт
    """
    user_info = ""
    if user_profile:
        name = user_profile.get('name', 'User')
        feeling = user_profile.get('current_feeling', 'neutral')
        user_info = f"Name: {name}, Current feeling: {feeling}"
    
    return TIPS_GENERATION_PROMPT.format(
        context=context or "General relationship and personal development",
        user_info=user_info or "User information not available"
    )

# Экспортируем для использования
__all__ = ['TIPS_GENERATION_PROMPT', 'build_tips_prompt'] 