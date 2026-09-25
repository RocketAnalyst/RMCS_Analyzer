"""Cross-platform GitHub Releases updater for RMCS Analyzer.

The application performs the version check in a worker thread so startup and
manual checks never block the Qt event loop.  The actual installation step is
platform-specific: Windows launches the signed/packaged Inno Setup installer,
while macOS uses a ZIP containing the .app bundle and a small detached helper
that waits for RMCS Analyzer to exit before replacing the installed bundle.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QProgressDialog,
)

from .app_info import APP_NAME, APP_VERSION, GITHUB_RELEASES_API


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    release_name: str
    release_notes: str
    release_url: str
    asset_name: str
    asset_url: str
    asset_size: int


class UpdateCheckWorker(QThread):
    update_found = Signal(object)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def run(self):
        try:
            request = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={
                    "User-Agent": f"{APP_NAME}/{APP_VERSION}",
                    "Accept": "application/vnd.github+json",
                },
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if payload.get("draft") or payload.get("prerelease"):
                self.no_update.emit()
                return

            tag = str(payload.get("tag_name", "")).strip()
            latest = _normalize_version(tag)
            current = _normalize_version(self.current_version)
            if latest is None or current is None:
                raise ValueError("The release version could not be interpreted.")

            if not _is_newer(latest, current):
                self.no_update.emit()
                return

            asset = _select_platform_asset(payload.get("assets", []), latest)
            if asset is None:
                raise ValueError(
                    "A compatible update package was not found for this operating system."
                )

            self.update_found.emit(
                UpdateInfo(
                    version=latest,
                    release_name=str(payload.get("name") or f"v{latest}"),
                    release_notes=str(payload.get("body") or "").strip(),
                    release_url=str(payload.get("html_url") or ""),
                    asset_name=str(asset.get("name") or ""),
                    asset_url=str(asset.get("browser_download_url") or ""),
                    asset_size=int(asset.get("size") or 0),
                )
            )
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self.error.emit("No published RMCS Analyzer releases were found.")
            else:
                self.error.emit(f"Update server returned HTTP {exc.code}.")
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            self.error.emit(f"Could not reach the update server.\n\n{reason}")
        except Exception as exc:
            self.error.emit(f"Could not check for updates.\n\n{exc}")


class UpdateDownloadWorker(QThread):
    progress = Signal(int)
    completed = Signal(str)
    error = Signal(str)

    def __init__(self, update: UpdateInfo, parent=None):
        super().__init__(parent)
        self.update = update
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def run(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="rmcs_analyzer_update_"))
        destination = temp_dir / self.update.asset_name
        try:
            request = urllib.request.Request(
                self.update.asset_url,
                headers={
                    "User-Agent": f"{APP_NAME}/{APP_VERSION}",
                    "Accept": "application/octet-stream",
                },
            )
            with urllib.request.urlopen(request, timeout=30) as response, destination.open("wb") as output:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                while True:
                    if self._cancel_requested:
                        raise InterruptedError("Update download cancelled.")
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    output.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        self.progress.emit(min(100, int(downloaded * 100 / total)))

            if not destination.exists() or destination.stat().st_size == 0:
                raise IOError("The downloaded update file was empty.")

            self.progress.emit(100)
            self.completed.emit(str(destination))
        except InterruptedError:
            _remove_tree(temp_dir)
        except Exception as exc:
            _remove_tree(temp_dir)
            self.error.emit(f"The update could not be downloaded.\n\n{exc}")


class UpdateManager:
    """Owns update checks, update dialogs, downloads, and installation."""

    def __init__(self, parent=None):
        self.parent = parent
        self._check_worker = None
        self._download_worker = None
        self._progress_dialog = None
        self._checking = False
        self._installing = False

    def check_for_updates(self, parent=None, manual=True):
        if self._checking or self._installing:
            return

        self.parent = parent or self.parent
        self._checking = True
        worker = UpdateCheckWorker(APP_VERSION, self.parent)
        self._check_worker = worker
        worker.update_found.connect(lambda update: self._on_update_found(update, manual))
        worker.no_update.connect(lambda: self._on_no_update(manual))
        worker.error.connect(lambda message: self._on_check_error(message, manual))
        worker.finished.connect(self._check_finished)
        worker.start()

    def _check_finished(self):
        self._checking = False
        worker = self._check_worker
        self._check_worker = None
        if worker is not None:
            worker.deleteLater()

    def _on_no_update(self, manual):
        if manual and self.parent is not None:
            QMessageBox.information(
                self.parent,
                "RMCS Analyzer — No Update Available",
                f"RMCS Analyzer {APP_VERSION} is currently the latest available version.",
            )

    def _on_check_error(self, message, manual):
        if manual and self.parent is not None:
            QMessageBox.warning(
                self.parent,
                "RMCS Analyzer — Update Check Failed",
                message,
            )

    def _on_update_found(self, update: UpdateInfo, _manual):
        if self.parent is None:
            return

        box = QMessageBox(self.parent)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("RMCS Analyzer Update Available")
        box.setText(
            f"A new version of RMCS Analyzer is available.\n\n"
            f"Current version: {APP_VERSION}\n"
            f"New version: {update.version}"
        )
        if update.release_notes:
            notes = update.release_notes
            if len(notes) > 3500:
                notes = notes[:3500].rstrip() + "\n…"
            box.setInformativeText(f"What's new:\n\n{notes}")

        install_button = box.addButton("Install Now", QMessageBox.ButtonRole.AcceptRole)
        later_button = box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(install_button)
        box.exec()

        if box.clickedButton() is install_button:
            self._begin_download(update)
        elif box.clickedButton() is later_button:
            return

    def _begin_download(self, update: UpdateInfo):
        if self._installing:
            return
        self._installing = True

        self._progress_dialog = QProgressDialog(
            "Downloading RMCS Analyzer update…",
            "Cancel",
            0,
            100,
            self.parent,
        )
        self._progress_dialog.setWindowTitle("RMCS Analyzer Update")
        self._progress_dialog.setAutoClose(False)
        self._progress_dialog.setAutoReset(False)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.canceled.connect(self._cancel_download)
        self._progress_dialog.show()

        worker = UpdateDownloadWorker(update, self.parent)
        self._download_worker = worker
        worker.progress.connect(self._progress_changed)
        worker.completed.connect(lambda path: self._download_complete(update, path))
        worker.error.connect(self._download_error)
        worker.finished.connect(self._download_finished)
        worker.start()

    def _progress_changed(self, value):
        if self._progress_dialog is not None:
            self._progress_dialog.setValue(value)

    def _cancel_download(self):
        if self._download_worker is not None:
            self._download_worker.cancel()

    def _download_error(self, message):
        self._installing = False
        self._close_progress()
        if self.parent is not None:
            QMessageBox.warning(
                self.parent,
                "RMCS Analyzer Update Failed",
                message,
            )

    def _download_finished(self):
        worker = self._download_worker
        self._download_worker = None
        if worker is not None:
            worker.deleteLater()

    def _download_complete(self, update, path):
        if self._progress_dialog is not None:
            self._progress_dialog.setLabelText("Installing RMCS Analyzer update…")
            self._progress_dialog.setCancelButton(None)
            self._progress_dialog.setValue(100)
        try:
            if sys.platform.startswith("win"):
                _install_windows(Path(path))
            elif sys.platform == "darwin":
                _install_macos(Path(path))
            else:
                raise RuntimeError("Automatic updates are not supported on this operating system.")
        except Exception as exc:
            self._installing = False
            self._close_progress()
            if self.parent is not None:
                QMessageBox.critical(
                    self.parent,
                    "RMCS Analyzer Update Failed",
                    f"The update was downloaded, but it could not be installed.\n\n{exc}",
                )
            return

        # The platform installer/helper takes over from here.
        QApplication.instance().quit()

    def _close_progress(self):
        if self._progress_dialog is not None:
            self._progress_dialog.close()
            self._progress_dialog.deleteLater()
            self._progress_dialog = None


def _normalize_version(value):
    match = re.search(r"(?:^|[^0-9])(\d+)\.(\d+)\.(\d+)(?:[^0-9]|$)", str(value))
    if not match:
        return None
    return ".".join(match.groups())


def _version_tuple(value):
    return tuple(int(part) for part in value.split("."))


def _is_newer(latest, current):
    return _version_tuple(latest) > _version_tuple(current)


def _select_platform_asset(assets, version):
    system = sys.platform
    candidates = []
    for asset in assets or []:
        name = str(asset.get("name") or "")
        lower = name.lower()
        if system.startswith("win"):
            if lower.endswith(".exe") and "setup" in lower and "rmcs_analyzer" in lower:
                candidates.append(asset)
        elif system == "darwin":
            if "rmcs" in lower and (lower.endswith(".zip") or lower.endswith(".dmg")) and ("mac" in lower or "osx" in lower):
                candidates.append(asset)

    exact_windows = f"rmcs_analyzer_v{version}_setup.exe".lower()
    for asset in candidates:
        if str(asset.get("name") or "").lower() == exact_windows:
            return asset

    if system == "darwin":
        # Prefer ZIP because it can be installed without relying on Finder.
        candidates.sort(key=lambda item: 0 if str(item.get("name") or "").lower().endswith(".zip") else 1)
    return candidates[0] if candidates else None


def _install_windows(installer_path: Path):
    if not installer_path.exists():
        raise FileNotFoundError(installer_path)
    subprocess.Popen(
        [
            str(installer_path),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
        ],
        cwd=str(installer_path.parent),
        start_new_session=True,
        close_fds=True,
    )


def _install_macos(package_path: Path):
    if not package_path.exists():
        raise FileNotFoundError(package_path)

    app_bundle = _macos_app_bundle()
    if app_bundle is None:
        raise RuntimeError("The installed RMCS Analyzer application bundle could not be located.")

    temp_dir = package_path.parent
    helper = temp_dir / "install_rmcs_update.sh"
    pid = os.getpid()
    package_q = shlex.quote(str(package_path))
    target_q = shlex.quote(str(app_bundle))
    helper.write_text(
        "#!/bin/bash\n"
        "set -u\n"
        f"PACKAGE={package_q}\n"
        f"TARGET={target_q}\n"
        f"PARENT_PID={pid}\n"
        "while kill -0 \"$PARENT_PID\" 2>/dev/null; do sleep 1; done\n"
        "WORK=\"$(mktemp -d /tmp/rmcs_update_extract.XXXXXX)\"\n"
        "cleanup() { rm -rf \"$WORK\"; }\n"
        "trap cleanup EXIT\n"
        "unzip -q \"$PACKAGE\" -d \"$WORK\"\n"
        "NEW_APP=\"$(find \"$WORK\" -maxdepth 3 -type d -name 'RMCS Analyzer.app' -print -quit)\"\n"
        "if [ -z \"$NEW_APP\" ]; then exit 20; fi\n"
        "STAGED=\"$WORK/RMCS Analyzer.app\"\n"
        "/usr/bin/ditto \"$NEW_APP\" \"$STAGED\"\n"
        "if [ -w \"$(dirname \"$TARGET\")\" ]; then\n"
        "  rm -rf \"$TARGET\"\n"
        "  /usr/bin/ditto \"$STAGED\" \"$TARGET\" || exit 21\n"
        "else\n"
        "  PRIVILEGED=\"$WORK/install_privileged.sh\"\n"
        "  cat > \"$PRIVILEGED\" <<EOF\n"
        "#!/bin/bash\n"
        "set -e\n"
        "rm -rf $(printf '%q' \"$TARGET\")\n"
        "/usr/bin/ditto $(printf '%q' \"$STAGED\") $(printf '%q' \"$TARGET\")\n"
        "EOF\n"
        "  chmod 700 \"$PRIVILEGED\"\n"
        "  /usr/bin/osascript -e 'do shell script \"/bin/bash \" & quoted form of \"'\"$PRIVILEGED\"'\" with administrator privileges' || exit 22\n"
        "fi\n"
        "/usr/bin/open \"$TARGET\"\n",
        encoding="utf-8",
    )
    helper.chmod(0o700)
    subprocess.Popen(
        ["/bin/bash", str(helper)],
        cwd=str(temp_dir),
        start_new_session=True,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _macos_app_bundle():
    executable = Path(sys.executable).resolve()
    for parent in (executable, *executable.parents):
        if parent.suffix.lower() == ".app" and parent.name == "RMCS Analyzer.app":
            return parent
    return None


def _remove_tree(path: Path):
    try:
        import shutil
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass
