class RAGRetriever:
    """
    Production implementation:
        1. Embed user_message thành vector
           (OpenAI ada-002 hoặc sentence-transformers)
        2. Query FAISS index: index.search(vector, k=3)
        3. Rerank kết quả nếu cần (Cohere reranker)
        4. Trả về top-k chunks dưới dạng string
    """

    # Knowledge base — trong production sẽ được
    # load từ FAISS index đã được embed sẵn
    KNOWLEDGE_BASE = {
        "competency_framework": """
            Gucci Group Competency Framework (4 themes):

            1. VISION
               - Strategic thinking across brand boundaries
               - Future orientation and market sensing
               - Behaviors: Associate = understands brand strategy;
                 Mid = shapes team direction;
                 Senior = influences Group-level strategy

            2. ENTREPRENEURSHIP
               - Innovation within brand constraints
               - Calculated risk-taking and ownership
               - Behaviors: Associate = proposes new ideas;
                 Mid = leads cross-functional initiatives;
                 Senior = drives Group-wide transformation

            3. PASSION
               - Deep craftsmanship and brand heritage pride
               - Customer obsession and quality standards
               - Behaviors: Associate = demonstrates brand knowledge;
                 Mid = embodies and transmits brand values;
                 Senior = guardians of brand equity

            4. TRUST
               - Psychological safety within teams
               - Foundation for cross-brand collaboration
               - Behaviors: Associate = reliable team member;
                 Mid = builds bridges across functions;
                 Senior = enables inter-brand mobility culture
        """,

        "group_hr_mandate": """
            Group HR Mandate:
            - Identify and develop talent across all 9 brands
            - Increase inter-brand mobility (target: +20% YoY)
            - Support brand DNA — NEVER impose Group process
            - Each brand retains autonomy over local HR decisions

            Key principle: The Group provides tools and frameworks.
            Brands choose how and when to adopt them.
        """,

        "mobility_policy": """
            Inter-brand Mobility Policy:
            - Requires Trust competency at Level 2+ (Mid level)
            - Minimum 18 months tenure in current brand role
            - Line manager endorsement required
            - Brand HR and Group HR joint approval process
            - Candidate retains original brand affiliation
              for cultural identity purposes
        """,

        "360_program": """
            360° Feedback Program Design:
            - Rater groups: Self, Manager, Peers (3-5), Direct Reports
            - Scale: 1-5 behavioral frequency scale
            - Items per theme: 5 items × 4 themes = 20 items total
            - Anonymity: All raters except manager are anonymous
            - Language coverage: EN, FR, IT, DE, ES, ZH, JA
            - Data privacy: GDPR compliant, results shared only
              with participant and their coach
        """,

        "rollout_plan": """
            Cascade Rollout Strategy:
            - Train-the-trainer model across brands and regions
            - Workshop format: 2-day interactive sessions
            - Local HR as primary trainer (not Group HR)
            - Phased rollout: Pilot 2 brands → Evaluate → Scale
            - Change risks: Brand identity dilution,
              time pressure during peak seasons,
              language and cultural adaptation needs
            - KPIs: Trainer certification rate, 
              completion rate, mobility rate change
        """
    }

    # Keyword mapping để simulate semantic search
    KEYWORD_MAP = {
        "competency": "competency_framework",
        "vision": "competency_framework",
        "entrepreneurship": "competency_framework",
        "passion": "competency_framework",
        "trust": "competency_framework",
        "framework": "competency_framework",
        "behavior": "competency_framework",
        "mobility": "mobility_policy",
        "inter-brand": "mobility_policy",
        "transfer": "mobility_policy",
        "mandate": "group_hr_mandate",
        "mission": "group_hr_mandate",
        "autonomy": "group_hr_mandate",
        "360": "360_program",
        "feedback": "360_program",
        "rater": "360_program",
        "survey": "360_program",
        "rollout": "rollout_plan",
        "cascade": "rollout_plan",
        "trainer": "rollout_plan",
        "workshop": "rollout_plan",
        "kpi": "rollout_plan",
    }

    def retrieve(self, user_message: str, k: int = 2) -> str:
        """
        Args:
            user_message : Tin nhắn của learner
            k            : Số chunks muốn retrieve (default 2)

        Returns:
            String chứa relevant context để inject vào prompt

        Production replacement:
            query_vector = embed_model.encode(user_message)
            distances, indices = faiss_index.search(
                query_vector.reshape(1, -1), k
            )
            return "\n\n".join([chunks[i] for i in indices[0]])
        """
        msg_lower = user_message.lower()
        matched_keys = set()

        for keyword, chunk_key in self.KEYWORD_MAP.items():
            if keyword in msg_lower:
                matched_keys.add(chunk_key)
                if len(matched_keys) >= k:
                    break

        if not matched_keys:
            matched_keys.add("group_hr_mandate")

        retrieved_chunks = [
            self.KNOWLEDGE_BASE[key]
            for key in matched_keys
        ]

        return "\n\n---\n\n".join(retrieved_chunks)