
import html

def html_escape(text: str) -> str:
    """
    Escapes text for Telegram HTML parse mode.
    Handles <, >, &, and ".
    """
    if text is None:
        return ""
    return html.escape(str(text), quote=True)

def render_message(data: dict) -> str:
    """
    Renders the AI analysis and candidates into a Telegram-safe HTML message.
    Handles schema variations (e.g. reply_text_en vs text).
    
    Args:
        data: A dictionary containing:
            - analysis (dict)
            - candidates (list)
            - model_used (str)
            - persona (str)
            
    Returns:
        str: HTML formatted message string.
    """
    
    # 1. Header & Persona
    persona = data.get("persona", "unknown").lower()
    model = data.get("model_used", "unknown")
    
    if "dev" in persona:
        header = "👨‍💻 <b>ARCHITECT OUTPUT</b>"
    elif "brand" in persona:
        header = "🔮 <b>VISIONARY OUTPUT</b>"
    else:
        header = "🤖 <b>AI OUTPUT</b>"
        
    lines = [header]
    
    # 2. Brief Analysis
    analysis = data.get("analysis", {})
    # Handle different possible keys (prompt_builder has 'intent', 'tone', 'topic')
    topic = html_escape(analysis.get("topic", "N/A"))
    sentiment = html_escape(analysis.get("sentiment", "N/A"))
    intent = html_escape(analysis.get("intent", "N/A"))
    tone = html_escape(analysis.get("tone", ""))
    
    meta_parts = []
    if topic != "N/A": meta_parts.append(topic)
    if intent != "N/A": meta_parts.append(intent)
    if tone: meta_parts.append(tone)
    if sentiment != "N/A": meta_parts.append(sentiment)
    
    lines.append(f"📊 <i>{' | '.join(meta_parts)}</i>")
    lines.append("") 
    
    # 3. Ranked Candidates
    candidates = data.get("candidates", [])
    if not candidates:
        lines.append("⚠️ No candidates generated.")
    else:
        # Sort by score descending (if not already sorted)
        candidates.sort(key=lambda x: (x.get('score_total') or x.get('score', 0)), reverse=True)
        
        # Identify recommended
        rec_id = data.get("recommended_id")
        
        for cand in candidates:
            # Handle schema variants
            cid = cand.get("id", "?")
            
            # Text uses reply_text_en or text
            text = cand.get("reply_text_en") or cand.get("text", "")
            text = html_escape(text)
            
            # Score uses score_total or score
            score = cand.get("score_total") or cand.get("score", 0)
            
            # Rationale uses rationale_en or rationale
            rationale = cand.get("rationale_en") or cand.get("rationale", "")
            rationale = html_escape(rationale)
            
            angle = cand.get("angle")
            angle_str = f" — {html_escape(angle)}" if angle else ""
            
            risks = cand.get("risk_flags", [])
            
            # Icon
            if score >= 90: icon = "🔥"
            elif score >= 75: icon = "🟢"
            elif score >= 50: icon = "🟡"
            else: icon = "🔴"
            
            is_rec = " ⭐" if str(cid) == str(rec_id) else ""
            
            lines.append(f"<b>#{cid}{angle_str}</b> {icon} <b>{score}</b>{is_rec}")
            lines.append(f"<code>{text}</code>")
            
            if rationale:
                lines.append(f"<i>{rationale}</i>")
            
            if risks:
                risk_str = ", ".join([html_escape(r) for r in risks])
                lines.append(f"⚠️ {risk_str}")
            
            lines.append("")

    # 4. Footer
    lines.append(f"⚙️ <pre>{html_escape(model)}</pre>")
    
    return "\n".join(lines)
