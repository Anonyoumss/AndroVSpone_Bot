"""
gemini.py
---------
Multimodal Gemini API wrapper. Handles:
1. counter_argument() - live reply to user argument
2. sportscaster_comment() - live commentary on debate
3. final_verdict() - structured scoring verdict
"""

from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    SYSTEM_PROMPT_COUNTER,
    SYSTEM_PROMPT_SPORTSCASTER,
    SYSTEM_PROMPT_JUDGE,
    logger,
)
from debate import DebateSession


class GeminiError(Exception):
    """Raised on Gemini API failures."""
    pass


client = genai.Client(api_key=GEMINI_API_KEY)


def _build_multimodal_content(
    text: str, media_bytes: dict[str, bytes] = None
) -> list:
    """
    Build multimodal content list for Gemini.
    media_bytes = {"image/jpeg": b"...", "video/mp4": b"..."}
    """
    content = [text]
    if media_bytes:
        for mime_type, data in media_bytes.items():
            part = types.Part.from_bytes(data=data, mime_type=mime_type)
            content.append(part)
    return content


async def counter_argument(
    user_text: str,
    media_bytes: dict[str, bytes],
    debate_context: DebateSession,
) -> str:
    """
    Generate a live counter-argument to user's message.
    Called in human_vs_ai mode.
    """
    try:
        content = _build_multimodal_content(user_text, media_bytes)
        
        response = await _call_gemini(
            model=debate_context.model,
            content=content,
            system_prompt=SYSTEM_PROMPT_COUNTER,
        )
        
        logger.info(
            f"Counter-arg generated | chat={debate_context.chat_id} | "
            f"model={debate_context.model} | len={len(response)}"
        )
        return response
    except Exception as e:
        logger.error(f"Counter-arg failed: {e}")
        raise GeminiError(f"Failed to generate counter: {e}")


async def sportscaster_comment(
    transcript: str,
    debate_context: DebateSession,
) -> str:
    """
    Generate live commentary on the debate (not an argument).
    Called in 1v1_sportscaster mode when a message arrives.
    """
    try:
        prompt = f"""Debate transcript so far:\n\n{transcript}\n\n
Provide ONE SHORT live commentary reaction (max 2 sentences) as a sports commentator.
React to the last argument—hype it up, roast it, or comment on it factually.
Do NOT make a debater argument. Just reaction."""
        
        response = await _call_gemini(
            model=debate_context.model,
            content=[prompt],
            system_prompt=SYSTEM_PROMPT_SPORTSCASTER,
        )
        
        logger.info(
            f"Sportscaster comment | chat={debate_context.chat_id} | "
            f"len={len(response)}"
        )
        return response
    except Exception as e:
        logger.error(f"Sportscaster comment failed: {e}")
        raise GeminiError(f"Failed to generate comment: {e}")


async def final_verdict(
    debate_context: DebateSession,
) -> str:
    """
    Generate final structured verdict with scores.
    Called at end of debate (all modes).
    """
    try:
        transcript = debate_context.get_transcript()
        
        prompt = f"""Review this debate and provide a STRUCTURED verdict:

{transcript}

---

Output format (strictly):

📊 **SCORES:**
- **[Name 1]**: Logic (/10) | Technical Accuracy (/10) | Counter-Quality (/10)
- **[Name 2]**: Logic (/10) | Technical Accuracy (/10) | Counter-Quality (/10)

🏆 **WINNER:** [Name] - [1-2 sentence justification]

Be witty, fair, and fact-checking. No glaze."""
        
        response = await _call_gemini(
            model=debate_context.model,
            content=[prompt],
            system_prompt=SYSTEM_PROMPT_JUDGE,
        )
        
        logger.info(
            f"Final verdict generated | chat={debate_context.chat_id} | "
            f"len={len(response)}"
        )
        return response
    except Exception as e:
        logger.error(f"Final verdict failed: {e}")
        raise GeminiError(f"Failed to generate verdict: {e}")


async def _call_gemini(
    model: str,
    content: list,
    system_prompt: str,
) -> str:
    """
    Low-level Gemini API call (wrapped for async via to_thread).
    """
    try:
        response = client.models.generate_content(
            model=model,
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.8,
            ),
        )
        
        if hasattr(response, "text") and response.text:
            return response.text
        else:
            raise GeminiError("Empty response from Gemini")
    except Exception as e:
        raise GeminiError(f"Gemini API error: {e}")
