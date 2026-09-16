APPLICATION_STYLE = """
QMainWindow {
    background-color: #080e14;
}

QWidget {
    font-family: "Segoe UI";
}

#header {
    background-color: #101820;
    border-bottom: 1px solid #26333f;
}

#title {
    color: #f1f5f8;
    font-size: 23px;
    font-weight: 600;
}

#subtitle {
    color: #7f94a8;
    font-size: 12px;
}

#headerButton {
    background-color: #17232e;
    color: #d8e3eb;
    border: 1px solid #314452;
    border-radius: 5px;
    padding: 8px 15px;
    font-size: 12px;
}

#headerButton:hover {
    background-color: #1e3140;
    border-color: #3e8ed0;
}

#settingsButton {
    background-color: #17232e;
    color: #a9bdcc;
    border: 1px solid #314452;
    border-radius: 5px;
    font-size: 17px;
}

#settingsButton:hover {
    background-color: #1e3140;
}

#content {
    background-color: #080e14;
}

#panel {
    background-color: #0e161e;
    border: 1px solid #26343f;
    border-radius: 7px;
}

#sectionTitle {
    color: #a9bac8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

#infoRow {
    border-bottom: 1px solid #1b2730;
}

#infoLabel {
    color: #687d8d;
    font-size: 10px;
}

#infoValue {
    color: #d9e3ea;
    font-size: 13px;
}

#fileList {
    background-color: #0a1118;
    color: #aebdca;
    border: 1px solid #202e38;
    border-radius: 5px;
    padding: 4px;
    font-size: 12px;
}

#fileList::item {
    padding: 7px;
    border-radius: 3px;
}

#fileList::item:selected {
    background-color: #15344c;
    color: #e7f4ff;
}

#graphPlaceholder {
    background-color: #080e13;
    border: 1px solid #1d2a34;
    border-radius: 5px;
}

#graphTitle {
    color: #8fa4b4;
    font-size: 19px;
    font-weight: 500;
}

#graphDescription {
    color: #536977;
    font-size: 12px;
}

#playback {
    background-color: #101a23;
    border: 1px solid #263640;
    border-radius: 5px;
}

#playbackButton {
    background-color: #17242e;
    color: #b6c7d2;
    border: 1px solid #344753;
    border-radius: 18px;
    min-width: 34px;
    max-width: 34px;
    min-height: 30px;
    max-height: 30px;
}

#playbackButton:hover {
    background-color: #203542;
}

#playButton {
    background-color: #0d6fbd;
    color: white;
    border: 1px solid #1689df;
    border-radius: 20px;
    min-width: 42px;
    max-width: 42px;
    min-height: 36px;
    max-height: 36px;
}

#playButton:hover {
    background-color: #1183d4;
}

#timeLabel {
    color: #8296a5;
    font-size: 12px;
}

#metricCard {
    background-color: #111c25;
    border: 1px solid #243540;
    border-radius: 5px;
}

#metricName {
    color: #8296a5;
    font-size: 11px;
}

#metricValue {
    color: #e1ebf2;
    font-size: 17px;
    font-weight: 600;
}

#metricUnit {
    color: #607787;
    font-size: 10px;
}

#eventRow {
    background-color: #0b131a;
    border-radius: 4px;
}

#eventName {
    color: #91a4b1;
    font-size: 11px;
}

#eventValue {
    color: #c8d5dd;
    font-size: 11px;
}

#statusLabel {
    background-color: #10251d;
    color: #59c992;
    border: 1px solid #1d4d39;
    border-radius: 5px;
    padding: 8px;
    font-size: 11px;
}

#footer {
    background-color: #0b1219;
    border-top: 1px solid #1d2a34;
}

#footerLabel {
    color: #4e6473;
    font-size: 10px;
}
"""