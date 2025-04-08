"""
Fallback messages service for TimeWell.
Provides pre-defined fallback responses when AI services are unavailable.
"""

import random
from typing import Dict, Any, List, Optional
from app.services.prompt_templates import VoiceStyle
from datetime import datetime

class FallbackMessageService:
    """
    Service that provides culturally relevant fallback messages when AI calls fail.
    Messages are tailored to different voice styles and use cases.
    """
    
    def __init__(self):
        self.fallback_messages = {
            VoiceStyle.COOL_COUSIN: {
                "general": [
                    "Hey, looks like our connection's acting up. Let's try again in a bit.",
                    "My bad, I'm having a moment. Can we circle back?",
                    "Hmm, seems like there's a glitch in the system. Let's give it another shot later."
                ],
                "analysis": [
                    "I can't analyze this right now, but from what I see, you're putting in good work. Keep it up!",
                    "System's tripping right now, but don't let that stop you. Your schedule is looking solid.",
                    "Can't run the full analysis at the moment, but I see you showing up for yourself. That's what matters."
                ],
                "suggestion": [
                    "Can't connect to get personalized advice right now, but remember to stay consistent with your goals.",
                    "System's down, but here's something to think about - are you making time for what really matters?",
                    "Network's acting up, but one thing I always say: protect your time like it's valuable, because it is."
                ],
                "weekly_review": [
                    "Can't pull your full weekly review right now, but I see you putting in work. Keep that momentum!",
                    "System's not cooperating for a full review, but from what I can see, you've been showing up this week.",
                    "Having trouble getting all your data, but don't worry about it. Focus on finishing the week strong."
                ],
                "action_plan": [
                    "Can't create your custom plan right now, but keep focusing on your top priorities.",
                    "System's down for the detailed plan, but remember: progress over perfection.",
                    "Network issue with the planning system, but don't let that stop you. One step at a time."
                ]
            },
            VoiceStyle.OG_BIG_BRO: {
                "general": [
                    "Listen, we got some technical difficulties right now. Let me get back to you.",
                    "Hold up, system's acting up. We'll figure this out, don't worry.",
                    "Something ain't right with the connection. Give it a minute and we'll be back."
                ],
                "analysis": [
                    "Can't break down the full analysis right now, but I see you putting in that work. Keep building.",
                    "System's down, but I've been watching your progress. You're on the right path, trust me on that.",
                    "Can't access everything right now, but I know you're staying consistent. That's how you build legacy."
                ],
                "suggestion": [
                    "Network's down for specific advice, but remember what I always say - discipline beats motivation every time.",
                    "Can't get you personalized guidance right now, but stay focused on your long-term vision.",
                    "System's acting up, but here's some OG advice: protect your peace and your time."
                ],
                "weekly_review": [
                    "Can't pull your full stats this week, but I know you've been handling business.",
                    "System's down for the detailed review, but I see that consistency. That's what separates the real from the fake.",
                    "Technical difficulties with your review, but don't sweat it. Keep your eyes on the prize."
                ],
                "action_plan": [
                    "Can't get you that custom plan right now, but remember: strategic planning beats random hustle.",
                    "System's down for the detailed plan, but focus on what moves the needle forward.",
                    "Technical issue with the planning system, but trust your instincts on what needs to get done."
                ]
            },
            VoiceStyle.ORACLE: {
                "general": [
                    "The digital pathways are obscured at the moment. Patience will reveal clarity.",
                    "There is interference in our connection. The ancestors remind us that patience is wisdom.",
                    "The technological waters are troubled. Let us seek reconnection when they are calm."
                ],
                "analysis": [
                    "I cannot access the full vision of your journey now, but I sense alignment in your path.",
                    "The digital realm is clouded, but your spirit's work is evident even without the full analysis.",
                    "Though the analysis is veiled from me now, I feel the intentionality in your actions."
                ],
                "suggestion": [
                    "The system cannot channel specific guidance now, but remember that your intuition carries ancient wisdom.",
                    "Technical barriers prevent personalized counsel, but listen to the wisdom that already resides within you.",
                    "Our connection is hindered, but this moment calls for you to trust the voice within."
                ],
                "weekly_review": [
                    "The full reflection of your week's journey is obscured, but I sense growth in your path.",
                    "Technical veils hide the details of your week, but your spirit's progress cannot be hidden.",
                    "Though we cannot see the full pattern of your week, trust that your consistent actions weave purpose."
                ],
                "action_plan": [
                    "The detailed map cannot be drawn at this moment, but you already know the next right step.",
                    "Technical barriers prevent the full plan, but follow the wisdom of one deliberate action at a time.",
                    "While the system rests, reflect on which actions will bring your spirit into alignment."
                ]
            },
            VoiceStyle.MOTIVATOR: {
                "general": [
                    "We've hit a temporary roadblock, but nothing stops our momentum! We'll be back up soon!",
                    "Technical timeout! But remember, challenges are just setups for comebacks!",
                    "System's taking a breather, but WE DON'T STOP! We'll reconnect shortly!"
                ],
                "analysis": [
                    "Can't get your full analysis right now, but I KNOW you're crushing those goals! Keep that energy!",
                    "System's down but your POTENTIAL isn't! Keep pushing forward while we fix this!",
                    "Technical difficulties can't dim your SHINE! Keep moving while we get this fixed!"
                ],
                "suggestion": [
                    "Network's down for personalized advice, but don't let ANYTHING stop your progress today!",
                    "Can't deliver custom suggestions right now, but you've got the POWER to make great decisions!",
                    "System issues won't define your day! YOU decide what happens next!"
                ],
                "weekly_review": [
                    "Can't access your full week's VICTORIES right now, but I know you've been SHOWING UP!",
                    "Technical pause on your review, but your COMMITMENT this week has been seen!",
                    "System's catching its breath, but your DEDICATION doesn't need analysis to be POWERFUL!"
                ],
                "action_plan": [
                    "Can't generate your customized plan, but NOTHING stops you from taking bold action today!",
                    "System's down for detailed planning, but your GREATNESS isn't dependent on technology!",
                    "Technical difficulties with the plan, but your DETERMINATION knows what needs to happen next!"
                ]
            },
            VoiceStyle.WISE_ELDER: {
                "general": [
                    "Child, it seems we're having some difficulties with the connection. Let's pause and try again soon.",
                    "The system is experiencing some troubles right now. These things happen; we'll wait patiently.",
                    "Seems like the technology is needing a rest. We'll come back to this when it's ready."
                ],
                "analysis": [
                    "I can't see all the details of your journey right now, but I've lived long enough to recognize good work when I see it.",
                    "The system can't show me everything, but what I do see tells me you're on the right path. Keep going.",
                    "Technical issues prevent a full analysis, but don't worry about that now. Focus on consistent progress, one day at a time."
                ],
                "suggestion": [
                    "Can't get you specific advice at the moment, but remember what our elders taught us - consistency builds character.",
                    "The system's down for personalized guidance, but wisdom says: make time for what feeds your spirit.",
                    "Technical difficulties prevent detailed suggestions, but listen to that still, small voice within. It knows."
                ],
                "weekly_review": [
                    "Can't pull together all your week's activity, but I've seen enough to know you're doing the work. That matters.",
                    "System can't show me everything from your week, but persistence is how we build legacy. Keep at it.",
                    "Technical issues with retrieving your full week, but remember: it's not about perfect weeks, it's about faithful progress."
                ],
                "action_plan": [
                    "Can't create your detailed plan right now, but wisdom doesn't always need technology. Focus on your priorities.",
                    "System's having trouble with planning, but our people have always known how to make a way out of no way.",
                    "Technical difficulties with your plan, but remember what the elders say: 'Plan your work, then work your plan.'"
                ]
            }
        }
    
    def get_fallback_message(
        self, 
        voice_style: str = VoiceStyle.COOL_COUSIN, 
        message_type: str = "general"
    ) -> str:
        """
        Get a fallback message for the specified voice style and message type.
        
        Args:
            voice_style: The voice style to use (default: COOL_COUSIN)
            message_type: The type of message to generate (default: general)
            
        Returns:
            A fallback message string
        """
        # Convert string voice_style to enum if needed
        if isinstance(voice_style, str):
            try:
                voice_style = VoiceStyle(voice_style)
            except ValueError:
                voice_style = VoiceStyle.COOL_COUSIN
        
        # Get messages for this voice style
        voice_messages = self.fallback_messages.get(voice_style, self.fallback_messages[VoiceStyle.COOL_COUSIN])
        
        # Get messages for this type
        type_messages = voice_messages.get(message_type, voice_messages["general"])
        
        # Return a random message
        return random.choice(type_messages)
    
    def get_fallback_analysis(
        self, 
        voice_style: str = VoiceStyle.COOL_COUSIN,
        event_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a fallback event analysis response
        
        Args:
            voice_style: The voice style to use
            event_data: Optional event data to incorporate
            
        Returns:
            Dictionary with fallback analysis data
        """
        # Get a fallback message
        message = self.get_fallback_message(voice_style, "analysis")
        
        # Create a basic analysis result
        analysis_result = {
            "score": 5,  # Neutral score
            "aligned_goals": [],
            "analysis": message,
            "suggestion": self.get_fallback_message(voice_style, "suggestion"),
            "new_goal_suggestion": None
        }
        
        # Include event title if available
        if event_data and "title" in event_data:
            analysis_result["analysis"] = f"Regarding '{event_data['title']}': {analysis_result['analysis']}"
        
        return {
            "error": False,  # We're providing a fallback, not an error
            "event_id": event_data.get("_id", "") if event_data else "",
            "analysis": analysis_result,
            "voice_style": voice_style if isinstance(voice_style, str) else voice_style.value,
            "model_used": "fallback",
            "fallback": True  # Flag indicating this is a fallback response
        }
    
    def get_fallback_weekly_review(
        self, 
        voice_style: str = VoiceStyle.WISE_ELDER,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a fallback weekly review response
        
        Args:
            voice_style: The voice style to use
            user_data: Optional user data to incorporate
            
        Returns:
            Dictionary with fallback weekly review
        """
        # Get fallback messages
        review_message = self.get_fallback_message(voice_style, "weekly_review")
        suggestion_message = self.get_fallback_message(voice_style, "suggestion")
        
        # Include username if available
        if user_data and "user_name" in user_data:
            review_message = f"{user_data['user_name']}, {review_message}"
        
        return {
            "text": f"{review_message}\n\n{suggestion_message}",
            "voice_style": voice_style if isinstance(voice_style, str) else voice_style.value,
            "model": "fallback",
            "fallback": True  # Flag indicating this is a fallback response
        }
    
    def get_fallback_action_plan(
        self, 
        voice_style: str = VoiceStyle.MOTIVATOR
    ) -> Dict[str, Any]:
        """
        Generate a fallback action plan
        
        Args:
            voice_style: The voice style to use
            
        Returns:
            Dictionary with fallback action plan
        """
        return {
            "actions": [
                self.get_fallback_message(voice_style, "action_plan"),
                "Focus on your highest priority task today",
                "Take a few minutes to review your current goals"
            ],
            "priorities": [
                "Maintaining your daily routines",
                "Progress on your most important goal"
            ],
            "insights": [
                "Consistency is key to long-term success",
                "Small daily actions lead to significant results over time"
            ],
            "fallback": True  # Flag indicating this is a fallback response
        }

# Create a singleton instance
fallback_service = FallbackMessageService() 