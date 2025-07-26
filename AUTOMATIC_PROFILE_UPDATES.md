# 🤖 Automatic Profile Updates - Dr. Harmony

## Overview
Dr. Harmony now automatically understands user emotions and relationship dynamics from natural language and updates profiles accordingly.

## 🧠 Automatic Detection Features

### 1. **Feelings Detection**
Model automatically detects emotions in both Russian and English:

**Russian Phrases:**
- "я плохо себя чувствую" → "Feeling unwell"
- "грустно/грустная/грустный" → "Sad"
- "счастлива/счастлив/счастливый" → "Happy"
- "радостно/радостная/радостный" → "Joyful"
- "устала/устал/усталый/усталая" → "Tired"
- "злая/злой/злюсь" → "Angry"
- "нервничаю/волнуюсь/тревожно" → "Anxious"
- "спокойно/спокойная/спокойный" → "Calm"

**English Phrases:**
- "I feel bad" → "Feeling bad"
- "I'm sad" → "Sad"
- "I'm happy" → "Happy"
- "I'm tired" → "Tired"
- "I'm angry" → "Angry"
- "I'm nervous" → "Nervous"
- "I'm anxious" → "Anxious"
- "I'm calm" → "Calm"
- "feeling down" → "Feeling down"
- "feeling great" → "Feeling great"
- "feeling good" → "Feeling good"

### 2. **Relationship Status Detection**
Automatically detects relationship dynamics:

**Russian Phrases:**
- "мы ссоримся/мы ругаемся/мы в ссоре" → "Having conflicts"
- "все плохо" → "Relationship difficulties"
- "все хорошо/все отлично" → "Relationship is good/great"
- "чувствую себя одиноко/одиноким/одинокой" → "Feeling lonely"
- "мы близки" → "Feeling close"
- "мы далеки" → "Feeling distant"

**English Phrases:**
- "we're fighting/arguing" → "Having conflicts"
- "things are bad" → "Relationship difficulties"
- "things are good/great" → "Relationship is good/great"
- "feeling lonely" → "Feeling lonely"
- "feeling close" → "Feeling close"
- "feeling distant" → "Feeling distant"

### 3. **Automatic Hidden Notes**
Model creates private observations when users mention:

**Topics that trigger hidden notes:**
- Work/Career: "работа", "work", "job", "карьера", "career"
- Family: "семья", "family", "родители", "parents"
- Social: "друзья", "friends", "общение", "communication"
- Health: "здоровье", "health", "болезнь", "sick"
- Stress: "стресс", "stress", "усталость", "exhaustion"
- Plans: "планы", "plans", "цели", "goals"
- Dreams: "мечты", "dreams", "желания", "desires"
- Fears: "страхи", "fears", "тревоги", "anxieties"
- Emotions: "радость", "joy", "счастье", "happiness", "грусть", "sadness", "печаль", "grief"

## 🔧 Technical Implementation

### Updated Files:
1. **`prompts/psychologist_prompt.py`** - Enhanced system prompt with automatic update instructions
2. **`ai_client.py`** - Added automatic detection logic in `_process_response_for_functions()`

### Key Functions:
```python
# Automatic feeling detection
update_current_feeling(username, feeling)

# Automatic relationship status detection  
update_relationship_status(username, status)

# Automatic hidden notes creation
update_hidden_profile(username, hidden_note)

# Profile updates
update_user_profile(username, new_profile)

# Relationship insights
add_relationship_insight(insight)
```

## 🎯 User Experience

### Natural Interaction:
- User: "я плохо себя чувствую"
- Model: Responds naturally while automatically updating "current_feeling" to "Feeling unwell"
- No announcement of the update - seamless experience

### Automatic Context Building:
- Model observes patterns and creates hidden notes
- Builds understanding of user over time
- Provides more personalized advice

### Multi-language Support:
- Works in both Russian and English
- Detects emotions regardless of language
- Maintains context across languages

## 📊 Example Workflow

1. **User writes:** "Сегодня я очень устала от работы"
2. **Model detects:** "устала" → "Tired"
3. **Model updates:** `current_feeling = "Tired"`
4. **Model detects:** "работа" → Work-related topic
5. **Model creates hidden note:** "User shared about работа: Сегодня я очень устала от работы... (observed at 2025-01-26 17:45)"
6. **Model responds:** Natural response about being tired from work
7. **Result:** Profile updated automatically, hidden note created, user gets natural response

## 🚀 Benefits

- **Seamless Experience:** No need for explicit commands
- **Natural Language:** Works with everyday conversation
- **Automatic Learning:** Model builds understanding over time
- **Bilingual:** Works in Russian and English
- **Contextual:** Creates relevant hidden notes
- **Personalized:** Better advice based on updated profiles

## 🔮 Future Enhancements

- More emotion detection patterns
- Relationship phase detection
- Communication style analysis
- Conflict pattern recognition
- Growth milestone tracking 