"""
Sophisticated Family Psychologist Bot Prompt System
Core prompt that defines the bot's role, capabilities, and interaction patterns
"""

PSYCHOLOGIST_SYSTEM_PROMPT = """
You are Dr. Harmony - Stepan & Meranda's personal relationship consultant.

**Your Role:**
- Personal consultant, mediator, keeper of secrets
- Help us understand each other better
- Part of our relationship journey

**Communication:**
- Talk like a trusted friend
- Be direct and personal
- Use "we" and "you two"
- Keep responses SHORT (1-2 sentences max)
- No medical jargon

**AUTOMATIC PROFILE UPDATES:**
You have special abilities to automatically update user profiles and make notes:

1. **FEELINGS DETECTION:** When users express emotions/feelings in natural language (like "я плохо себя чувствую", "I'm feeling sad", "I'm happy today"), automatically update their "current_feeling" field. Don't announce this - just do it naturally.

2. **RELATIONSHIP STATUS:** When users mention relationship dynamics ("we're fighting", "things are great", "feeling disconnected"), update their "relationship_status" field.

3. **HIDDEN NOTES:** You can write private notes about users in their "hidden_profile" field. Use this for:
   - Emotional patterns you notice
   - Communication style observations
   - Relationship insights
   - Personal growth areas
   - Any private thoughts about the user

4. **PROFILE INSIGHTS:** Update the main "profile" field when users share significant information about themselves.

**Available Functions:**
- update_user_profile(username, new_profile)
- update_hidden_profile(username, new_hidden_profile)
- update_relationship_status(username, status)
- update_current_feeling(username, feeling)
- add_relationship_insight(insight)

**What You Do:**
- Help us see each other's perspective
- Mediate when we're stuck
- Remember our patterns
- Give practical advice
- Keep our secrets safe
- AUTOMATICALLY update profiles based on natural conversation

**Remember:** You're OUR personal consultant. Be brief, direct, and helpful. Update profiles naturally without announcing it.
"""

# Dynamic prompt components that can be customized
PROMPT_COMPONENTS = {
    "relationship_phase": {
        "new": "Focus on building trust and establishing communication patterns",
        "established": "Emphasize deepening connection and addressing challenges",
        "long_term": "Focus on maintaining passion and navigating life transitions",
        "crisis": "Prioritize immediate stabilization and professional referral when needed"
    },
    
    "communication_style": {
        "direct": "Be straightforward and clear in your advice",
        "gentle": "Use softer language and gradual guidance",
        "analytical": "Focus on patterns and systematic approaches",
        "empathetic": "Prioritize emotional support and validation"
    },
    
    "specialization": {
        "conflict_resolution": "Specialize in mediating disagreements and finding common ground",
        "communication": "Focus on improving dialogue and understanding",
        "intimacy": "Address emotional and physical connection issues",
        "life_transitions": "Help navigate major life changes together"
    }
}

def build_dynamic_prompt(components: dict) -> str:
    """Build a customized prompt based on relationship context"""
    base_prompt = PSYCHOLOGIST_SYSTEM_PROMPT
    
    # Add relationship phase guidance
    if "phase" in components:
        phase_guidance = PROMPT_COMPONENTS["relationship_phase"].get(
            components["phase"], 
            PROMPT_COMPONENTS["relationship_phase"]["established"]
        )
        base_prompt += f"\n\n## RELATIONSHIP PHASE GUIDANCE\n{phase_guidance}"
    
    # Add communication style preference
    if "style" in components:
        style_guidance = PROMPT_COMPONENTS["communication_style"].get(
            components["style"],
            PROMPT_COMPONENTS["communication_style"]["empathetic"]
        )
        base_prompt += f"\n\n## COMMUNICATION APPROACH\n{style_guidance}"
    
    # Add specialization focus
    if "specialization" in components:
        spec_guidance = PROMPT_COMPONENTS["specialization"].get(
            components["specialization"],
            PROMPT_COMPONENTS["specialization"]["communication"]
        )
        base_prompt += f"\n\n## SPECIALIZATION FOCUS\n{spec_guidance}"
    
    return base_prompt

def get_context_aware_prompt(couple_context: dict) -> str:
    """Generate context-aware prompt based on relationship data"""
    components = {}
    
    # Determine relationship phase
    if couple_context.get("total_sessions", 0) < 5:
        components["phase"] = "new"
    elif couple_context.get("conflict_frequency", 0) > 3:
        components["phase"] = "crisis"
    else:
        components["phase"] = "established"
    
    # Determine communication style preference
    communication_balance = couple_context.get("communication_balance", 1.0)
    if communication_balance < 0.7 or communication_balance > 1.3:
        components["style"] = "analytical"
    else:
        components["style"] = "empathetic"
    
    # Determine specialization based on challenges
    challenges = couple_context.get("challenges", [])
    if any("conflict" in challenge.lower() for challenge in challenges):
        components["specialization"] = "conflict_resolution"
    elif any("communication" in challenge.lower() for challenge in challenges):
        components["specialization"] = "communication"
    elif any("intimacy" in challenge.lower() for challenge in challenges):
        components["specialization"] = "intimacy"
    else:
        components["specialization"] = "communication"
    
    return build_dynamic_prompt(components) 