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
#rociWordmark {
    color: #f0f4f7;
    font-size: 16pt;
    font-weight: 800;
    letter-spacing: 4px;
    padding-left: 8px;
}
#rociTagline {
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
