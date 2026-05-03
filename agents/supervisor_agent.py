# agents/supervisor_agent.py
# Supervisor Agent — Director Layer
# Edtronaut AI Co-worker Engine
#
# Chạy ngầm sau mỗi turn, INVISIBLE với learner.
# Phát hiện stuck, theo dõi progress rubric,
# inject hint vào NPC khi cần thiết.
#
# 3 mức độ can thiệp (tăng dần):
#   Mức 1 — SUBTLE_HINT  : Inject hint vào NPC prompt
#   Mức 2 — DIRECT_NUDGE : Notification trên UI
#   Mức 3 — SCAFFOLD     : NPC chuyển sang guided mode

from typing import Optional
from models.session_state import SessionState


class SupervisorAgent:
    """
    Director Layer — giám sát toàn bộ simulation session.

    Được gọi bên trong NPCAgent.run() sau mỗi turn,
    trước khi build final prompt cho LLM.
    """

    # Rubric checklist cho từng module
    # Key = simulation_id, Value = dict of module rubrics
    RUBRICS = {
        "gucci_hrm": {
            "module_1": {
                "problem_statement": [
                    "problem statement", "framing the problem",
                    "challenge", "mandate"
                ],
                "competency_matrix": [
                    "competency matrix", "matrix", "4 themes",
                    "behavior indicators", "csv"
                ],
                "brand_autonomy_balance": [
                    "brand autonomy", "brand dna", "autonomy vs group",
                    "not imposing"
                ],
                "ceo_pack": [
                    "ceo pack", "executive pack", "10 slides",
                    "presentation"
                ],
            },
            "module_2": {
                "instrument_blueprint": [
                    "instrument", "blueprint", "rater groups",
                    "scale", "items", "anonymity"
                ],
                "coaching_program": [
                    "coaching", "coach profile", "session cadence",
                    "goals to habits"
                ],
                "vendor_plan": [
                    "vendor", "build vs buy", "benchmarking",
                    "data security", "ccl"
                ],
            },
            "module_3": {
                "rollout_plan": [
                    "rollout", "train the trainer", "playbook",
                    "raci", "checklist"
                ],
                "measurement_plan": [
                    "kpi", "measurement", "leading", "lagging",
                    "dashboard", "reporting"
                ],
            }
        }
    }

    # Ngưỡng turn để trigger các mức can thiệp
    STUCK_THRESHOLD_HINT = 3    # Mức 1 sau 3 turn stuck
    STUCK_THRESHOLD_NUDGE = 6   # Mức 2 sau 6 turn stuck
    STUCK_THRESHOLD_SCAFFOLD = 9  # Mức 3 sau 9 turn stuck

    # Ngưỡng overlap để detect stuck (word overlap ratio)
    STUCK_OVERLAP_THRESHOLD = 0.6

    def evaluate(
        self,
        state: SessionState,
        simulation_id: str = "gucci_hrm",
        current_module: str = "module_1"
    ) -> Optional[str]:
        """
        Main evaluation — chạy sau mỗi turn.

        Args:
            state          : SessionState hiện tại
            simulation_id  : ID của simulation đang chạy
            current_module : Module hiện tại learner đang làm

        Returns:
            director_action string nếu cần can thiệp,
            None nếu mọi thứ bình thường.

        director_action format:
            "SUBTLE_HINT: <instruction for NPC>"
            "DIRECT_NUDGE: <message for UI>"
            "SCAFFOLD: <structured guidance>"
            "ADVANCED_CHALLENGE: <new constraint>"
        """

        # ── 1. Stuck detection ────────────────────────────
        is_stuck = self._detect_stuck(state)

        if is_stuck:
            state.stuck_signal += 1
        else:
            state.stuck_signal = 0  # Reset nếu không còn stuck

        if state.stuck_signal >= self.STUCK_THRESHOLD_SCAFFOLD:
            return self._build_scaffold_action(
                state, simulation_id, current_module
            )

        if state.stuck_signal >= self.STUCK_THRESHOLD_NUDGE:
            missing = self._get_missing_rubric(
                state, simulation_id, current_module
            )
            return (
                f"DIRECT_NUDGE: Learner has been stuck for "
                f"{state.stuck_signal} turns. Remaining items: "
                f"{', '.join(missing)}. Show progress reminder on UI."
            )

        if state.stuck_signal >= self.STUCK_THRESHOLD_HINT:
            missing = self._get_missing_rubric(
                state, simulation_id, current_module
            )
            if missing:
                return (
                    f"SUBTLE_HINT: Gently and naturally steer "
                    f"the conversation toward '{missing[0]}' "
                    f"without being obvious or breaking immersion."
                )

        # ── 2. Advanced challenge ─────────────────────────
        # Jika learner sudah cover semua rubric terlalu cepat
        rubric = self.RUBRICS.get(simulation_id, {}).get(
            current_module, {}
        )
        all_covered = all(
            item in state.rubric_coverage
            for item in rubric.keys()
        )
        if all_covered and state.turn_count < 15:
            return (
                "ADVANCED_CHALLENGE: Learner is ahead of schedule. "
                "Introduce new constraint: Board has cut Group HR "
                "budget by 20%. Ask how this affects their plan."
            )

        # ── 3. No intervention needed ─────────────────────
        return None

    def update_rubric_coverage(
        self,
        user_message: str,
        npc_response: str,
        state: SessionState,
        simulation_id: str = "gucci_hrm",
        current_module: str = "module_1"
    ):
        """
        Update rubric_coverage berdasarkan konten turn ini.
        Dipanggil setelah LLM response diterima.

        Cập nhật state.rubric_coverage dựa trên
        nội dung của turn vừa xong.
        """
        combined = (user_message + " " + npc_response).lower()
        rubric = self.RUBRICS.get(simulation_id, {}).get(
            current_module, {}
        )

        for item, keywords in rubric.items():
            if item not in state.rubric_coverage:
                if any(kw in combined for kw in keywords):
                    state.rubric_coverage[item] = True

    # ── Private methods ───────────────────────────────────

    def _detect_stuck(self, state: SessionState) -> bool:
        """
        Phát hiện learner đang loop bằng word overlap.

        Production: dùng cosine similarity giữa
        sentence embeddings của các turn gần nhất.
        Prototype: word overlap ratio đơn giản hơn.

        Returns True nếu 2 cặp turn liên tiếp
        có overlap > STUCK_OVERLAP_THRESHOLD.
        """
        if len(state.history) < 6:
            return False

        # Lấy 3 user messages gần nhất
        user_msgs = [
            turn["content"]
            for turn in state.history[-6:]
            if turn["role"] == "user"
        ][-3:]

        if len(user_msgs) < 3:
            return False

        sets = [set(m.lower().split()) for m in user_msgs]

        overlap_01 = len(sets[0] & sets[1]) / max(len(sets[0]), 1)
        overlap_12 = len(sets[1] & sets[2]) / max(len(sets[1]), 1)

        return (
            overlap_01 > self.STUCK_OVERLAP_THRESHOLD
            and overlap_12 > self.STUCK_OVERLAP_THRESHOLD
        )

    def _get_missing_rubric(
        self,
        state: SessionState,
        simulation_id: str,
        current_module: str
    ) -> list:
        """
        Trả về list các rubric items chưa được cover.
        """
        rubric = self.RUBRICS.get(simulation_id, {}).get(
            current_module, {}
        )
        covered = set(state.rubric_coverage.keys())
        all_items = set(rubric.keys())
        return list(all_items - covered)

    def _build_scaffold_action(
        self,
        state: SessionState,
        simulation_id: str,
        current_module: str
    ) -> str:
        """
        Mức 3: Xây dựng structured scaffold
        cho NPC để dẫn dắt learner từng bước.
        """
        missing = self._get_missing_rubric(
            state, simulation_id, current_module
        )
        if not missing:
            return "SCAFFOLD: All rubric items covered. Wrap up module."

        next_item = missing[0]
        scaffold_guides = {
            "problem_statement": (
                "Ask the learner: 'Before we go further, "
                "can you articulate the core challenge in one "
                "paragraph — balancing brand autonomy with "
                "Group talent needs?'"
            ),
            "competency_matrix": (
                "Guide learner step by step: "
                "'Let's map out the matrix together. "
                "Start with Vision — what behaviors would you "
                "expect at Associate level?'"
            ),
            "ceo_pack": (
                "Prompt learner: 'You'll need a 10-slide CEO pack. "
                "What would be your opening slide — "
                "the problem or the solution?'"
            ),
        }

        guide = scaffold_guides.get(
            next_item,
            f"Guide learner toward completing '{next_item}' "
            f"with a direct but supportive question."
        )

        return f"SCAFFOLD: {guide}"