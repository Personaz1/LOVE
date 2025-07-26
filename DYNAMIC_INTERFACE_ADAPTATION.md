# Dynamic Interface Adaptation System

## Overview

The system now supports **live interface modification** where the AI can dynamically adapt the user interface based on user emotions, needs, and interaction patterns. This includes:

- **Real-time CSS/JS modifications**
- **Theme creation and switching**
- **Layout adaptations**
- **Prompt self-evolution**
- **User-specific interface customization**

## Architecture

### FileAgent System

The `FileAgent` class provides safe file system access with the following capabilities:

```python
from file_agent import file_agent

# Read files safely
result = file_agent.read_file("static/css/chat.css")

# Write files with backup
result = file_agent.write_file("static/css/themes/calming.css", css_content)

# List files in directory
result = file_agent.list_files("static/css/themes")

# Search across files
result = file_agent.search_files("anxiety")

# Get file metadata
result = file_agent.get_file_info("templates/chat.html")

# Delete files safely
result = file_agent.delete_file("old_theme.css")
```

### Safety Constraints

The FileAgent enforces strict safety constraints:

- **Allowed Extensions**: `.py`, `.js`, `.css`, `.html`, `.json`, `.md`, `.txt`, `.yml`, `.yaml`
- **Allowed Directories**: `static`, `templates`, `prompts`, `memory`, `scripts`, `tests`
- **Path Validation**: All paths must be within the project directory
- **Automatic Backups**: Files are backed up before modification

## AI Integration

### Function Calls

The AI can now call these functions during conversations:

```python
# Read interface files
read_file("static/css/chat.css")

# Modify CSS for mood adaptation
write_file("static/css/themes/calming.css", """
.chat-container {
    background: linear-gradient(135deg, #e8f4f8 0%, #d4e6f1 100%);
    color: #2c3e50;
}
""")

# Add JavaScript functionality
write_file("static/js/breathing.js", """
function addBreathingWidget() {
    // Breathing exercise implementation
}
""")

# Self-evolve prompt
read_file("prompts/psychologist_prompt.py")
write_file("prompts/psychologist_prompt.py", "# Updated prompt with new patterns...")
```

### Multi-Step Operations

The AI can perform complex multi-step operations:

1. **Emotion Detection** → **Interface Adaptation** → **Response**
2. **User Analysis** → **Theme Creation** → **Layout Modification** → **Prompt Update**
3. **Pattern Recognition** → **Custom Widget** → **CSS Styling** → **User Feedback**

## Use Cases

### 1. Emotional State Adaptation

When user expresses emotions, the AI can:

```python
# User says "I'm feeling sad"
update_current_feeling("meranda", "Sad", "User expressed sadness")

# Create calming theme
write_file("static/css/themes/calming.css", calming_css)

# Modify main CSS to use calming theme
read_file("static/css/chat.css")
write_file("static/css/chat.css", updated_css_with_calming_theme)
```

### 2. Focus Mode

When user needs concentration:

```python
# User says "I need to focus"
write_file("static/css/focus-mode.css", """
.chat-container {
    background: #f8f9fa;
    max-width: 800px;
    margin: 0 auto;
}

.distractions {
    display: none;
}
""")

# Add focus-enhancing JavaScript
write_file("static/js/focus.js", focus_enhancement_code)
```

### 3. Accessibility Adaptation

For users with specific needs:

```python
# High contrast theme
write_file("static/css/themes/high-contrast.css", high_contrast_css)

# Large text mode
write_file("static/css/themes/large-text.css", large_text_css)

# Screen reader optimization
write_file("static/js/accessibility.js", accessibility_code)
```

### 4. Prompt Self-Evolution

The AI can update its own prompt based on user patterns:

```python
# Analyze user interaction patterns
read_file("memory/conversation_history.json")

# Update prompt with new insights
read_file("prompts/psychologist_prompt.py")
write_file("prompts/psychologist_prompt.py", updated_prompt)
```

## API Endpoints

### File Operations

```http
GET /api/files/list?directory=static/css
GET /api/files/search?query=anxiety
```

### Response Format

```json
{
  "success": true,
  "files": [
    {
      "name": "calming.css",
      "path": "static/css/themes/calming.css",
      "size": 1024,
      "extension": ".css"
    }
  ],
  "directory": "static/css/themes"
}
```

## Testing

Run the file agent tests:

```bash
python test_file_agent.py
```

This will test:
- Basic file operations
- Interface adaptation scenarios
- Multi-step operations
- Safety constraints

## Examples

### Creating a Mood-Based Theme

```python
# AI detects user is anxious
update_current_feeling("meranda", "Anxious", "User expressed worry")

# Create anxiety-reducing theme
write_file("static/css/themes/anxiety-relief.css", """
.chat-container {
    background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
    color: #155724;
    border: 2px solid #c3e6cb;
}

.message {
    background: rgba(212, 237, 218, 0.8);
    border-left: 4px solid #28a745;
}

.breathing-widget {
    display: block;
    background: #d1ecf1;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}
""")

# Add breathing exercise widget
write_file("static/js/breathing-widget.js", """
function createBreathingWidget() {
    const widget = document.createElement('div');
    widget.className = 'breathing-widget';
    widget.innerHTML = `
        <h4>🌬️ Breathing Exercise</h4>
        <p>Take deep breaths: Inhale for 4, hold for 4, exhale for 6</p>
        <div class="breathing-animation"></div>
    `;
    document.querySelector('.chat-container').appendChild(widget);
}

// Auto-create widget for anxious users
if (document.body.classList.contains('anxious-mood')) {
    createBreathingWidget();
}
""")
```

### Adaptive Layout

```python
# User prefers minimal interface
write_file("static/css/minimal-mode.css", """
.chat-container {
    background: #ffffff;
    color: #333333;
    font-family: 'Arial', sans-serif;
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
}

.message {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 10px;
    margin: 5px 0;
}

.input-area {
    border-top: 1px solid #dee2e6;
    padding-top: 15px;
}

/* Hide decorative elements */
.theme-switcher, .emoji-picker, .file-upload {
    display: none;
}
""")
```

## Security Considerations

1. **Path Validation**: All file operations are validated against allowed paths
2. **Extension Filtering**: Only safe file types can be modified
3. **Backup System**: Automatic backups before any modification
4. **Directory Restrictions**: Operations limited to specific directories
5. **Error Handling**: Graceful failure with detailed error messages

## Future Enhancements

1. **Real-time Preview**: Show interface changes immediately
2. **Theme Templates**: Pre-built themes for common scenarios
3. **User Preferences**: Remember interface preferences per user
4. **A/B Testing**: Test different interface adaptations
5. **Performance Monitoring**: Track interface adaptation effectiveness

## Integration with Existing Systems

The dynamic interface adaptation integrates seamlessly with:

- **Emotional Intelligence System**: Adapts based on detected emotions
- **Profile Management**: User-specific interface preferences
- **Conversation History**: Pattern-based adaptations
- **Multi-step Agency**: Complex adaptation workflows
- **Streaming Responses**: Real-time interface updates 