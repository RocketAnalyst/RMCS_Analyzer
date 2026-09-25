APPLICATION_STYLE = """
QMainWindow {
    background-color: #070c12;
    color: #dbe7ef;
}
QWidget {
    font-family: "Segoe UI";
    color: #dbe7ef;
}
QFrame#header {
    background-color: #0a121a;
    border-bottom: 1px solid #1d2a35;
}
#title {
    color: #f5f8fb;
    font-size: 17pt;
    font-weight: 650;
}
#subtitle {
    color: #6f8798;
    font-size: 9pt;
}
#versionLabel {
    color: #6e8394;
    font-size: 9pt;
    font-weight: 600;
}
#headerButton, #settingsButton {
    background-color: #0e1821;
    color: #c9d7e0;
    border: 1px solid #263b4a;
    border-radius: 5px;
    padding: 7px 14px;
    font-size: 9pt;
}
#headerButton:hover, #settingsButton:hover {
    background-color: #132332;
    border-color: #147fd1;
}
#settingsButton {
    padding: 0;
    font-size: 13pt;
}
#headerDescriptor {
    color: #71899a;
    font-size: 9pt;
}
#appWordmark {
    color: #f0f4f7;
    font-size: 16pt;
    font-weight: 800;
    letter-spacing: 4px;
    padding-left: 8px;
}
#appTagline {
    color: #7890a0;
    font-size: 6pt;
    font-weight: 600;
    letter-spacing: 1px;
}

#headerStatus {
    color: #58e28d;
    background-color: #0b2117;
    border: 1px solid #1d6240;
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 8pt;
    font-weight: 650;
}
#headerStatus[modified="true"] {
    color: #ff6f72;
    background-color: #2a1418;
    border-color: #78343b;
}

#content {
    background-color: #070c12;
}
#sidebarContainer, #workspaceContainer {
    background-color: transparent;
    border: none;
}
#panel {
    background-color: #0b141d;
    border: 1px solid #1d303e;
    border-radius: 7px;
}
#sideCard {
    background-color: #0c151e;
    border: 1px solid #1d303e;
    border-radius: 7px;
}
#sectionTitle {
    color: #b8c8d3;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
}
#infoRow {
    border-bottom: 1px solid #172630;
}
#infoLabel {
    color: #72899a;
    font-size: 8pt;
}
#infoValueEdit {
    background-color: #111c26;
    color: #dce7ee;
    border: 1px solid #263b49;
    border-radius: 4px;
    padding: 5px 7px;
    selection-background-color: #155f92;
}
#infoValueEdit:focus {
    border-color: #1788d9;
    background-color: #12212c;
}
#fileList {
    background-color: #081018;
    color: #b9c9d3;
    border: 1px solid #1c303d;
    border-radius: 5px;
    padding: 4px;
    font-size: 9pt;
}
#fileList::item {
    padding: 7px 8px;
    border-radius: 3px;
}
#fileList::item:selected {
    background-color: #0b5e96;
    color: #f2f9ff;
}
#fileList::item:hover:!selected {
    background-color: #11222f;
}
#brandingCard {
    background-color: transparent;
    border: none;
}

#workspaceTabs {
    background-color: transparent;
    border: none;
}
#workspaceTabs::pane {
    background-color: #081017;
    border: 1px solid #1b303e;
    border-radius: 0 0 6px 6px;
    top: -1px;
}
#workspaceTabs::tab-bar {
    left: 0px;
}
#workspaceTabs QTabBar::tab {
    background-color: #0d151d;
    color: #718798;
    border: 1px solid #1b303e;
    border-bottom: none;
    padding: 8px 17px;
    min-width: 88px;
    margin-right: 2px;
}
#workspaceTabs QTabBar::tab:first {
    border-top-left-radius: 5px;
}
#workspaceTabs QTabBar::tab:last {
    border-top-right-radius: 5px;
}
#workspaceTabs QTabBar::tab:hover {
    color: #bcd0dd;
    background-color: #11212d;
}
#workspaceTabs QTabBar::tab:selected {
    background-color: #0d6fbd;
    color: #ffffff;
    border-color: #1289df;
    font-weight: 650;
}

#thrustWorkspaceHeader {
    background-color: transparent;
    border: none;
}
#graphTitle {
    color: #e4edf3;
    font-size: 13pt;
    font-weight: 600;
}
#graphDescription {
    color: #637a89;
    font-size: 8pt;
}
#graphControls {
    background-color: transparent;
    border: none;
}
#graphToggle {
    color: #9db1be;
    font-size: 8pt;
}
#graphSettingsButton {
    background-color: #0d1821;
    color: #8fa6b5;
    border: 1px solid #263b48;
    border-radius: 4px;
    font-size: 12pt;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}
#graphSettingsButton:hover {
    color: #e4f0f7;
    border-color: #1788d9;
}
#playback {
    background-color: #0d1821;
    border: 1px solid #1d3341;
    border-radius: 6px;
}
#playbackButton {
    background-color: #10202b;
    color: #b8cad5;
    border: 1px solid #304655;
    border-radius: 18px;
    min-width: 34px;
    max-width: 34px;
    min-height: 30px;
    max-height: 30px;
}
#playbackButton:hover {
    background-color: #183040;
    border-color: #218cda;
}
#playButton {
    background-color: #0b75c9;
    color: white;
    border: 1px solid #1596e8;
    border-radius: 20px;
    min-width: 42px;
    max-width: 42px;
    min-height: 36px;
    max-height: 36px;
}
#playButton:hover {
    background-color: #1189df;
}
#timeLabel {
    color: #8399a8;
    font-size: 8pt;
}

#subPanel, #keyResultsPanel, #additionalMetricsPanel, #cstarPanel, #motorClassificationPanel {
    background-color: #0b151e;
    border: 1px solid #1e3442;
    border-radius: 7px;
}
#subPanelTitle, #motorClassificationTitle {
    color: #d7e4ec;
    font-size: 8pt;
    font-weight: 650;
}
#lowerPanelHeader {
    color: #d7e4ec;
    font-size: 8pt;
    font-weight: 650;
}
#videoPreview {
    background-color: #070e14;
    border: 1px solid #203440;
    border-radius: 5px;
}
#videoStatus {
    color: #6f8797;
    font-size: 7pt;
}
#videoOption {
    color: #8fa5b4;
    font-size: 7pt;
}
#videoControlGroup {
    background-color: #0d1922;
    border: 1px solid #263d4b;
    border-radius: 5px;
}
#videoControlLabel {
    color: #8fa5b4;
    font-size: 7pt;
    font-weight: 600;
}
#videoSyncSpin {
    background-color: #0d1922;
    color: #b7c8d2;
    border: 1px solid #29404e;
    border-radius: 4px;
    padding: 2px 5px;
    font-size: 7pt;
}
#videoRemoveButton {
    background-color: #101e28;
    color: #8fa5b4;
    border: 1px solid #29404e;
    border-radius: 4px;
    padding: 2px 7px;
}
#videoRemoveButton:hover {
    border-color: #c95d5d;
    color: #f0b0b0;
}
#videoPlaceholder {
    color: #5f7584;
    font-size: 8pt;
}
#loadVideoButton {
    background-color: #101e28;
    color: #8fa5b4;
    border: 1px solid #29404e;
    border-radius: 5px;
    padding: 6px 10px;
}
#exportButton {
    background-color: #101e28;
    color: #b7c8d2;
    border: 1px solid #29404e;
    border-radius: 5px;
    padding: 6px 9px;
    text-align: left;
}
#exportButton:hover {
    background-color: #152b3a;
    border-color: #218bd8;
    color: #eef7fc;
}
#exportIcon {
    color: #1594e8;
    font-size: 12pt;
    font-weight: 700;
}
#exportLabel {
    color: #b7c8d2;
    font-size: 8pt;
}

#metricCard {
    background-color: #0d1922;
    border: 1px solid #203744;
    border-radius: 6px;
}
#metricIcon {
    color: #8da6b5;
    font-size: 14pt;
    font-weight: 600;
    min-width: 25px;
}
#metricName {
    color: #9db0bc;
    font-size: 8pt;
}
#metricValue {
    color: #e6eff4;
    font-size: 12pt;
    font-weight: 650;
}
#metricUnit {
    color: #718695;
    font-size: 8pt;
}
#metricRow {
    background-color: transparent;
    border: none;
}
#metricValueSmall {
    color: #d7e5ed;
    font-size: 8pt;
}
#additionalMetricsPanel #metricName {
    color: #8fa5b3;
}
#additionalMetricsPanel #metricValueSmall {
    color: #dce8ee;
    font-size: 8pt;
}

#eventRow {
    background-color: #0a131b;
    border: 1px solid #132530;
    border-radius: 5px;
}
#eventDot {
    min-width: 7px;
    max-width: 7px;
    min-height: 7px;
    max-height: 7px;
    border-radius: 4px;
}
#eventDotIgnition { background-color: #21dc63; }
#eventDotPeak { background-color: #1589df; }
#eventDotBurnout { background-color: #ff4b4f; }
#eventName {
    color: #aabcc7;
    font-size: 8pt;
}
#eventValue {
    color: #e2edf2;
    font-size: 8pt;
}

#cstarInfoButton {
    background-color: transparent;
    color: #7f9aab;
    border: 1px solid #29404e;
    border-radius: 10px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
    font-weight: 700;
}
#cstarInfoButton:hover {
    color: #dceaf2;
    border-color: #218bd8;
}
#cstarValue {
    color: #e5eef3;
    font-size: 8pt;
    font-weight: 600;
}
#cstarUnavailable {
    color: #687e8d;
    font-size: 8pt;
}
#cstarDetail {
    color: #6f8594;
    font-size: 7pt;
}
#cstarAvailable {
    color: #57df8b;
}

#motorClassCard_neighbor {
    background-color: #0a141c;
    border: 1px solid #253b48;
    border-radius: 5px;
}
#motorClassCard_selected {
    background-color: #21d95f;
    border: 1px solid #48ed7d;
    border-radius: 5px;
}
#motorClassCardLabel {
    color: #b8cbd5;
    font-size: 12pt;
    font-weight: 600;
}
#motorClassCard_selected #motorClassCardLabel {
    color: #07140b;
    font-size: 15pt;
    font-weight: 750;
}
#motorClassificationImpulse {
    color: #dce8ee;
    font-size: 8pt;
}
#motorClassificationResult {
    color: #41e875;
    font-size: 14pt;
    font-weight: 700;
}
#motorClassificationRange {
    color: #d7e4eb;
    font-size: 8pt;
}
#motorClassificationNote {
    color: #6f8492;
    font-size: 7pt;
}

#footer {
    background-color: #080f16;
    border-top: 1px solid #1b2b37;
}
#footerLabel {
    color: #506775;
    font-size: 8pt;
}

#workspacePlaceholder {
    background-color: #080f15;
    border: none;
}
#plotHoverReadout {
    background-color: rgba(7, 13, 18, 235);
    color: #dce7ee;
    border: 1px solid #526b7a;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 8pt;
}

# -------------------------------------------------------------
# SETTINGS
# -------------------------------------------------------------
QDialog {
    background-color: #0a121a;
    color: #dbe7ef;
}
QTabWidget#settingsTabs::pane {
    background-color: #0b151e;
    border: 1px solid #1d303e;
    border-radius: 5px;
}
QTabWidget#settingsTabs QTabBar::tab {
    background-color: #0d151d;
    color: #718798;
    border: 1px solid #1b303e;
    padding: 8px 16px;
}
QTabWidget#settingsTabs QTabBar::tab:selected {
    background-color: #0d6fbd;
    color: #ffffff;
}
#settingsIntro {
    color: #7f96a5;
    font-size: 9pt;
}
QGroupBox {
    color: #cbd9e2;
    border: 1px solid #243a48;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #9fb3c0;
}
QLineEdit, QComboBox, QListWidget {
    background-color: #0d1922;
    color: #dce7ee;
    border: 1px solid #29404e;
    border-radius: 4px;
    padding: 5px 7px;
}
QListWidget::item {
    padding: 5px 4px;
}
QListWidget::item:hover {
    background-color: #112532;
}
QCheckBox {
    color: #aebfca;
}
#videoOverlayOptionsButton {
    background-color: #101e28;
    color: #8fa5b4;
    border: 1px solid #29404e;
    border-radius: 5px;
    padding: 6px 9px;
}
#videoOverlayOptionsButton:hover {
    background-color: #152b3a;
    border-color: #218bd8;
    color: #eef7fc;
}
#videoPdfFrameLabel {
    color: #b7c8d2;
    font-size: 7pt;
}
#videoPdfFrameButton {
    background-color: #101e28;
    color: #8fa5b4;
    border: 1px solid #29404e;
    border-radius: 4px;
    padding: 3px 7px;
    font-size: 7pt;
}
#videoPdfFrameButton:hover {
    background-color: #183040;
    border-color: #218bd8;
    color: #ffffff;
}
#videoPopoutButton {
    background-color: #101e28;
    color: #8fa5b4;
    border: 1px solid #29404e;
    border-radius: 5px;
    padding: 6px 10px;
}
#videoPopoutButton:hover {
    background-color: #152b3a;
    border-color: #218bd8;
    color: #eef7fc;
}
#videoSyncStepButton {
    background-color: #101e28;
    color: #9eb2be;
    border: 1px solid #29404e;
    border-radius: 4px;
    padding: 0;
}
#videoSyncStepButton:hover {
    background-color: #183040;
    border-color: #218bd8;
    color: #ffffff;
}

QPushButton:disabled {
    color: #526572;
    background-color: #0d151d;
    border-color: #1b2c37;
}
QScrollBar:vertical {
    background: #0a1118;
    width: 9px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #263e4d;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


# -----------------------------------------------------------------
# LIGHT THEME
# -----------------------------------------------------------------
LIGHT_THEME_STYLE = r"""

QMainWindow {
    background-color: #eef2f5;
    color: #1d2b36;
}

QWidget {
    font-family: "Segoe UI";
    color: #1d2b36;
}

QFrame#header {
    background-color: #ffffff;
    border-bottom: 1px solid #b8c6d0;
}

#title {
    color: #162b39;
    font-size: 17pt;
    font-weight: 650;
}

#subtitle {
    color: #4d6573;
    font-size: 9pt;
}

#versionLabel {
    color: #4d6573;
    font-size: 9pt;
    font-weight: 600;
}

#headerButton, #settingsButton {
    background-color: #f7f9fb;
    color: #263f4d;
    border: 1px solid #9eafbb;
    border-radius: 5px;
    padding: 7px 14px;
    font-size: 9pt;
}

#headerButton:hover, #settingsButton:hover {
    background-color: #e2f0f8;
    border-color: #147fd1;
}

#settingsButton {
    padding: 0;
    font-size: 13pt;
}

#headerDescriptor {
    color: #4d6573;
    font-size: 9pt;
}

#appWordmark {
    color: #162b39;
    font-size: 16pt;
    font-weight: 800;
    letter-spacing: 4px;
    padding-left: 8px;
}

#appTagline {
    color: #4d6573;
    font-size: 6pt;
    font-weight: 600;
    letter-spacing: 1px;
}


#headerStatus {
    color: #16864a;
    background-color: #edf9f2;
    border: 1px solid #72c59a;
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 8pt;
    font-weight: 650;
}

#headerStatus[modified="true"] {
    color: #b83c43;
    background-color: #fff1f2;
    border-color: #d99398;
}


#content {
    background-color: #eef2f5;
}

#sidebarContainer, #workspaceContainer {
    background-color: transparent;
    border: none;
}

#panel {
    background-color: #ffffff;
    border: 1px solid #aebfca;
    border-radius: 7px;
}

#sideCard {
    background-color: #ffffff;
    border: 1px solid #aebfca;
    border-radius: 7px;
}

#sectionTitle {
    color: #2d4655;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
}

#infoRow {
    border-bottom: 1px solid #d2dce3;
}

#infoLabel {
    color: #4b6371;
    font-size: 8pt;
}

#infoValueEdit {
    background-color: #f6f9fb;
    color: #253844;
    border: 1px solid #9fb1bd;
    border-radius: 4px;
    padding: 5px 7px;
    selection-background-color: #155f92;
}

#infoValueEdit:focus {
    border-color: #1788d9;
    background-color: #ffffff;
}

#fileList {
    background-color: #f6f9fb;
    color: #304b5a;
    border: 1px solid #aebfca;
    border-radius: 5px;
    padding: 4px;
    font-size: 9pt;
}

#fileList::item {
    padding: 7px 8px;
    border-radius: 3px;
}

#fileList::item:selected {
    background-color: #0b5e96;
    color: #ffffff;
}

#fileList::item:hover:!selected {
    background-color: #e9f3f9;
}

#brandingCard {
    background-color: transparent;
    border: none;
}


#workspaceTabs {
    background-color: transparent;
    border: none;
}

#workspaceTabs::pane {
    background-color: #ffffff;
    border: 1px solid #aebfca;
    border-radius: 0 0 6px 6px;
    top: -1px;
}

#workspaceTabs::tab-bar {
    left: 0px;
}

#workspaceTabs QTabBar::tab {
    background-color: #e7edf1;
    color: #4b6371;
    border: 1px solid #aebfca;
    border-bottom: none;
    padding: 8px 17px;
    min-width: 88px;
    margin-right: 2px;
}

#workspaceTabs QTabBar::tab:first {
    border-top-left-radius: 5px;
}

#workspaceTabs QTabBar::tab:last {
    border-top-right-radius: 5px;
}

#workspaceTabs QTabBar::tab:hover {
    color: #243f4e;
    background-color: #dbe8ef;
}

#workspaceTabs QTabBar::tab:selected {
    background-color: #0d6fbd;
    color: #ffffff;
    border-color: #1289df;
    font-weight: 650;
}


#thrustWorkspaceHeader {
    background-color: transparent;
    border: none;
}

#graphTitle {
    color: #213b4a;
    font-size: 13pt;
    font-weight: 600;
}

#graphDescription {
    color: #506875;
    font-size: 8pt;
}

#graphControls {
    background-color: transparent;
    border: none;
}

#graphToggle {
    color: #425b69;
    font-size: 8pt;
}

#graphSettingsButton {
    background-color: #e8eef2;
    color: #425b69;
    border: 1px solid #9fb1bd;
    border-radius: 4px;
    font-size: 12pt;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}

#graphSettingsButton:hover {
    color: #23485c;
    border-color: #1788d9;
}

#playback {
    background-color: #e8eef2;
    border: 1px solid #aebfca;
    border-radius: 6px;
}

#playbackButton {
    background-color: #ffffff;
    color: #425b69;
    border: 1px solid #304655;
    border-radius: 18px;
    min-width: 34px;
    max-width: 34px;
    min-height: 30px;
    max-height: 30px;
}

#playbackButton:hover {
    background-color: #dbe8ef;
    border-color: #218cda;
}

#playButton {
    background-color: #0b75c9;
    color: white;
    border: 1px solid #1596e8;
    border-radius: 20px;
    min-width: 42px;
    max-width: 42px;
    min-height: 36px;
    max-height: 36px;
}

#playButton:hover {
    background-color: #1189df;
}

#timeLabel {
    color: #506875;
    font-size: 8pt;
}


#subPanel, #keyResultsPanel, #additionalMetricsPanel, #cstarPanel, #motorClassificationPanel {
    background-color: #ffffff;
    border: 1px solid #aebfca;
    border-radius: 7px;
}

#subPanelTitle, #motorClassificationTitle {
    color: #304b5a;
    font-size: 8pt;
    font-weight: 650;
}

#lowerPanelHeader {
    color: #304b5a;
    font-size: 8pt;
    font-weight: 650;
}

#videoPreview {
    background-color: #ffffff;
    border: 1px solid #b1c1cb;
    border-radius: 5px;
}

#videoStatus {
    color: #4b6371;
    font-size: 7pt;
}

#videoOption {
    color: #425b69;
    font-size: 7pt;
}

#videoControlGroup {
    background-color: #f4f7f9;
    border: 1px solid #9fb1bd;
    border-radius: 5px;
}

#videoControlLabel {
    color: #425b69;
    font-size: 7pt;
    font-weight: 600;
}

#videoSyncSpin {
    background-color: #f4f7f9;
    color: #2d4655;
    border: 1px solid #94a8b4;
    border-radius: 4px;
    padding: 2px 5px;
    font-size: 7pt;
}

#videoRemoveButton {
    background-color: #f4f7f9;
    color: #4d6573;
    border: 1px solid #94a8b4;
    border-radius: 4px;
    padding: 2px 7px;
}

#videoRemoveButton:hover {
    border-color: #c95d5d;
    color: #b83c43;
}

#videoPlaceholder {
    color: #526a77;
    font-size: 8pt;
}

#loadVideoButton {
    background-color: #f4f7f9;
    color: #4d6573;
    border: 1px solid #94a8b4;
    border-radius: 5px;
    padding: 6px 10px;
}

#exportButton {
    background-color: #f4f7f9;
    color: #2d4655;
    border: 1px solid #94a8b4;
    border-radius: 5px;
    padding: 6px 9px;
    text-align: left;
}

#exportButton:hover {
    background-color: #e2f0f8;
    border-color: #218bd8;
    color: #2d4655;
}

#exportIcon {
    color: #1594e8;
    font-size: 12pt;
    font-weight: 700;
}

#exportLabel {
    color: #2d4655;
    font-size: 8pt;
}


#metricCard {
    background-color: #f4f7f9;
    border: 1px solid #b1c1cb;
    border-radius: 6px;
}

#metricIcon {
    color: #536b79;
    font-size: 14pt;
    font-weight: 600;
    min-width: 25px;
}

#metricName {
    color: #425b69;
    font-size: 8pt;
}

#metricValue {
    color: #304b5a;
    font-size: 12pt;
    font-weight: 650;
}

#metricUnit {
    color: #4b6371;
    font-size: 8pt;
}

#metricRow {
    background-color: transparent;
    border: none;
}

#metricValueSmall {
    color: #304b5a;
    font-size: 8pt;
}

#additionalMetricsPanel #metricName {
    color: #425b69;
}

#additionalMetricsPanel #metricValueSmall {
    color: #304b5a;
    font-size: 8pt;
}


#eventRow {
    background-color: #ffffff;
    border: 1px solid #aebdc7;
    border-radius: 5px;
}

#eventDot {
    min-width: 7px;
    max-width: 7px;
    min-height: 7px;
    max-height: 7px;
    border-radius: 4px;
}

#eventDotIgnition { background-color: #21dc63; }

#eventDotPeak { background-color: #1589df; }

#eventDotBurnout { background-color: #ff4b4f; }

#eventName {
    color: #304b5a;
    font-size: 8pt;
}

#eventValue {
    color: #304b5a;
    font-size: 8pt;
}


#cstarInfoButton {
    background-color: transparent;
    color: #4b6371;
    border: 1px solid #94a8b4;
    border-radius: 10px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
    font-weight: 700;
}

#cstarInfoButton:hover {
    color: #304b5a;
    border-color: #218bd8;
}

#cstarValue {
    color: #304b5a;
    font-size: 8pt;
    font-weight: 600;
}

#cstarUnavailable {
    color: #506875;
    font-size: 8pt;
}

#cstarDetail {
    color: #506875;
    font-size: 7pt;
}

#cstarAvailable {
    color: #16864a;
}


#motorClassCard_neighbor {
    background-color: #ffffff;
    border: 1px solid #9fb1bd;
    border-radius: 5px;
}

#motorClassCard_selected {
    background-color: #21d95f;
    border: 1px solid #48ed7d;
    border-radius: 5px;
}

#motorClassCardLabel {
    color: #425b69;
    font-size: 12pt;
    font-weight: 600;
}

#motorClassCard_selected #motorClassCardLabel {
    color: #ffffff;
    font-size: 15pt;
    font-weight: 750;
}

#motorClassificationImpulse {
    color: #304b5a;
    font-size: 8pt;
}

#motorClassificationResult {
    color: #16a84a;
    font-size: 14pt;
    font-weight: 700;
}

#motorClassificationRange {
    color: #304b5a;
    font-size: 8pt;
}

#motorClassificationNote {
    color: #506875;
    font-size: 7pt;
}


#footer {
    background-color: #f7f9fb;
    border-top: 1px solid #c5d1d9;
}

#footerLabel {
    color: #425b69;
    font-size: 8pt;
}


#workspacePlaceholder {
    background-color: #ffffff;
    border: none;
}

#plotHoverReadout {
    background-color: rgba(255, 255, 255, 245);
    color: #263a46;
    border: 1px solid #526b7a;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 8pt;
}


# -------------------------------------------------------------
# SETTINGS
# -------------------------------------------------------------
QDialog {
    background-color: #ffffff;
    color: #1d2b36;
}

QTabWidget#settingsTabs::pane {
    background-color: #ffffff;
    border: 1px solid #aebfca;
    border-radius: 5px;
}

QTabWidget#settingsTabs QTabBar::tab {
    background-color: #e7edf1;
    color: #4b6371;
    border: 1px solid #aebfca;
    padding: 8px 16px;
}

QTabWidget#settingsTabs QTabBar::tab:selected {
    background-color: #0d6fbd;
    color: #ffffff;
}

#settingsIntro {
    color: #4b6371;
    font-size: 9pt;
}

QGroupBox {
    color: #304b5a;
    border: 1px solid #9fb1bc;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #425b69;
}

QLineEdit, QComboBox, QListWidget {
    background-color: #f4f7f9;
    color: #253844;
    border: 1px solid #94a8b4;
    border-radius: 4px;
    padding: 5px 7px;
}

QListWidget::item {
    padding: 5px 4px;
}

QListWidget::item:hover {
    background-color: #112532;
}

QCheckBox {
    color: #425b69;
}

#videoOverlayOptionsButton {
    background-color: #f4f7f9;
    color: #4d6573;
    border: 1px solid #94a8b4;
    border-radius: 5px;
    padding: 6px 9px;
}

#videoOverlayOptionsButton:hover {
    background-color: #e2f0f8;
    border-color: #218bd8;
    color: #2d4655;
}

#videoPdfFrameLabel {
    color: #2d4655;
    font-size: 7pt;
}

#videoPdfFrameButton {
    background-color: #f4f7f9;
    color: #4d6573;
    border: 1px solid #94a8b4;
    border-radius: 4px;
    padding: 3px 7px;
    font-size: 7pt;
}

#videoPdfFrameButton:hover {
    background-color: #dbe8ef;
    border-color: #218bd8;
    color: #2d4655;
}

#videoPopoutButton {
    background-color: #f4f7f9;
    color: #4d6573;
    border: 1px solid #94a8b4;
    border-radius: 5px;
    padding: 6px 10px;
}

#videoPopoutButton:hover {
    background-color: #e2f0f8;
    border-color: #218bd8;
    color: #2d4655;
}

#videoSyncStepButton {
    background-color: #f4f7f9;
    color: #425b69;
    border: 1px solid #94a8b4;
    border-radius: 4px;
    padding: 0;
}

#videoSyncStepButton:hover {
    background-color: #dbe8ef;
    border-color: #218bd8;
    color: #2d4655;
}


QPushButton:disabled {
    color: #667b88;
    background-color: #e7edf1;
    border-color: #aebfca;
}

QScrollBar:vertical {
    background: #ffffff;
    width: 9px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #8ea1ad;
    min-height: 30px;
    border-radius: 4px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Light-mode contrast refinements */
QPushButton, QToolButton { color: #2d4655; }
QPushButton:hover, QToolButton:hover { color: #213d4d; }
QLabel { color: #2d4655; }
QCheckBox::indicator, QRadioButton::indicator { border: 1px solid #8ea2ae; background: #ffffff; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background: #1683d2; border-color: #1683d2; }
QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { border: none; }

/* Native/light-mode fallbacks */
QDialog, QMainWindow, QWidget { color: #253844; }
QToolTip { background: #ffffff; color: #253844; border: 1px solid #9fb1bd; }
QMenu { background: #ffffff; color: #253844; border: 1px solid #aebfca; }
QMenu::item:selected { background: #e9f3f9; color: #23485c; }
QComboBox QAbstractItemView { background: #ffffff; color: #253844; selection-background-color: #1683d2; selection-color: #ffffff; }
QTableWidget, QTableView { background: #ffffff; color: #253844; gridline-color: #d9e2e8; }
QHeaderView::section { background: #e7edf1; color: #2d4655; border: 1px solid #aebfca; }
QPushButton { background: #f7f9fb; color: #263f4d; border: 1px solid #9fb1bd; }
QPushButton:hover { background: #e2f0f8; border-color: #1683d2; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #f6f9fb; color: #253844; border: 1px solid #9fb1bd; }
QCheckBox, QRadioButton { color: #3e5866; }
QScrollBar:vertical, QScrollBar:horizontal { background: #edf2f5; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #b8c8d2; }

#eventsButton { background: #f7f9fb; color: #263f4d; border: 1px solid #9fb1bd; }
#eventsButton:hover { background: #e2f0f8; border-color: #1683d2; }
#plotHoverReadout { background: rgba(255,255,255,245); color: #263a46; border-color: #718895; }
#brandingRmcs, #brandingAnalyzer { color: #162b39; }
#brandingTagline { color: #4d6573; }
#compareLegendLabel { color: #304b5a; }

/* Final light-theme contrast pass */
#content { background-color: #eef2f5; }
#panel, #sideCard { background-color: #ffffff; border-color: #aebfca; }
#workspaceTabs::pane { background-color: #ffffff; border-color: #aebfca; }
#subPanel, #keyResultsPanel, #additionalMetricsPanel, #cstarPanel, #motorClassificationPanel { background-color: #f9fbfc; border-color: #aebfca; }
#metricCard { background-color: #f1f5f7; border-color: #b2c1ca; }
#eventRow { background-color: #f7f9fa; border-color: #b4c3cc; }
#playback { background-color: #e8eef2; border-color: #aebfca; }
#videoControlGroup { background-color: #eef3f6; border-color: #aebdc7; }
#exportButton, #loadVideoButton, #videoPopoutButton, #videoOverlayOptionsButton, #videoPdfFrameButton, #videoSyncStepButton { background-color: #f1f5f7; border-color: #9fb1bd; color: #304b5a; }
#sectionTitle, #subPanelTitle, #motorClassificationTitle, #lowerPanelHeader { color: #294655; }
#infoLabel, #metricName, #metricUnit, #videoStatus, #videoOption, #videoControlLabel, #footerLabel, #graphDescription { color: #4b6371; }
#metricValue, #metricValueSmall, #eventName, #eventValue, #cstarValue, #motorClassificationImpulse, #motorClassificationRange { color: #263f4d; }
#cstarUnavailable, #cstarDetail, #motorClassificationNote { color: #526a77; }
#footer { background-color: #e8eef2; border-top-color: #b8c6d0; }
#workspacePlaceholder { background-color: #ffffff; }


/* Light theme polish - final contrast tuning */
#content { background-color: #edf1f4; }

/* Stronger panel hierarchy without heavy borders */
#panel, #sideCard { background-color: #ffffff; border-color: #9eafb9; }
#subPanel, #keyResultsPanel, #additionalMetricsPanel, #cstarPanel, #motorClassificationPanel {
    background-color: #f7f9fa;
    border-color: #a4b4bd;
}
#metricCard { background-color: #eef3f6; border-color: #a8b8c2; }
#eventRow { background-color: #f4f7f8; border-color: #aab9c2; }
#playback { background-color: #e5ebef; border-color: #9eafb9; }
#videoControlGroup { background-color: #ebf0f3; border-color: #a2b1bb; }

/* Primary / secondary text */
QWidget { color: #243944; }
QLabel { color: #304b59; }
#infoLabel, #metricName, #metricUnit, #videoStatus, #videoOption,
#videoControlLabel, #footerLabel, #graphDescription, #graphToggle {
    color: #405a68;
}
#sectionTitle, #subPanelTitle, #motorClassificationTitle, #lowerPanelHeader,
#graphTitle { color: #243f4d; }
#metricValue, #metricValueSmall, #eventName, #eventValue, #cstarValue,
#motorClassificationImpulse, #motorClassificationRange { color: #1f3541; }
#cstarUnavailable, #cstarDetail, #motorClassificationNote { color: #49616e; }

/* Controls */
QPushButton, QToolButton {
    background-color: #f4f7f9;
    color: #294653;
    border-color: #94a7b2;
}
QPushButton:hover, QToolButton:hover {
    background-color: #e1edf4;
    color: #1d3d4c;
    border-color: #1683d2;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #d4e5ef;
}
QPushButton:disabled, QToolButton:disabled {
    color: #71838e;
    background-color: #e9eef1;
    border-color: #b4c1c8;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #f8fafb;
    color: #263f4c;
    border-color: #91a5b0;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #1683d2;
}

/* Workspace navigation */
#workspaceTabs QTabBar::tab {
    background-color: #e9eef1;
    color: #526875;
    border-color: #b0bec6;
}
#workspaceTabs QTabBar::tab:hover {
    background-color: #dde8ee;
    color: #294958;
}
#workspaceTabs QTabBar::tab:selected {
    background-color: #0d6fbd;
    color: #ffffff;
    border-color: #1289df;
}

/* Settings dialog: subtle surface separation */
QDialog { background-color: #f1f4f6; color: #243944; }
QDialog QWidget { color: #304b59; }
QTabWidget#settingsTabs::pane {
    background-color: #f7f9fa;
    border-color: #a3b2bb;
}
QTabWidget#settingsTabs QTabBar::tab {
    background-color: #e3e9ed;
    color: #4a626f;
    border-color: #aab8c0;
}
QTabWidget#settingsTabs QTabBar::tab:selected {
    background-color: #9aa6ad;
    color: #152b37;
}
QGroupBox {
    color: #304b59;
    border-color: #9eafb9;
}
QGroupBox::title { color: #3b5664; }

/* Lower panels and export controls */
#exportButton, #loadVideoButton, #videoPopoutButton,
#videoOverlayOptionsButton, #videoPdfFrameButton, #videoSyncStepButton {
    background-color: #f1f5f7;
    border-color: #94a7b2;
    color: #294653;
}
#exportButton:hover, #loadVideoButton:hover, #videoPopoutButton:hover,
#videoOverlayOptionsButton:hover, #videoPdfFrameButton:hover, #videoSyncStepButton:hover {
    background-color: #e1edf4;
    border-color: #1683d2;
}

/* Footer */
#footer { background-color: #e4eaee; border-top-color: #aebcc5; }

/* Plot/graph controls */
#graphSettingsButton { background-color: #f1f5f7; color: #3f5967; border-color: #98aab4; }
#graphSettingsButton:hover { background-color: #e1edf4; color: #1d3d4c; }
#eventsButton { background-color: #f1f5f7; color: #294653; border-color: #94a7b2; }
#eventsButton:hover { background-color: #e1edf4; color: #1d3d4c; border-color: #1683d2; }
#plotHoverReadout { background: rgba(255,255,255,245); color: #243944; border-color: #697f8b; }

"""



def application_style(theme="dark"):
    """Return one complete, standalone stylesheet for the requested theme."""
    if str(theme or "dark").lower() == "light":
        return LIGHT_THEME_STYLE
    return APPLICATION_STYLE
