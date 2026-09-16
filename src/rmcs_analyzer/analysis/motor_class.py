from .results import MotorClassification


class MotorClassCalculator:
    """
    Determine rocket motor impulse class.

    Classification is based on total impulse, not peak thrust.
    """

    CLASS_LIMITS = (
        ("1/8A", 0.3125),
        ("1/4A", 0.625),
        ("1/2A", 1.25),
        ("A", 2.50),
        ("B", 5.00),
        ("C", 10.00),
        ("D", 20.00),
        ("E", 40.00),
        ("F", 80.00),
        ("G", 160.00),
        ("H", 320.00),
        ("I", 640.00),
        ("J", 1280.00),
        ("K", 2560.00),
        ("L", 5120.00),
        ("M", 10240.00),
        ("N", 20480.00),
        ("O", 40960.00),
    )

    def classify(
        self,
        total_impulse_Ns: float,
    ) -> MotorClassification:
        """Return the applicable impulse class."""

        if total_impulse_Ns < 0:
            return MotorClassification(
                description=(
                    "Invalid negative total impulse."
                )
            )

        lower_limit = 0.0

        for class_name, upper_limit in (
            self.CLASS_LIMITS
        ):
            if total_impulse_Ns <= upper_limit:
                return MotorClassification(
                    motor_class=class_name,
                    lower_limit_Ns=lower_limit,
                    upper_limit_Ns=upper_limit,
                    description=(
                        f"{class_name} impulse class"
                    ),
                )

            lower_limit = upper_limit

        return MotorClassification(
            description=(
                "Above the O-class range."
            )
        )