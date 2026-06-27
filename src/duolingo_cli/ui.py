"""
Rich UI rendering utilities for the CLI.

Provides beautiful terminal output for Duolingo data:
profiles, streaks, leaderboards, vocabulary tables, etc.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.rule import Rule
from rich.align import Align
from rich import box

console = Console()

# ── Duolingo brand colors ──
DUO_GREEN = "#58CC02"
DUO_BLUE = "#1CB0F6"
DUO_RED = "#FF4B4B"
DUO_ORANGE = "#FF9600"
DUO_PURPLE = "#CE82FF"
DUO_GOLD = "#FFC800"
DUO_GRAY = "#AFAFAF"
DUO_DARK = "#1B1B1B"

# ── Language flag emojis ──
LANG_FLAGS: dict[str, str] = {
    "en": "🇬🇧", "es": "🇪🇸", "fr": "🇫🇷", "de": "🇩🇪", "it": "🇮🇹",
    "pt": "🇧🇷", "ja": "🇯🇵", "ko": "🇰🇷", "zh": "🇨🇳", "ru": "🇷🇺",
    "ar": "🇸🇦", "hi": "🇮🇳", "tr": "🇹🇷", "nl": "🇳🇱", "sv": "🇸🇪",
    "pl": "🇵🇱", "no": "🇳🇴", "da": "🇩🇰", "fi": "🇫🇮", "el": "🇬🇷",
    "he": "🇮🇱", "id": "🇮🇩", "ro": "🇷🇴", "cs": "🇨🇿", "uk": "🇺🇦",
    "vi": "🇻🇳", "th": "🇹🇭", "hu": "🇭🇺", "ga": "🇮🇪", "cy": "🏴",
    "sw": "🇰🇪", "eo": "🟢", "la": "🏛️", "hv": "🐉", "kl": "🖖",
    "gn": "🇵🇾", "yi": "🕎", "zu": "🇿🇦", "ca": "🏴", "ht": "🇭🇹",
}


def get_flag(lang_code: str) -> str:
    """Get flag emoji for a language code."""
    return LANG_FLAGS.get(lang_code, "🌍")


def print_banner() -> None:
    """Print the DuolingoCLI banner."""
    banner_text = Text()
    banner_text.append("  🦉  ", style="bold")
    banner_text.append("DuolingoCLI", style=f"bold {DUO_GREEN}")
    banner_text.append("  —  ", style="dim")
    banner_text.append("Learn from your terminal", style=f"italic {DUO_BLUE}")

    console.print(Panel(
        Align.center(banner_text),
        border_style=DUO_GREEN,
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    ))


def print_profile(user_data: dict) -> None:
    """Render a beautiful user profile panel."""
    name = user_data.get("name") or user_data.get("username", "Unknown")
    username = user_data.get("username", "")
    streak = user_data.get("streak", 0)
    total_xp = user_data.get("totalXp", 0)
    lingots = user_data.get("lingots", 0)
    has_plus = user_data.get("hasPlus", False)
    courses = user_data.get("courses", [])

    # Build profile
    lines = []

    # Name & badge
    name_text = Text()
    name_text.append(f"  {name}", style=f"bold {DUO_GREEN}")
    if has_plus:
        name_text.append("  ⭐ SUPER", style=f"bold {DUO_GOLD}")
    lines.append(name_text)

    lines.append(Text(f"  @{username}", style="dim"))
    lines.append(Text(""))

    # Stats row
    stats_table = Table(show_header=False, box=None, padding=(0, 3))
    stats_table.add_column(justify="center")
    stats_table.add_column(justify="center")
    stats_table.add_column(justify="center")

    stats_table.add_row(
        Text(f"🔥 {streak}", style=f"bold {DUO_ORANGE}"),
        Text(f"⚡ {total_xp:,}", style=f"bold {DUO_BLUE}"),
        Text(f"💎 {lingots:,}", style=f"bold {DUO_RED}"),
    )
    stats_table.add_row(
        Text("Streak", style="dim"),
        Text("Total XP", style="dim"),
        Text("Lingots", style="dim"),
    )
    lines.append(stats_table)

    # Courses
    if courses:
        lines.append(Text(""))
        lines.append(Text("  📚 Active Courses:", style=f"bold {DUO_PURPLE}"))
        for course in courses[:5]:
            lang = course.get("learningLanguage", "?")
            title = course.get("title", lang)
            xp = course.get("xp", 0)
            crowns = course.get("crowns", 0)
            flag = get_flag(lang)
            course_text = Text()
            course_text.append(f"     {flag} {title}", style="bold")
            course_text.append(f"  •  {xp:,} XP", style=f"{DUO_BLUE}")
            course_text.append(f"  •  👑 {crowns}", style=f"{DUO_GOLD}")
            lines.append(course_text)

    # Build renderable group
    from rich.console import Group
    panel_content = Group(*lines)

    console.print(Panel(
        panel_content,
        title=f"[{DUO_GREEN}]👤 Profile[/{DUO_GREEN}]",
        border_style=DUO_GREEN,
        padding=(1, 1),
    ))


def print_streak(streak_data: dict) -> None:
    """Render streak info with fire emoji visualization."""
    streak = streak_data.get("streak", 0)
    sd = streak_data.get("streak_data", {})

    current = sd.get("currentStreak", {})
    start_date = current.get("startDate", "?")
    length = current.get("length", streak)

    # Visual streak
    fire_bar = "🔥" * min(streak, 30)
    if streak > 30:
        fire_bar += f" +{streak - 30}"

    lines = []
    lines.append(Text(f"  {fire_bar}", style=f"bold {DUO_ORANGE}"))
    lines.append(Text(""))
    lines.append(Text(f"  Current Streak: ", style="dim").append(
        f"{streak} days", style=f"bold {DUO_ORANGE}"
    ))
    if start_date != "?":
        lines.append(Text(f"  Started: ", style="dim").append(
            start_date, style="bold"
        ))

    from rich.console import Group
    console.print(Panel(
        Group(*lines),
        title=f"[{DUO_ORANGE}]🔥 Streak[/{DUO_ORANGE}]",
        border_style=DUO_ORANGE,
        padding=(1, 1),
    ))


def print_xp_info(xp_data: dict) -> None:
    """Render XP information panel."""
    total = xp_data.get("total_xp", 0)
    weekly = xp_data.get("weekly_xp", 0)
    monthly = xp_data.get("monthly_xp", 0)
    goal = xp_data.get("xp_goal", 0)
    lingots = xp_data.get("lingots", 0)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", justify="right")
    table.add_column(style="bold")

    table.add_row("Total XP", Text(f"⚡ {total:,}", style=f"{DUO_BLUE}"))
    table.add_row("Weekly XP", Text(f"📊 {weekly:,}", style=f"{DUO_GREEN}"))
    table.add_row("Monthly XP", Text(f"📈 {monthly:,}", style=f"{DUO_PURPLE}"))
    table.add_row("Daily Goal", Text(f"🎯 {goal} XP", style=f"{DUO_ORANGE}"))
    table.add_row("Lingots", Text(f"💎 {lingots:,}", style=f"{DUO_RED}"))

    console.print(Panel(
        table,
        title=f"[{DUO_BLUE}]⚡ XP Summary[/{DUO_BLUE}]",
        border_style=DUO_BLUE,
        padding=(1, 1),
    ))


def print_leaderboard(rankings: list[dict], current_username: str = "") -> None:
    """Render a leaderboard table."""
    if not rankings:
        console.print(Panel(
            "[dim]No leaderboard data available.[/dim]",
            title=f"[{DUO_GOLD}]🏆 Leaderboard[/{DUO_GOLD}]",
            border_style=DUO_GOLD,
        ))
        return

    table = Table(
        box=box.ROUNDED,
        border_style=DUO_GOLD,
        show_lines=False,
        padding=(0, 1),
    )
    table.add_column("#", justify="center", style="bold", width=4)
    table.add_column("User", style="bold", min_width=20)
    table.add_column("XP", justify="right", style=f"bold {DUO_BLUE}", min_width=8)

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}

    for i, entry in enumerate(rankings[:20]):
        name = entry.get("displayName") or entry.get("username", "?")
        xp = entry.get("totalXp", 0)
        rank = medals.get(i, f" {i + 1}")

        style = ""
        if name == current_username:
            style = f"bold {DUO_GREEN}"
            name = f"→ {name} (you)"

        table.add_row(str(rank), Text(name, style=style), f"{xp:,}")

    console.print(Panel(
        table,
        title=f"[{DUO_GOLD}]🏆 Weekly Leaderboard[/{DUO_GOLD}]",
        border_style=DUO_GOLD,
        padding=(1, 1),
    ))



def print_stats(user_data: dict) -> None:
    """Render a comprehensive stats dashboard."""
    import datetime
    
    # Extract data
    total_xp = user_data.get("totalXp", 0)
    streak = user_data.get("streak", 0)
    longest_streak = user_data.get("streakData", {}).get("longestStreak", {}).get("length", streak)
    gems = user_data.get("gemsConfig", {}).get("gems")
    if gems is None:
        gems = user_data.get("gems", 0)
    lingots = user_data.get("lingots", 0)
    
    creation_ts = user_data.get("creationDate", 0)
    creation_str = "?"
    if creation_ts:
        creation_str = datetime.datetime.fromtimestamp(creation_ts).strftime("%B %Y")
    
    # Calculate totals from courses
    courses = user_data.get("courses", [])
    active_courses = len(courses)
    
    # Create the layout
    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style=DUO_BLUE,
        show_header=False,
        padding=(0, 2)
    )
    table.add_column(style="dim", justify="right")
    table.add_column(style="bold")
    
    # Add rows
    table.add_row("Total XP", Text(f"⚡ {total_xp:,}", style=f"{DUO_BLUE}"))
    table.add_row("Current Streak", Text(f"🔥 {streak} days", style=f"{DUO_ORANGE}"))
    table.add_row("Longest Streak", Text(f"🏆 {longest_streak} days", style=f"{DUO_GOLD}"))
    table.add_row("Active Courses", Text(f"📚 {active_courses}", style=f"{DUO_PURPLE}"))
    table.add_row("Gems", Text(f"💎 {gems:,}", style=f"{DUO_RED}"))
    table.add_row("Member Since", Text(f"📅 {creation_str}", style=f"{DUO_GREEN}"))
    
    console.print(Panel(
        table,
        title=f"[{DUO_BLUE}]📊 Your Statistics[/{DUO_BLUE}]",
        border_style=DUO_BLUE,
        padding=(1, 2)
    ))

def print_shop(shop_data: dict, user_gems: int = 0) -> None:
    """Render the shop inventory."""
    items = shop_data.get("shopItems", [])
    if not items:
        console.print(Panel(
            "[dim]The shop is currently unavailable.[/dim]",
            title=f"[{DUO_PURPLE}]🛒 Store[/{DUO_PURPLE}]",
            border_style=DUO_PURPLE,
        ))
        return

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style=DUO_PURPLE,
        show_lines=False,
    )
    table.add_column("Item", style=f"bold {DUO_GREEN}", min_width=20)
    table.add_column("Description", style="dim", min_width=30)
    table.add_column("Price", justify="right", style=f"bold {DUO_BLUE}")

    for item in items:
        # We only care about gems items or streak freezes, not subscriptions
        if item.get("currencyType") == "XGM" or item.get("id") in ["streak_freeze", "heart_refill"]:
            name = item.get("localizedName") or item.get("name") or item.get("id").replace("_", " ").title()
            desc = item.get("localizedDescription", "No description.")
            price = item.get("price", 0)
            
            # Format price
            price_str = f"💎 {price}" if price > 0 else "Free"

            table.add_row(name, desc, price_str)

    console.print(Panel(
        table,
        title=f"[{DUO_PURPLE}]🛒 Shop (Balance: 💎 {user_gems:,})[/{DUO_PURPLE}]",
        border_style=DUO_PURPLE,
        padding=(1, 1),
    ))

def print_courses(courses: list[dict]) -> None:
    """Render courses list."""
    if not courses:
        console.print("[dim]No courses found.[/dim]")
        return

    table = Table(
        box=box.ROUNDED,
        border_style=DUO_GREEN,
    )
    table.add_column("", width=3)
    table.add_column("Course", style="bold", min_width=20)
    table.add_column("XP", justify="right", style=DUO_BLUE)
    table.add_column("Crowns", justify="center", style=DUO_GOLD)
    table.add_column("From", style="dim")

    for course in courses:
        lang = course.get("learningLanguage", "?")
        from_lang = course.get("fromLanguage", "?")
        title = course.get("title", lang)
        xp = course.get("xp", 0)
        crowns = course.get("crowns", 0)

        table.add_row(
            get_flag(lang),
            title,
            f"{xp:,}",
            f"👑 {crowns}",
            f"{get_flag(from_lang)} {from_lang.upper()}",
        )

    console.print(Panel(
        table,
        title=f"[{DUO_GREEN}]📚 Courses[/{DUO_GREEN}]",
        border_style=DUO_GREEN,
        padding=(1, 1),
    ))


def print_health(health_data: dict) -> None:
    """Render health/hearts info."""
    hearts = health_data.get("healthPoints", 5)
    max_hearts = health_data.get("maxHealthPoints", 5)
    unlimited = health_data.get("unlimitedHearts", False)

    if unlimited:
        hearts_vis = "❤️" * 5 + " ∞"
        status = "Unlimited (Super)"
    else:
        hearts_vis = "❤️" * hearts + "🖤" * (max_hearts - hearts)
        status = f"{hearts}/{max_hearts}"

    console.print(Panel(
        Text.from_markup(f"  {hearts_vis}\n  [dim]Hearts: {status}[/dim]"),
        title=f"[{DUO_RED}]❤️ Health[/{DUO_RED}]",
        border_style=DUO_RED,
        padding=(1, 1),
    ))


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"  [bold {DUO_GREEN}]✓[/bold {DUO_GREEN}] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"  [bold {DUO_RED}]✗[/bold {DUO_RED}] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"  [bold {DUO_ORANGE}]⚠[/bold {DUO_ORANGE}] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"  [bold {DUO_BLUE}]ℹ[/bold {DUO_BLUE}] {message}")
