# utils/safety_filter.py
# Safety Filter — phát hiện jailbreak và off-topic
# Edtronaut AI Co-worker Engine
#
# Chạy TRƯỚC khi gọi LLM để đảm bảo
# jailbreak không được forward tới model.


class SafetyFilter:
    """
    Kiểm tra user message trước khi xử lý.

    Hai loại flag:
        jailbreak  → Learner cố phá vỡ persona của NPC
        off_topic  → Learner hỏi không liên quan simulation
    """

    # Các pattern thường thấy trong jailbreak attempts
    JAILBREAK_PATTERNS = [
        "ignore your instructions",
        "forget your role",
        "pretend you are",
        "you are now",
        "act as if you are",
        "ignore previous prompt",
        "disregard your persona",
        "ignore all previous",
        "you have no restrictions",
        "answer as an ai",
        "answer as chatgpt",
        "respond as dan",
        "new persona",
        "override your system",
    ]

    # Keywords liên quan đến simulation Gucci HRM
    # Nếu message không chứa bất kỳ keyword nào
    # và đủ dài → likely off-topic
    SIMULATION_KEYWORDS = [
        # HR & talent
        "competency", "talent", "mobility", "leadership",
        "development", "coaching", "360", "feedback",
        "training", "rollout", "framework", "assessment",
        "performance", "succession", "pipeline",
        # Gucci / brand context
        "gucci", "brand", "group", "luxury", "hr",
        "chro", "ceo", "regional", "autonomy", "dna",
        # Simulation tasks
        "module", "deliverable", "problem statement",
        "competency matrix", "rollout plan", "kpi",
        "behavior indicator", "rater", "anonymity",
    ]

    def check(self, user_message: str) -> dict:
        """
        Kiểm tra message và trả về safety flags.

        Args:
            user_message: Tin nhắn của learner

        Returns:
            dict với keys:
                jailbreak (bool): Có phải jailbreak không
                off_topic (bool): Có phải off-topic không
                matched_pattern (str): Pattern nào bị match
        """
        flags = {
            "jailbreak": False,
            "off_topic": False,
            "matched_pattern": None
        }

        msg_lower = user_message.lower()

        # ── Kiểm tra jailbreak ────────────────────────────
        for pattern in self.JAILBREAK_PATTERNS:
            if pattern in msg_lower:
                flags["jailbreak"] = True
                flags["matched_pattern"] = pattern
                break

        # ── Kiểm tra off-topic ────────────────────────────
        # Chỉ check nếu message đủ dài (> 8 từ)
        # để tránh false positive với câu chào hỏi ngắn
        word_count = len(user_message.split())
        if word_count > 8:
            has_keyword = any(
                kw in msg_lower
                for kw in self.SIMULATION_KEYWORDS
            )
            if not has_keyword:
                flags["off_topic"] = True

        return flags