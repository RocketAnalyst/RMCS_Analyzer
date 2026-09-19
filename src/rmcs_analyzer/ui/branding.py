from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


class Branding(QFrame):
    """
    RMCS Analyzer branding component.

    Modes:

        compact
            Used in the application header.

        full
            Used in the lower-left application area.
    """

    BLUE = "#1598FF"
    WHITE = "#F2F6FA"
    MUTED = "#7FA4C8"

    def __init__(
        self,
        mode="compact",
        parent=None,
    ):
        super().__init__(parent)

        self.mode = mode

        if mode == "full":
            self.build_full_branding()
        else:
            self.build_compact_branding()

    # =============================================================
    # ROCKET GRAPHIC
    # =============================================================

    def create_rocket_pixmap(
        self,
        width,
        height,
        color,
    ):
        """
        Render the RMCS Analyzer rocket mark.
        """

        svg = f"""
        <svg
            width="{width}"
            height="{height}"
            viewBox="0 0 100 160"
            xmlns="http://www.w3.org/2000/svg"
        >

            <g
                fill="none"
                stroke="{color}"
                stroke-width="4.5"
                stroke-linecap="round"
                stroke-linejoin="round"
            >

                <!-- Rocket body -->

                <path
                    d="
                        M50 4
                        C35 19 25 40 23 65
                        L23 111
                        L50 139
                        L77 111
                        L77 65
                        C75 40 65 19 50 4
                        Z
                    "
                />

                <!-- Center line -->

                <path
                    d="
                        M50 5
                        L50 139
                    "
                />

                <!-- Window -->

                <circle
                    cx="50"
                    cy="48"
                    r="9"
                />

                <!-- Left fin -->

                <path
                    d="
                        M23 83
                        L5 105
                        L23 108
                    "
                />

                <!-- Right fin -->

                <path
                    d="
                        M77 83
                        L95 105
                        L77 108
                    "
                />

                <!-- Exhaust -->

                <path
                    d="
                        M37 137
                        C37 146 31 153 25 158
                    "
                />

                <path
                    d="
                        M63 137
                        C63 146 69 153 75 158
                    "
                />

            </g>

            <!-- Blue exhaust flame -->

            <path
                d="
                    M43 137
                    C43 146 47 153 50 158
                    C53 153 57 146 57 137
                "
                fill="{self.BLUE}"
                stroke="none"
            />

        </svg>
        """

        renderer = QSvgRenderer(
            QByteArray(
                svg.encode("utf-8")
            )
        )

        pixmap = QPixmap(
            width,
            height,
        )

        pixmap.fill(
            Qt.GlobalColor.transparent
        )

        painter = QPainter(
            pixmap
        )

        renderer.render(
            painter
        )

        painter.end()

        return pixmap

    # =============================================================
    # COMPACT HEADER BRANDING
    # =============================================================

    def build_compact_branding(self):
        """
        Build the compact header version of the logo.
        """

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            8
        )

        # ---------------------------------------------------------
        # Small rocket
        # ---------------------------------------------------------

        rocket = QLabel()

        rocket.setPixmap(
            self.create_rocket_pixmap(
                26,
                42,
                self.BLUE,
            )
        )

        rocket.setFixedSize(
            26,
            42,
        )

        rocket.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            rocket
        )

        # ---------------------------------------------------------
        # Name and subtitle
        # ---------------------------------------------------------

        text_layout = QVBoxLayout()

        text_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        text_layout.setSpacing(
            1
        )

        title_row = QHBoxLayout()

        title_row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        title_row.setSpacing(
            7
        )

        title = QLabel(
            "RMCS Analyzer"
        )

        title.setObjectName(
            "title"
        )

        version = QLabel(
            "v0.1.0"
        )

        version.setObjectName(
            "versionLabel"
        )

        title_row.addWidget(
            title
        )

        title_row.addWidget(
            version
        )

        text_layout.addLayout(
            title_row
        )

        # The application descriptor is rendered in the center of the
        # header to match the dashboard reference. Keep the compact
        # brand focused on the product name and version.
        

        layout.addLayout(
            text_layout
        )

    # =============================================================
    # FULL APPLICATION BRANDING
    # =============================================================

    def build_full_branding(self):
        """
        Build the full RMCS Analyzer logo for the lower-left
        portion of the application.
        """

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            8,
            6,
            6,
            6,
        )

        layout.setSpacing(
            9
        )

        # ---------------------------------------------------------
        # Rocket mark
        # ---------------------------------------------------------

        rocket = QLabel()

        rocket.setPixmap(
            self.create_rocket_pixmap(
                50,
                82,
                self.WHITE,
            )
        )

        rocket.setFixedSize(
            50,
            82,
        )

        rocket.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            rocket,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        # ---------------------------------------------------------
        # Wordmark
        # ---------------------------------------------------------

        wordmark_layout = QVBoxLayout()

        wordmark_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        wordmark_layout.setSpacing(
            0
        )

        rmcs = QLabel(
            "RMCS"
        )

        rmcs.setStyleSheet(
            """
            QLabel {
                color: #F2F6FA;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 2px;
            }
            """
        )

        analyzer = QLabel(
            "ANALYZER"
        )

        analyzer.setStyleSheet(
            """
            QLabel {
                color: #F2F6FA;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            """
        )

        tagline = QLabel(
            "MEASURE  •  ANALYZE  •  ADVANCE"
        )

        tagline.setStyleSheet(
            """
            QLabel {
                color: #7FA4C8;
                font-size: 7px;
                font-weight: 600;
                letter-spacing: 0.8px;
            }
            """
        )

        wordmark_layout.addWidget(
            rmcs
        )

        wordmark_layout.addWidget(
            analyzer
        )

        wordmark_layout.addSpacing(
            4
        )

        wordmark_layout.addWidget(
            tagline
        )

        layout.addLayout(
            wordmark_layout
        )

        layout.addStretch()