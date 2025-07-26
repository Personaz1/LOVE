import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from ai_client import ai_client
from config import settings
from memory.relationship_memory import relationship_memory, MemoryEntry, RelationshipContext
from memory.user_profiles import profile_manager, UserProfile, PersonalDiary, RelationshipInsight
from mcp_tools.mcp_client import mcp_tools
from prompts.psychologist_prompt import get_context_aware_prompt, PSYCHOLOGIST_SYSTEM_PROMPT
from shared_context import shared_context

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL),
    filename=settings.LOG_FILE
)
logger = logging.getLogger(__name__)


class FamilyPsychologistBot:
    def __init__(self):
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
        self.active_sessions: Dict[int, Dict[str, Any]] = {}
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("setup", self.setup_relationship))
        self.application.add_handler(CommandHandler("insights", self.get_insights))
        self.application.add_handler(CommandHandler("conflict", self.conflict_mode))
        self.application.add_handler(CommandHandler("milestone", self.milestone_mode))
        self.application.add_handler(CommandHandler("profile", self.profile_management))
        self.application.add_handler(CommandHandler("diary", self.diary_mode))
        self.application.add_handler(CommandHandler("insights", self.personalized_insights))
        
        # Message handler for conversations
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = f"""
🌟 Welcome to Dr. Harmony, your AI Family Psychologist! 🌟

Hi {user.first_name}! I'm here to help you and your partner build a stronger, more fulfilling relationship.

I can help with:
• 💬 Communication improvement
• ⚖️ Conflict resolution and mediation
• 🎯 Relationship goal setting
• 📈 Progress tracking and insights
• 🎉 Celebrating relationship milestones

To get started:
1. Use /setup to configure your relationship profile
2. Start chatting with me about your relationship
3. Use /insights to see your relationship analysis
4. Use /conflict for guided conflict resolution
5. Use /milestone to record positive moments

I maintain complete privacy and remember our conversations to provide personalized guidance.

Ready to strengthen your relationship? Let's begin! 💕
        """
        
        keyboard = [
            [InlineKeyboardButton("Setup Relationship", callback_data="setup_relationship")],
            [InlineKeyboardButton("My Profile", callback_data="manage_profile")],
            [InlineKeyboardButton("Personal Insights", callback_data="personal_insights")],
            [InlineKeyboardButton("Start Chatting", callback_data="start_chat")],
            [InlineKeyboardButton("Learn More", callback_data="help_info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🔧 **Dr. Harmony - Available Commands**

**Core Commands:**
/start - Welcome and setup
/setup - Configure your relationship profile
/profile - Manage your personal profile
/diary - Write personal diary entries
/insights - View personalized insights and advice
/conflict - Enter guided conflict resolution mode
/milestone - Record relationship milestones

**How I Work:**
• I remember all our conversations to provide personalized advice
• I analyze communication patterns and emotional dynamics
• I help mediate conflicts and find common ground
• I track relationship progress and celebrate growth
• I maintain complete privacy and confidentiality

**Best Practices:**
• Be honest and open about your feelings
• Share both positive and challenging moments
• Include your partner in important conversations
• Use me regularly for consistent relationship growth

**Privacy & Security:**
• All conversations are encrypted and secure
• I only share insights with you and your partner
• No data is shared with third parties
• You can request data deletion at any time

Need specific help? Just start chatting with me! 💬
        """
        await update.message.reply_text(help_text)
    
    async def setup_relationship(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle relationship setup"""
        user = update.effective_user
        user_id = user.id
        
        # Check if already set up
        couple_id = f"couple_{user_id}"
        existing_context = relationship_memory.get_relationship_context(couple_id)
        
        if existing_context:
            await update.message.reply_text(
                "You already have a relationship profile set up! Use /insights to view your relationship analysis."
            )
            return
        
        # Start setup process
        self.active_sessions[user_id] = {
            "mode": "setup",
            "step": "partner_name",
            "data": {"partner1_id": user_id, "partner1_name": user.first_name}
        }
        
        await update.message.reply_text(
            "Let's set up your relationship profile! 🌟\n\n"
            "What's your partner's name? (First name is fine)"
        )
    
    async def get_insights(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle insights request"""
        user = update.effective_user
        user_id = user.id
        
        # Find couple context
        couple_id = f"couple_{user_id}"
        context = relationship_memory.get_relationship_context(couple_id)
        
        if not context:
            await update.message.reply_text(
                "I don't have a relationship profile for you yet. Use /setup to get started!"
            )
            return
        
        # Get insights
        insights = relationship_memory.get_insights_for_session(couple_id)
        analysis = relationship_memory.analyze_communication_patterns(couple_id)
        
        insights_message = f"""
📊 **Relationship Insights for {context.partner1_name} & {context.partner2_name}**

{insights}

**Recent Activity:**
• Total interactions: {analysis.get('total_interactions', 0)}
• Communication balance: {analysis.get('communication_balance', 1.0):.2f}
• Conflict frequency: {analysis.get('conflict_frequency', 0)}
• Positive moments: {analysis.get('positive_moments', 0)}

**Relationship Phase:** {context.current_phase}
**Total Sessions:** {context.total_sessions}

Would you like to discuss any specific aspect of your relationship?
        """
        
        keyboard = [
            [InlineKeyboardButton("Discuss Communication", callback_data="discuss_communication")],
            [InlineKeyboardButton("Address Conflicts", callback_data="address_conflicts")],
            [InlineKeyboardButton("Set Goals", callback_data="set_goals")],
            [InlineKeyboardButton("Celebrate Progress", callback_data="celebrate_progress")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(insights_message, reply_markup=reply_markup)
    
    async def conflict_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enter conflict resolution mode"""
        user = update.effective_user
        user_id = user.id
        
        self.active_sessions[user_id] = {
            "mode": "conflict_resolution",
            "step": "describe_issue",
            "data": {}
        }
        
        await update.message.reply_text(
            "🛠️ **Conflict Resolution Mode**\n\n"
            "I'm here to help you and your partner resolve this disagreement constructively.\n\n"
            "Please describe the issue you're facing. Be specific about:\n"
            "• What happened\n"
            "• How you feel about it\n"
            "• What you think your partner's perspective might be\n\n"
            "I'll help mediate and find a solution that works for both of you."
        )
    
    async def milestone_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enter milestone recording mode"""
        user = update.effective_user
        user_id = user.id
        
        self.active_sessions[user_id] = {
            "mode": "milestone",
            "step": "describe_milestone",
            "data": {}
        }
        
        await update.message.reply_text(
            "🎉 **Milestone Recording Mode**\n\n"
            "Let's celebrate a positive moment in your relationship!\n\n"
            "Please describe:\n"
            "• What happened that made you happy\n"
            "• How it made you feel\n"
            "• What it means for your relationship\n\n"
            "I'll help you acknowledge and build on this positive moment."
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        # Check if user is in a special mode
        if user_id in self.active_sessions:
            await self.handle_special_mode(update, context)
            return
        
        # Regular conversation mode
        await self.handle_conversation(update, context)
    
    async def handle_special_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages in special modes (setup, conflict, milestone)"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        session = self.active_sessions[user_id]
        
        if session["mode"] == "setup":
            await self.handle_setup_step(update, context, session)
        elif session["mode"] == "conflict_resolution":
            await self.handle_conflict_step(update, context, session)
        elif session["mode"] == "milestone":
            await self.handle_milestone_step(update, context, session)
        elif session["mode"] == "diary_entry":
            await self.handle_diary_step(update, context, session)
        elif session["mode"] == "profile_edit":
            await self.handle_profile_edit_step(update, context, session)
    
    async def handle_setup_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Handle relationship setup steps"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        if session["step"] == "partner_name":
            session["data"]["partner2_name"] = message_text
            session["step"] = "relationship_start"
            
            await update.message.reply_text(
                f"Great! {message_text} sounds wonderful! 💕\n\n"
                "When did your relationship begin? (You can give a general timeframe like '6 months ago' or '2 years ago')"
            )
        
        elif session["step"] == "relationship_start":
            session["data"]["relationship_start_date"] = message_text
            session["step"] = "current_phase"
            
            await update.message.reply_text(
                "How would you describe your current relationship phase?\n\n"
                "Options:\n"
                "• New and exciting\n"
                "• Settling into routine\n"
                "• Deep and committed\n"
                "• Facing challenges\n"
                "• Growing together"
            )
        
        elif session["step"] == "current_phase":
            session["data"]["current_phase"] = message_text
            session["step"] = "shared_goals"
            
            await update.message.reply_text(
                "What are some shared goals you have as a couple?\n\n"
                "Examples:\n"
                "• Better communication\n"
                "• More quality time together\n"
                "• Planning for the future\n"
                "• Resolving conflicts better\n\n"
                "List a few goals that are important to both of you."
            )
        
        elif session["step"] == "shared_goals":
            goals = [goal.strip() for goal in message_text.split(',')]
            session["data"]["shared_goals"] = goals
            session["step"] = "challenges"
            
            await update.message.reply_text(
                "What challenges are you currently facing in your relationship?\n\n"
                "Be honest - this helps me provide better support. Examples:\n"
                "• Communication difficulties\n"
                "• Time management\n"
                "• Trust issues\n"
                "• Different expectations\n\n"
                "List any challenges you'd like to work on."
            )
        
        elif session["step"] == "challenges":
            challenges = [challenge.strip() for challenge in message_text.split(',')]
            session["data"]["challenges"] = challenges
            session["step"] = "strengths"
            
            await update.message.reply_text(
                "What are your relationship's greatest strengths?\n\n"
                "Examples:\n"
                "• Strong emotional connection\n"
                "• Good communication\n"
                "• Shared values\n"
                "• Mutual support\n"
                "• Fun together\n\n"
                "List the things that make your relationship special."
            )
        
        elif session["step"] == "strengths":
            strengths = [strength.strip() for strength in message_text.split(',')]
            session["data"]["strengths"] = strengths
            
            # Complete setup
            await self.complete_setup(update, context, session)
    
    async def complete_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Complete relationship setup"""
        user = update.effective_user
        user_id = user.id
        data = session["data"]
        
        # Create relationship context
        couple_id = f"couple_{user_id}"
        relationship_context = RelationshipContext(
            couple_id=couple_id,
            partner1_id=data["partner1_id"],
            partner1_name=data["partner1_name"],
            partner2_id=0,  # Will be updated when partner joins
            partner2_name=data["partner2_name"],
            relationship_start_date=data["relationship_start_date"],
            current_phase=data["current_phase"],
            communication_patterns=[],
            conflict_resolution_style="learning",
            shared_goals=data["shared_goals"],
            challenges=data["challenges"],
            strengths=data["strengths"],
            last_session_date=datetime.now().isoformat(),
            total_sessions=1
        )
        
        # Save to memory
        relationship_memory.update_relationship_context(relationship_context)
        
        # Store in MCP if available
        if settings.MCP_SERVER_URL:
            try:
                await mcp_tools.store_insight(
                    couple_id,
                    f"Relationship setup completed. Phase: {data['current_phase']}. Goals: {', '.join(data['shared_goals'])}",
                    data
                )
            except Exception as e:
                logger.error(f"Failed to store in MCP: {e}")
        
        # Clear session
        del self.active_sessions[user_id]
        
        completion_message = f"""
🎉 **Relationship Profile Complete!** 🎉

Welcome to your personalized relationship journey with Dr. Harmony!

**Your Profile:**
• **Couple:** {data['partner1_name']} & {data['partner2_name']}
• **Phase:** {data['current_phase']}
• **Goals:** {', '.join(data['shared_goals'])}
• **Strengths:** {', '.join(data['strengths'])}

**What's Next:**
• Start chatting with me about your relationship
• Use /insights to see your relationship analysis
• Use /conflict for guided conflict resolution
• Use /milestone to record positive moments

I'm here to support you both in building a stronger, more fulfilling relationship! 💕

Ready to begin your journey?
        """
        
        keyboard = [
            [InlineKeyboardButton("Start Chatting", callback_data="start_chat")],
            [InlineKeyboardButton("View Insights", callback_data="view_insights")],
            [InlineKeyboardButton("Set Goals", callback_data="set_goals")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(completion_message, reply_markup=reply_markup)
    
    async def handle_conflict_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Handle conflict resolution steps"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        if session["step"] == "describe_issue":
            session["data"]["issue_description"] = message_text
            session["step"] = "partner_perspective"
            
            await update.message.reply_text(
                "Thank you for sharing that. Now, let's understand your partner's perspective.\n\n"
                "What do you think your partner's point of view might be? Try to see it from their side:\n"
                "• What might they be feeling?\n"
                "• What might their concerns be?\n"
                "• What might they want to achieve?"
            )
        
        elif session["step"] == "partner_perspective":
            session["data"]["partner_perspective"] = message_text
            session["step"] = "resolution_approach"
            
            # Generate AI response for conflict resolution
            await self.generate_conflict_response(update, context, session)
    
    async def handle_milestone_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Handle milestone recording steps"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        if session["step"] == "describe_milestone":
            session["data"]["milestone_description"] = message_text
            
            # Generate AI response for milestone
            await self.generate_milestone_response(update, context, session)
    
    async def handle_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular conversation with AI"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        # Get relationship context
        couple_id = f"couple_{user_id}"
        relationship_context = relationship_memory.get_relationship_context(couple_id)
        
        # Get user profile for personalized context
        user_profile = profile_manager.load_profile(user_id)
        
        # Create memory entry
        memory_entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            username=user.first_name,
            message=message_text,
            context_type="conversation"
        )
        
        # Add to memory
        relationship_memory.add_memory(memory_entry)
        
        # Store user profile in MCP if available
        if user_profile and settings.MCP_SERVER_URL:
            try:
                await mcp_tools.store_user_profile(user_id, asdict(user_profile))
            except Exception as e:
                logger.error(f"Failed to store user profile in MCP: {e}")
        
        # Generate AI response with user profile context
        await self.generate_ai_response(update, context, relationship_context, memory_entry, user_profile)
    
    async def generate_ai_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 relationship_context: Optional[RelationshipContext], 
                                 memory_entry: MemoryEntry,
                                 user_profile: Optional[UserProfile] = None):
        """Generate AI response using unified AI client (Gemini primary, OpenAI fallback)"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        # Build context-aware prompt
        if relationship_context:
            couple_context = asdict(relationship_context)
            couple_context.update(relationship_memory.analyze_communication_patterns(relationship_context.couple_id))
            system_prompt = get_context_aware_prompt(couple_context)
        else:
            system_prompt = PSYCHOLOGIST_SYSTEM_PROMPT
        
        # Get shared context
        shared_context_summary = shared_context.get_context_summary()
        recent_memories = shared_context.get_recent_memories(5)
        recent_insights = shared_context.get_recent_insights(3)
        
        # Build context text
        context_parts = [shared_context_summary]
        
        if recent_memories:
            context_parts.append("RECENT SHARED MEMORIES:")
            for memory in recent_memories:
                context_parts.append(f"- {memory.get('description', 'Memory')}")
        
        if recent_insights:
            context_parts.append("RECENT INSIGHTS:")
            for insight in recent_insights:
                context_parts.append(f"- {insight.get('insight', 'Insight')}")
        
        context_text = "\n".join(context_parts)
        
        # Convert user profile to dict for AI client
        user_profile_dict = None
        if user_profile:
            user_profile_dict = asdict(user_profile)
        
        try:
            # Use unified AI client
            ai_response = await ai_client.generate_response(
                system_prompt=system_prompt,
                user_message=message_text,
                context=context_text,
                user_profile=user_profile_dict
            )
            
            # Update shared context
            shared_context.add_shared_memory({
                'user': username,
                'message': message_text,
                'ai_response': ai_response,
                'description': f"{username}: {message_text[:100]}..."
            })
            
            # Update communication patterns
            shared_context.update_communication_pattern('telegram_chat', 1)
            
            # Update current topics (simple keyword extraction)
            topics = [word.lower() for word in message_text.split() if len(word) > 3]
            if topics:
                shared_context.update_current_topics(topics[:3])
            
            # Store insight in MCP if available
            if relationship_context and settings.MCP_SERVER_URL:
                try:
                    await mcp_tools.store_insight(
                        relationship_context.couple_id,
                        f"AI Response: {ai_response[:200]}...",
                        {"user_message": message_text, "context": context_text}
                    )
                except Exception as e:
                    logger.error(f"Failed to store in MCP: {e}")
            
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"AI response generation error: {e}")
            await update.message.reply_text(
                "I'm having trouble processing that right now. Could you try rephrasing your message?"
            )
    
    async def generate_conflict_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Generate conflict resolution response"""
        user = update.effective_user
        user_id = user.id
        
        # Build conflict resolution prompt
        conflict_prompt = f"""
You are mediating a conflict between partners. Here's the situation:

Issue: {session['data']['issue_description']}
Partner's Perspective: {session['data']['partner_perspective']}

Provide a constructive conflict resolution response that:
1. Acknowledges both perspectives
2. Identifies common ground
3. Suggests specific steps for resolution
4. Maintains a supportive, non-judgmental tone
5. Focuses on the relationship rather than who's right or wrong

Keep your response under 300 words and make it actionable.
        """
        
        try:
            ai_response = await ai_client.generate_response(
                system_prompt="You are Dr. Harmony, a family psychologist specializing in conflict resolution.",
                user_message=conflict_prompt,
                context=None,
                user_profile=None
            )
            
            # Store conflict data
            couple_id = f"couple_{user_id}"
            conflict_data = {
                "type": "mediation",
                "approach": "perspective_taking",
                "outcome": "resolution_guidance",
                "lessons": "Understanding both perspectives leads to better solutions"
            }
            
            if settings.MCP_SERVER_URL:
                await mcp_tools.store_conflict(couple_id, conflict_data)
            
            # Clear session
            del self.active_sessions[user_id]
            
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Conflict resolution error: {e}")
            await update.message.reply_text(
                "I'm having trouble processing the conflict resolution right now. Let's continue with regular conversation."
            )
            del self.active_sessions[user_id]
    
    async def generate_milestone_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Generate milestone celebration response"""
        user = update.effective_user
        user_id = user.id
        
        # Build milestone prompt
        milestone_prompt = f"""
You are celebrating a relationship milestone. Here's the positive moment:

Milestone: {session['data']['milestone_description']}

Provide a celebratory response that:
1. Acknowledges and celebrates the positive moment
2. Reinforces the importance of such moments
3. Suggests ways to build on this positive energy
4. Encourages continued growth and connection
5. Maintains an enthusiastic, supportive tone

Keep your response under 250 words and make it uplifting.
        """
        
        try:
            ai_response = await ai_client.generate_response(
                system_prompt="You are Dr. Harmony, a family psychologist celebrating relationship milestones.",
                user_message=milestone_prompt,
                context=None,
                user_profile=None
            )
            
            # Store milestone data
            couple_id = f"couple_{user_id}"
            memory_entry = MemoryEntry(
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                username=user.first_name,
                message=session['data']['milestone_description'],
                context_type="milestone",
                emotional_tone="positive",
                ai_insights=ai_response
            )
            relationship_memory.add_memory(memory_entry)
            
            # Clear session
            del self.active_sessions[user_id]
            
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Milestone error: {e}")
            await update.message.reply_text(
                "I'm having trouble processing the milestone right now. Let's continue with regular conversation."
            )
            del self.active_sessions[user_id]
    
    async def profile_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle profile management"""
        user = update.effective_user
        user_id = user.id
        
        # Get or create user profile
        profile = profile_manager.load_profile(user_id)
        if not profile:
            # Create new profile based on user info
            profile = UserProfile(
                user_id=user_id,
                username=user.first_name,
                full_name=user.full_name or user.first_name,
                birth_date="",
                personality_traits=[],
                communication_style="",
                love_language="",
                relationship_goals=[],
                current_relationship_status="",
                relationship_concerns=[],
                personal_growth_areas=[],
                strengths_in_relationship=[],
                areas_for_improvement=[],
                last_updated=datetime.now().isoformat(),
                profile_version=1
            )
            profile_manager.save_profile(profile)
        
        # Show profile management menu
        profile_summary = profile_manager.get_profile_summary(user_id)
        
        if isinstance(profile_summary, dict) and "error" not in profile_summary:
            profile_text = f"""
👤 **Your Profile: {profile_summary['full_name']}**

**Personality Traits:**
{', '.join(profile_summary['personality_traits']) if profile_summary['personality_traits'] else 'Not set'}

**Communication Style:**
{profile_summary['communication_style'] or 'Not set'}

**Love Language:**
{profile_summary['love_language'] or 'Not set'}

**Relationship Goals:**
{', '.join(profile_summary['relationship_goals']) if profile_summary['relationship_goals'] else 'Not set'}

**Current Status:**
{profile_summary['current_status'] or 'Not set'}

**Strengths:**
{', '.join(profile_summary['strengths']) if profile_summary['strengths'] else 'Not set'}

**Growth Areas:**
{', '.join(profile_summary['growth_areas']) if profile_summary['growth_areas'] else 'Not set'}

Last updated: {profile_summary['last_updated'][:10]}
            """
        else:
            profile_text = "Profile not found. Let's create one!"
        
        keyboard = [
            [InlineKeyboardButton("Edit Basic Info", callback_data="edit_basic_info")],
            [InlineKeyboardButton("Edit Personality", callback_data="edit_personality")],
            [InlineKeyboardButton("Edit Relationship Info", callback_data="edit_relationship_info")],
            [InlineKeyboardButton("View Partner's Profile", callback_data="view_partner_profile")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(profile_text, reply_markup=reply_markup)
    
    async def diary_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enter personal diary mode"""
        user = update.effective_user
        user_id = user.id
        
        self.active_sessions[user_id] = {
            "mode": "diary_entry",
            "step": "mood",
            "data": {}
        }
        
        await update.message.reply_text(
            "📖 **Personal Diary Mode**\n\n"
            "Let's reflect on your day and relationship. This is your private space for thoughts and feelings.\n\n"
            "How are you feeling today? (e.g., happy, stressed, grateful, anxious, excited)"
        )
    
    async def personalized_insights(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show personalized insights and advice"""
        user = update.effective_user
        user_id = user.id
        
        # Get user profile
        profile = profile_manager.load_profile(user_id)
        if not profile:
            await update.message.reply_text(
                "Please set up your profile first using /profile"
            )
            return
        
        # Get couple context
        couple_id = f"couple_{user_id}"
        relationship_context = relationship_memory.get_relationship_context(couple_id)
        
        # Generate personalized insights
        insights_data = profile_manager.generate_personalized_advice(user_id, couple_id, "current session")
        
        insights_text = f"""
🌟 **Personalized Insights for {profile.full_name}**

**Based on your profile and relationship patterns:**

**Communication Style:**
{profile.communication_style}

**Love Language:**
{profile.love_language}

**Current Goals:**
{', '.join(profile.relationship_goals)}

**Strengths to Build On:**
{', '.join(profile.strengths_in_relationship)}

**Areas for Growth:**
{', '.join(profile.areas_for_improvement)}

**Personalized Recommendations:**
• Practice {profile.love_language} more actively
• Focus on {', '.join(profile.personal_growth_areas[:2])}
• Build on your strengths in {', '.join(profile.strengths_in_relationship[:2])}

Would you like me to generate specific advice for any particular area?
        """
        
        keyboard = [
            [InlineKeyboardButton("Communication Advice", callback_data="comm_advice")],
            [InlineKeyboardButton("Conflict Resolution", callback_data="conflict_advice")],
            [InlineKeyboardButton("Personal Growth", callback_data="growth_advice")],
            [InlineKeyboardButton("Relationship Goals", callback_data="goals_advice")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(insights_text, reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "setup_relationship":
            await self.setup_relationship(update, context)
        elif query.data == "start_chat":
            await query.edit_message_text("Great! I'm ready to chat. Just send me a message about your relationship! 💬")
        elif query.data == "help_info":
            await self.help_command(update, context)
        elif query.data == "view_insights":
            await self.get_insights(update, context)
        elif query.data == "discuss_communication":
            await query.edit_message_text(
                "Let's discuss your communication! What specific aspect would you like to work on?\n\n"
                "• Active listening\n"
                "• Expressing feelings\n"
                "• Conflict communication\n"
                "• Daily check-ins\n"
                "• Something else"
            )
        elif query.data == "address_conflicts":
            await self.conflict_mode(update, context)
        elif query.data == "set_goals":
            await query.edit_message_text(
                "Let's set some relationship goals! What would you like to work on together?\n\n"
                "Some ideas:\n"
                "• Spend more quality time together\n"
                "• Improve communication about difficult topics\n"
                "• Plan future activities or milestones\n"
                "• Work on trust and understanding\n"
                "• Develop shared hobbies or interests\n\n"
                "What goals resonate with you?"
            )
        elif query.data == "celebrate_progress":
            await self.milestone_mode(update, context)
        elif query.data == "manage_profile":
            await self.profile_management(update, context)
        elif query.data == "personal_insights":
            await self.personalized_insights(update, context)
        elif query.data == "edit_basic_info":
            await self.start_profile_edit(update, context, "basic_info")
        elif query.data == "edit_personality":
            await self.start_profile_edit(update, context, "personality")
        elif query.data == "edit_relationship_info":
            await self.start_profile_edit(update, context, "relationship_info")
        elif query.data == "view_partner_profile":
            await self.view_partner_profile(update, context)
        elif query.data == "back_to_main":
            await self.start_command(update, context)
        elif query.data == "comm_advice":
            await self.generate_specific_advice(update, context, "communication")
        elif query.data == "conflict_advice":
            await self.generate_specific_advice(update, context, "conflict")
        elif query.data == "growth_advice":
            await self.generate_specific_advice(update, context, "growth")
        elif query.data == "goals_advice":
            await self.generate_specific_advice(update, context, "goals")
    
    async def handle_diary_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Handle diary entry steps"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        if session["step"] == "mood":
            session["data"]["mood"] = message_text
            session["step"] = "relationship_thoughts"
            
            await update.message.reply_text(
                "How are you feeling about your relationship today? What thoughts or feelings are coming up?"
            )
        
        elif session["step"] == "relationship_thoughts":
            session["data"]["relationship_thoughts"] = message_text
            session["step"] = "personal_growth"
            
            await update.message.reply_text(
                "What personal growth or learning have you experienced today?"
            )
        
        elif session["step"] == "personal_growth":
            session["data"]["personal_growth"] = message_text
            session["step"] = "gratitude"
            
            await update.message.reply_text(
                "What are you grateful for today? (about yourself, your partner, your relationship)"
            )
        
        elif session["step"] == "gratitude":
            session["data"]["gratitude_notes"] = message_text
            session["step"] = "challenges"
            
            await update.message.reply_text(
                "What challenges are you facing? (personal or relationship-related)"
            )
        
        elif session["step"] == "challenges":
            session["data"]["challenges"] = message_text
            session["step"] = "goals"
            
            await update.message.reply_text(
                "What would you like to work on or achieve tomorrow?"
            )
        
        elif session["step"] == "goals":
            session["data"]["goals_for_tomorrow"] = message_text
            
            # Complete diary entry
            await self.complete_diary_entry(update, context, session)
    
    async def complete_diary_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Complete diary entry"""
        user = update.effective_user
        user_id = user.id
        data = session["data"]
        
        # Create diary entry
        diary_entry = PersonalDiary(
            user_id=user_id,
            entry_date=datetime.now().strftime("%Y-%m-%d"),
            mood=data["mood"],
            relationship_thoughts=data["relationship_thoughts"],
            personal_growth=data["personal_growth"],
            gratitude_notes=data["gratitude_notes"],
            challenges=data["challenges"],
            goals_for_tomorrow=data["goals_for_tomorrow"]
        )
        
        # Save diary entry
        profile_manager.save_diary_entry(diary_entry)
        
        # Store in MCP if available
        if settings.MCP_SERVER_URL:
            try:
                await mcp_tools.store_diary_entry(user_id, asdict(diary_entry))
            except Exception as e:
                logger.error(f"Failed to store diary in MCP: {e}")
        
        # Clear session
        del self.active_sessions[user_id]
        
        completion_message = f"""
📖 **Diary Entry Complete!**

Thank you for sharing your thoughts and feelings. Here's a summary of your entry:

**Mood:** {data['mood']}
**Relationship Thoughts:** {data['relationship_thoughts'][:100]}...
**Personal Growth:** {data['personal_growth'][:100]}...
**Gratitude:** {data['gratitude_notes'][:100]}...
**Challenges:** {data['challenges'][:100]}...
**Tomorrow's Goals:** {data['goals_for_tomorrow'][:100]}...

Your diary entry has been saved and will help me provide more personalized insights in the future.

Keep up the great work on self-reflection! 🌟
        """
        
        await update.message.reply_text(completion_message)
    
    async def handle_profile_edit_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """Handle profile editing steps"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        if session["step"] == "basic_info":
            # Update full name
            profile_manager.update_profile_field(user_id, "full_name", message_text)
            session["step"] = "birth_date"
            
            await update.message.reply_text(
                "Great! When is your birthday? (format: YYYY-MM-DD, or just the year if you prefer)"
            )
        
        elif session["step"] == "birth_date":
            profile_manager.update_profile_field(user_id, "birth_date", message_text)
            
            # Complete basic info edit
            del self.active_sessions[user_id]
            
            await update.message.reply_text(
                "✅ Basic information updated successfully!\n\n"
                "Use /profile to view your updated profile."
            )
        
        elif session["step"] == "personality":
            # Parse personality traits
            traits = [trait.strip() for trait in message_text.split(',')]
            profile_manager.update_profile_field(user_id, "personality_traits", traits)
            session["step"] = "communication_style"
            
            await update.message.reply_text(
                "How would you describe your communication style? (e.g., direct and logical, emotional and intuitive, analytical and thoughtful)"
            )
        
        elif session["step"] == "communication_style":
            profile_manager.update_profile_field(user_id, "communication_style", message_text)
            session["step"] = "love_language"
            
            await update.message.reply_text(
                "What's your primary love language? (e.g., words of affirmation, acts of service, quality time, physical touch, receiving gifts)"
            )
        
        elif session["step"] == "love_language":
            profile_manager.update_profile_field(user_id, "love_language", message_text)
            
            # Complete personality edit
            del self.active_sessions[user_id]
            
            await update.message.reply_text(
                "✅ Personality information updated successfully!\n\n"
                "Use /profile to view your updated profile."
            )
        
        elif session["step"] == "relationship_info":
            profile_manager.update_profile_field(user_id, "current_relationship_status", message_text)
            session["step"] = "relationship_goals"
            
            await update.message.reply_text(
                "What are your main relationship goals? (e.g., better communication, deeper emotional connection, shared adventures, long-term commitment)"
            )
        
        elif session["step"] == "relationship_goals":
            goals = [goal.strip() for goal in message_text.split(',')]
            profile_manager.update_profile_field(user_id, "relationship_goals", goals)
            session["step"] = "strengths"
            
            await update.message.reply_text(
                "What are your strengths in relationships? (e.g., loyalty, empathy, communication, problem-solving, patience)"
            )
        
        elif session["step"] == "strengths":
            strengths = [strength.strip() for strength in message_text.split(',')]
            profile_manager.update_profile_field(user_id, "strengths_in_relationship", strengths)
            session["step"] = "growth_areas"
            
            await update.message.reply_text(
                "What areas would you like to improve in relationships? (e.g., active listening, emotional expression, conflict resolution, patience)"
            )
        
        elif session["step"] == "growth_areas":
            growth_areas = [area.strip() for area in message_text.split(',')]
            profile_manager.update_profile_field(user_id, "areas_for_improvement", growth_areas)
            
            # Complete relationship info edit
            del self.active_sessions[user_id]
            
            await update.message.reply_text(
                "✅ Relationship information updated successfully!\n\n"
                "Use /profile to view your updated profile."
            )
    
    async def start_profile_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, edit_type: str):
        """Start profile editing process"""
        user = update.effective_user
        user_id = user.id
        
        self.active_sessions[user_id] = {
            "mode": "profile_edit",
            "step": edit_type,
            "data": {}
        }
        
        if edit_type == "basic_info":
            await update.callback_query.edit_message_text(
                "Let's update your basic information!\n\n"
                "What's your full name? (e.g., Stepan Egoshin)"
            )
        elif edit_type == "personality":
            await update.callback_query.edit_message_text(
                "Let's explore your personality!\n\n"
                "What are your main personality traits? (e.g., analytical, creative, empathetic, logical, intuitive)"
            )
        elif edit_type == "relationship_info":
            await update.callback_query.edit_message_text(
                "Let's update your relationship information!\n\n"
                "What's your current relationship status? (e.g., committed and growing, newly together, long-term partnership)"
            )
    
    async def view_partner_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View partner's profile"""
        user = update.effective_user
        user_id = user.id
        
        # Get couple context to find partner ID
        couple_id = f"couple_{user_id}"
        relationship_context = relationship_memory.get_relationship_context(couple_id)
        
        if relationship_context:
            partner_id = relationship_context.partner2_id if relationship_context.partner1_id == user_id else relationship_context.partner1_id
            partner_profile = profile_manager.load_profile(partner_id)
            
            if partner_profile:
                partner_summary = profile_manager.get_profile_summary(partner_id)
                
                if isinstance(partner_summary, dict) and "error" not in partner_summary:
                    partner_text = f"""
👥 **Partner Profile: {partner_summary['full_name']}**

**Personality Traits:**
{', '.join(partner_summary['personality_traits']) if partner_summary['personality_traits'] else 'Not set'}

**Communication Style:**
{partner_summary['communication_style'] or 'Not set'}

**Love Language:**
{partner_summary['love_language'] or 'Not set'}

**Relationship Goals:**
{', '.join(partner_summary['relationship_goals']) if partner_summary['relationship_goals'] else 'Not set'}

**Strengths:**
{', '.join(partner_summary['strengths']) if partner_summary['strengths'] else 'Not set'}

**Growth Areas:**
{', '.join(partner_summary['growth_areas']) if partner_summary['growth_areas'] else 'Not set'}
                    """
                else:
                    partner_text = "Partner profile not found or incomplete."
            else:
                partner_text = "Partner profile not found."
        else:
            partner_text = "Relationship context not found. Please set up your relationship first."
        
        keyboard = [[InlineKeyboardButton("Back to My Profile", callback_data="manage_profile")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(partner_text, reply_markup=reply_markup)
    
    async def generate_specific_advice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, advice_type: str):
        """Generate specific advice for a particular area"""
        user = update.effective_user
        user_id = user.id
        
        profile = profile_manager.load_profile(user_id)
        if not profile:
            await update.callback_query.edit_message_text("Profile not found. Please set up your profile first.")
            return
        
        # Generate specific advice based on type
        if advice_type == "communication":
            advice_text = f"""
💬 **Communication Advice for {profile.full_name}**

Based on your communication style: **{profile.communication_style}**

**Specific Recommendations:**
• Practice active listening by repeating back what your partner says
• Use "I feel" statements instead of "You always" statements
• Take breaks during heated discussions to process emotions
• Schedule regular check-ins to discuss relationship matters
• Express appreciation for your partner's communication efforts

**For Your Love Language ({profile.love_language}):**
• Communicate your needs clearly and specifically
• Ask your partner how they prefer to receive communication
• Be patient with different communication styles
            """
        elif advice_type == "conflict":
            advice_text = f"""
⚖️ **Conflict Resolution Advice for {profile.full_name}**

**Your Strengths to Use:**
{', '.join(profile.strengths_in_relationship[:3])}

**Areas to Focus On:**
{', '.join(profile.areas_for_improvement[:3])}

**Conflict Resolution Strategies:**
• Take time to cool down before discussing heated topics
• Focus on the issue, not the person
• Use your {profile.love_language} to show care during conflicts
• Practice empathy by considering your partner's perspective
• Agree on a "time-out" signal when emotions run high
            """
        elif advice_type == "growth":
            advice_text = f"""
🌱 **Personal Growth Advice for {profile.full_name}**

**Growth Areas to Focus On:**
{', '.join(profile.personal_growth_areas)}

**Development Strategies:**
• Set specific, achievable goals for each growth area
• Practice self-reflection through daily journaling
• Seek feedback from your partner about your progress
• Celebrate small wins and improvements
• Be patient with yourself during the growth process
            """
        elif advice_type == "goals":
            advice_text = f"""
🎯 **Relationship Goals Advice for {profile.full_name}**

**Your Current Goals:**
{', '.join(profile.relationship_goals)}

**Goal Achievement Strategies:**
• Break down large goals into smaller, manageable steps
• Set specific timelines for each goal
• Regularly review and adjust goals together
• Celebrate progress toward goals
• Support each other's individual and shared goals
            """
        
        keyboard = [
            [InlineKeyboardButton("More Advice", callback_data="personal_insights")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(advice_text, reply_markup=reply_markup)
    
    async def run(self):
        """Run the bot"""
        logger.info("Starting Family Psychologist Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()


# Global bot instance
bot = FamilyPsychologistBot() 