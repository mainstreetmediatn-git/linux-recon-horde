class PolicyEngine:
    @staticmethod
    def validate_execution_policy(
        risk_level: str,
        user_acknowledged: bool,
    ) -> tuple[bool, str]:
        if risk_level in {"High", "Critical"} and not user_acknowledged:
            return (
                False,
                f"Module is rated {risk_level} risk. "
                "Explicit user acknowledgement is required.",
            )
        return True, "Passed policy check."
