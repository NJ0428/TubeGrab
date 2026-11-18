"""
Minimal i18n module for TubeGrab.

Usage::

    from app.utils.i18n import tr, set_language, get_language

    set_language("ko")
    print(tr("Settings"))   # → "설정"
    print(tr("Settings"))   # → "Settings"  (falls back to key)
"""

from __future__ import annotations

_LANG: str = "en"

# ---------------------------------------------------------------------------
# Korean translations  (key = English source string)
# ---------------------------------------------------------------------------
_KO: dict[str, str] = {
    # ── Top bar ────────────────────────────────────────────────────────────
    "🕐 History": "🕐 기록",
    "⊞ Batch": "⊞ 일괄",
    "☀ Light": "☀ 라이트",
    "☾ Dark": "☾ 다크",
    "ℹ About": "ℹ 정보",
    "⚙ Settings": "⚙ 설정",

    # ── Main window sections / labels ──────────────────────────────────────
    "VIDEO URL": "비디오 URL",
    "DOWNLOAD OPTIONS": "다운로드 옵션",
    "DOWNLOADS": "다운로드 목록",
    "Resolution:": "해상도:",
    "Format:": "형식:",
    "Subtitles:": "자막:",
    "Save to:": "저장 위치:",
    "None": "없음",
    "Configure…": "설정…",
    "Browse…": "찾아보기…",
    "⬇  Download": "⬇  다운로드",
    "Clear Completed": "완료 항목 지우기",
    "No downloads yet. Paste a URL above to get started.":
        "다운로드가 없습니다. 위에 URL을 붙여넣어 시작하세요.",
    "View download history": "다운로드 기록 보기",
    "Add multiple URLs at once": "여러 URL을 한 번에 추가",
    "Toggle light / dark theme": "라이트/다크 테마 전환",
    "About TubeGrab": "TubeGrab 정보",
    "Open settings": "설정 열기",
    "Choose download folder": "다운로드 폴더 선택",
    "Start downloading the video": "영상 다운로드 시작",
    "Remove completed, failed, and cancelled items": "완료·실패·취소 항목 제거",
    "Select download folder…": "다운로드 폴더 선택…",

    # ── Status bar messages ────────────────────────────────────────────────
    "Ready": "준비",
    "Warning: ffmpeg not found — audio extraction may fail.":
        "경고: ffmpeg를 찾을 수 없습니다 — 오디오 추출이 실패할 수 있습니다.",
    "Please enter a URL first.": "먼저 URL을 입력해주세요.",
    "Download cancelled.": "다운로드 취소됨.",
    "Cancelling download…": "다운로드 취소 중…",
    "Could not retry: task not found.": "재시도 불가: 작업을 찾을 수 없습니다.",
    "Retrying download…": "다운로드 재시도 중…",
    "Downloads paused.": "다운로드 일시 정지됨.",
    "Downloads resumed.": "다운로드 재개됨.",
    "URL auto-filled from clipboard.": "클립보드에서 URL을 자동 입력했습니다.",
    "URL loaded from clipboard.": "클립보드에서 URL을 불러왔습니다.",
    "Select Download Folder": "다운로드 폴더 선택",
    "Fetching playlist info…": "재생목록 정보 가져오는 중…",
    "TubeGrab is running in the background.": "TubeGrab이 백그라운드에서 실행 중입니다.",

    # Templates — caller does .format(*args) on the returned string
    "Fetching info for: {} …": "정보 가져오는 중: {} …",
    "Fetching playlist: {}/{} videos…": "재생목록 가져오는 중: {}/{} 영상…",
    "Ready — {}": "준비 — {}",
    "Error: {}": "오류: {}",
    "Playlist error: {}": "재생목록 오류: {}",
    "Download complete: {}": "다운로드 완료: {}",
    "Download failed: {}": "다운로드 실패: {}",
    "Downloading {} file(s) — {} queued": "{}개 파일 다운로드 중 — {}개 대기",
    "Queued {} videos for download": "{}개 영상을 대기열에 추가했습니다",
    "Re-download queued: {}": "재다운로드 대기열에 추가됨: {}",
    "Batch: {} URL added to queue.": "일괄: {}개 URL이 대기열에 추가됨.",
    "Batch: {} URLs added to queue.": "일괄: {}개 URL이 대기열에 추가됨.",
    "yt-dlp update available: {} → {} (updating…)":
        "yt-dlp 업데이트 가능: {} → {} (업데이트 중…)",

    # ── URL input ──────────────────────────────────────────────────────────
    "Enter YouTube URL…": "YouTube URL 입력…",
    "Paste": "붙여넣기",
    "Fetch Info": "정보 가져오기",
    "✔ Valid URL": "✔ 유효한 URL",
    "↳ Playlist detected": "↳ 재생목록 감지됨",
    "✘ Invalid URL": "✘ 잘못된 URL",
    "Paste URL from clipboard": "클립보드에서 URL 붙여넣기",
    "Fetch video information": "영상 정보 가져오기",

    # ── Clipboard banner ───────────────────────────────────────────────────
    "YouTube URL detected in clipboard:": "클립보드에서 YouTube URL 감지됨:",
    "Use This URL": "이 URL 사용",
    "Dismiss": "닫기",

    # ── Download item ──────────────────────────────────────────────────────
    "Cancel": "취소",
    "Open File": "파일 열기",
    "Retry": "재시도",
    "ETA: {}": "예상: {}",
    # Task status labels
    "Pending": "대기 중",
    "Downloading": "다운로드 중",
    "Completed": "완료",
    "Failed": "실패",
    "Cancelled": "취소됨",

    # ── Progress card ──────────────────────────────────────────────────────
    "Total: {}": "전체: {}",
    "Active: {}": "활성: {}",
    "Completed: {}": "완료: {}",

    # ── Settings dialog ────────────────────────────────────────────────────
    "Settings": "설정",
    "Download path:": "다운로드 경로:",
    "Default resolution:": "기본 해상도:",
    "Default format:": "기본 형식:",
    "Max concurrent downloads:": "최대 동시 다운로드:",
    "Theme:": "테마:",
    "Dark": "다크",
    "Light": "라이트",
    "Language:": "언어:",
    "Notify when download completes": "다운로드 완료 시 알림",
    "Auto-detect YouTube URLs from clipboard on focus":
        "앱 포커스 시 클립보드에서 YouTube URL 자동 감지",
    "Auto-fill silently (no confirmation banner)": "자동 입력 (확인 배너 없음)",
    "Minimize to tray on close (instead of quitting)":
        "닫기 시 트레이로 최소화 (종료 대신)",
    "Show tray notification on download complete": "다운로드 완료 시 트레이 알림 표시",
    "── Filename Template ──": "── 파일명 템플릿 ──",
    "Template:": "템플릿:",
    "Insert:": "삽입:",
    "── yt-dlp ──": "── yt-dlp ──",
    "Installed version:": "설치된 버전:",
    "Automatically update yt-dlp on startup": "시작 시 yt-dlp 자동 업데이트",
    "Update Now": "지금 업데이트",
    "Updating…": "업데이트 중…",
    "Failed: {}": "실패: {}",
    "Error (settings): {}": "오류: {}",
    "Preview: {}": "미리보기: {}",

    # ── About dialog ───────────────────────────────────────────────────────
    "About TubeGrab (title)": "TubeGrab 정보",
    "Version 1.0.0": "버전 1.0.0",
    "A fast, modern YouTube downloader": "빠르고 현대적인 YouTube 다운로더",
    "Close": "닫기",

    # ── History dialog ─────────────────────────────────────────────────────
    "Download History": "다운로드 기록",
    "Search by title or URL…": "제목 또는 URL로 검색…",
    "Date:": "날짜:",
    "Search": "검색",
    "Filter": "필터",
    "Clear Filter": "필터 지우기",
    "Title": "제목",
    "Channel": "채널",
    "Resolution": "해상도",
    "Format": "형식",
    "Size": "크기",
    "Date": "날짜",
    "Actions": "작업",
    "{} entry": "{}개 항목",
    "{} entries": "{}개 항목",
    "0 entries": "0개 항목",
    "Clear All History": "모든 기록 지우기",
    "↺ Re-download": "↺ 재다운로드",
    "✕ Remove": "✕ 삭제",
    "Are you sure you want to delete all download history?\n\nThis cannot be undone.":
        "모든 다운로드 기록을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",

    # ── Batch dialog ───────────────────────────────────────────────────────
    "Batch URL Input": "일괄 URL 입력",
    "BATCH URL INPUT": "일괄 URL 입력",
    "Paste one URL per line. Invalid URLs will be automatically filtered out.":
        "URL을 한 줄에 하나씩 붙여넣으세요. 잘못된 URL은 자동으로 필터링됩니다.",
    "Analyze URLs": "URL 분석",
    "Status": "상태",
    "Type": "유형",
    "Playlist": "재생목록",
    "Video": "영상",
    "✔ {} valid": "✔ {}개 유효",
    "✘ {} invalid": "✘ {}개 잘못됨",
    "⬛ {} duplicate": "⬛ {}개 중복",
    "⬛ {} duplicates": "⬛ {}개 중복",
    "{} URL will be queued": "{}개 URL이 대기열에 추가됩니다",
    "{} URLs will be queued": "{}개 URL이 대기열에 추가됩니다",
    "0 URLs will be queued": "0개 URL이 대기열에 추가됩니다",
    "Add to Queue ({})": "대기열에 추가 ({})",

    # ── Playlist dialog ────────────────────────────────────────────────────
    "Playlist Download": "재생목록 다운로드",
    "{} videos": "{}개 영상",
    "Select All": "전체 선택",
    "Deselect All": "전체 해제",
    "{} selected": "{}개 선택됨",
    "Download Selected ({})": "선택 다운로드 ({})",
    "Duration": "길이",

    # ── Subtitle dialog ────────────────────────────────────────────────────
    "Subtitle Options": "자막 옵션",
    "No subtitle information available. Languages will be requested as-is.":
        "자막 정보를 사용할 수 없습니다. 언어를 그대로 요청합니다.",
    "Select Languages:": "언어 선택:",
    "Hold Ctrl to select multiple languages": "Ctrl 키를 눌러 여러 언어를 선택하세요",
    "Subtitle Format:": "자막 형식:",
    "Include auto-generated subtitles": "자동 생성 자막 포함",
    "Download subtitles only (no video)": "자막만 다운로드 (영상 제외)",
    " (subtitle only)": " (자막만)",

    # ── FFmpeg dialog ──────────────────────────────────────────────────────
    "FFmpeg Not Found": "FFmpeg를 찾을 수 없음",
    "FFmpeg was not found on this system.\n\nAudio extraction (MP3/M4A) and some "
    "video merging features will not work.\n\nPlease install FFmpeg and ensure it "
    "is in your PATH.":
        "이 시스템에서 FFmpeg를 찾을 수 없습니다.\n\n오디오 추출(MP3/M4A) 및 일부 영상 "
        "병합 기능이 작동하지 않습니다.\n\nFFmpeg를 설치하고 PATH에 등록해주세요.",
    "Download FFmpeg": "FFmpeg 다운로드",
    "Continue Anyway": "그냥 계속",

    # ── Tray ───────────────────────────────────────────────────────────────
    "Show Window": "창 표시",
    "Pause Downloads": "다운로드 일시 정지",
    "Resume Downloads": "다운로드 재개",
    "Exit": "종료",
    "TubeGrab — {} download(s) active": "TubeGrab — {}개 다운로드 중",
    "Download failed: {}\n{}": "다운로드 실패: {}\n{}",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def set_language(lang: str) -> None:
    """Set the active UI language.  Accepted values: ``"en"``, ``"ko"``."""
    global _LANG
    _LANG = lang if lang in ("en", "ko") else "en"


def get_language() -> str:
    """Return the currently active language code."""
    return _LANG


def tr(key: str) -> str:
    """Return the translation of *key* for the active language.

    Falls back to *key* itself when no translation is found, so callers
    can use the English text directly as the key.
    """
    if _LANG == "ko":
        return _KO.get(key, key)
    return key
