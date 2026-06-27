"""
DuolingoCLI — Main CLI entry point.

Commands:
    duo auth login       — Save your JWT token
    duo auth logout      — Remove saved token
    duo auth status      — Check auth status

    duo profile          — View your profile
    duo streak           — View streak info
    duo xp               — View XP summary
    duo courses          — List your courses
    duo health           — View hearts/health
    duo leaderboard      — View weekly leaderboard
    duo vocab            — View learned vocabulary

    duo practice         — Start a practice session
"""

from __future__ import annotations

import sys

import click
from rich.console import Console

from . import __version__
from .api import DuolingoClient, DuolingoAPIError
from .config import (
    get_token, save_token, delete_token,
    get_user_id, save_user_id,
    get_username, save_username,
)
from .ui import (
    console, print_banner, print_profile, print_streak,
    print_xp_info, print_leaderboard,
    print_courses, print_health,
    print_success, print_error, print_warning, print_info,
    DUO_GREEN, DUO_RED,
)

# ────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────


def _get_client() -> DuolingoClient:
    """Get an authenticated API client, or exit with error."""
    token = get_token()
    if not token:
        print_error(
            "Not authenticated! Run [bold]duo auth login[/bold] first.\n"
            "  You need a JWT token from your browser cookies.\n"
            "  See [bold]duo auth login --help[/bold] for instructions."
        )
        sys.exit(1)
    return DuolingoClient(token)


def _handle_api_error(e: DuolingoAPIError) -> None:
    """Handle API errors gracefully."""
    if e.status_code == 401:
        print_error(
            "Your JWT token has expired. Please update it:\n"
            "  [bold]duo auth login[/bold]"
        )
    elif e.status_code == 403:
        print_error("Access forbidden. Your account may be restricted.")
    elif e.status_code == 429:
        print_warning("Rate limited! Wait a moment and try again.")
    else:
        print_error(f"API error: {e.message}")
    sys.exit(1)


# ────────────────────────────────────────────
# CLI Group
# ────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="DuolingoCLI")
@click.pass_context
def cli(ctx):
    """🦉 DuolingoCLI — Practice Duolingo from your terminal.

    An unofficial CLI tool that uses Duolingo's API to let you
    view your profile, track progress, and practice lessons
    right from your terminal.

    Get started:

        duo auth login     Save your JWT token

        duo profile        View your profile

        duo practice       Start practicing!
    """
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print()
        console.print(ctx.get_help())


# ────────────────────────────────────────────
# Auth commands
# ────────────────────────────────────────────


@cli.group()
def auth():
    """🔑 Manage authentication (JWT token)."""
    pass


@auth.command("login")
@click.option(
    "--token", "-t",
    prompt=True,
    hide_input=True,
    help="Your Duolingo JWT token from browser cookies.",
)
def auth_login(token: str):
    """Save your JWT token for authentication.

    To get your JWT token:

    \b
    1. Log in to duolingo.com in your browser
    2. Open Developer Tools (F12)
    3. Go to Console tab
    4. Paste this command:
       document.cookie.split(';').find(c => c.includes('jwt_token'))?.split('=')[1]
    5. Copy the token value
    """
    token = token.strip()
    if not token:
        print_error("Token cannot be empty.")
        return

    # Validate token by trying to fetch user info
    console.print()
    print_info("Validating token...")

    try:
        client = DuolingoClient(token)
        user_info = client.get_user_info()
        username = user_info.get("username", "?")
        user_id = str(user_info.get("id", ""))

        save_token(token)
        save_username(username)
        save_user_id(user_id)

        console.print()
        print_success(f"Authenticated as [bold]{username}[/bold]! 🦉")
        print_info(f"User ID: {user_id}")
        print_info("Token saved securely.")

    except DuolingoAPIError as e:
        print_error(f"Invalid token: {e.message}")
    except Exception as e:
        print_error(f"Failed to validate token: {e}")


@auth.command("logout")
def auth_logout():
    """Remove saved JWT token."""
    delete_token()
    print_success("Token removed. You are logged out.")


@auth.command("status")
def auth_status():
    """Check authentication status."""
    token = get_token()
    username = get_username()

    if token:
        print_success(f"Authenticated as [bold]{username or '?'}[/bold]")
        print_info(f"Token: {token[:20]}...{token[-10:]}")
    else:
        print_warning("Not authenticated. Run [bold]duo auth login[/bold].")


# ────────────────────────────────────────────
# Profile commands
# ────────────────────────────────────────────


@cli.command()
def profile():
    """👤 View your Duolingo profile."""
    try:
        with _get_client() as client:
            console.print()
            user_data = client.get_user_info()
            print_profile(user_data)
    except DuolingoAPIError as e:
        _handle_api_error(e)


@cli.command()
def streak():
    """🔥 View your streak information."""
    try:
        with _get_client() as client:
            console.print()
            streak_data = client.get_streak()
            print_streak(streak_data)
    except DuolingoAPIError as e:
        _handle_api_error(e)


@cli.command()
def xp():
    """⚡ View your XP summary."""
    try:
        with _get_client() as client:
            console.print()
            xp_data = client.get_xp_info()
            print_xp_info(xp_data)
    except DuolingoAPIError as e:
        _handle_api_error(e)


@cli.command()
def courses():
    """📚 List your courses."""
    try:
        with _get_client() as client:
            console.print()
            courses_data = client.get_courses()
            print_courses(courses_data)
    except DuolingoAPIError as e:
        _handle_api_error(e)


@cli.command()
def health():
    """❤️ View your health/hearts."""
    try:
        with _get_client() as client:
            console.print()
            health_data = client.get_health()
            print_health(health_data)
    except DuolingoAPIError as e:
        _handle_api_error(e)


@cli.command()
def leaderboard():
    """🏆 View your weekly leaderboard."""
    try:
        with _get_client() as client:
            console.print()
            username = client.get_username()
            rankings = client.get_leaderboard()
            print_leaderboard(rankings, current_username=username)
    except DuolingoAPIError as e:
        _handle_api_error(e)



@cli.command()
def shop():
    """🛒 View the Duolingo store."""
    try:
        with _get_client() as client:
            console.print()
            shop_data = client.get_shop_items()
            
            # Fetch user info to get gem balance
            user_info = client.get_user_info()
            gems = user_info.get("gemsConfig", {}).get("gems")
            if gems is None:
                gems = user_info.get("gems", 0)
                
            from .ui import print_shop
            print_shop(shop_data, user_gems=gems)
            
            print_info("Note: Purchasing items is currently not supported via CLI.")
    except DuolingoAPIError as e:
        _handle_api_error(e)


@cli.command()
def stats():
    """📊 View your advanced statistics dashboard."""
    try:
        with _get_client() as client:
            console.print()
            user_info = client.get_user_info()
            
            from .ui import print_stats
            print_stats(user_info)
            console.print()
    except DuolingoAPIError as e:
        _handle_api_error(e)


# ────────────────────────────────────────────
# Path / Lessons
# ────────────────────────────────────────────

@cli.command()
@click.option("--audio/--no-audio", default=False, help="Play audio for challenges (requires playsound package).")
def path(audio: bool):
    """🗺️ Continue your learning path (next lesson)."""
    try:
        with _get_client() as client:
            console.print()
            print_info("Finding next lesson in your path...")
            
            node = client.get_next_lesson()
            if not node:
                print_error("Could not find any active lessons in your path. Have you finished the course?")
                return
            
            title = node.get("debugName", "Lesson")
            skill_id = node.get("skillId")
            
            if not skill_id:
                print_warning(f"Found node '{title}' but it has no skill ID. Trying generic practice instead.")
                session = client.start_practice_session()
            else:
                section_idx = node.get("sectionIndex", "?")
                unit_idx = node.get("unitIndex", "?")
                print_info(f"Starting: Section {section_idx}, Unit {unit_idx} — {title}")
                console.print()
                session = None
                level_session_index = node.get("levelSessionIndex", 0)
                # Try levelSessionIndex and decrement once if server rejects it (500)
                for attempt_lsi in [level_session_index, level_session_index - 1]:
                    if attempt_lsi < 0:
                        break
                    try:
                        session = client.start_practice_session(
                            session_type="LESSON",
                            skill_id=skill_id,
                            level_id=node.get("levelId"),
                            level_index=node.get("levelIndex"),
                            level_session_index=attempt_lsi,
                            tree_id=node.get("treeId"),
                            is_final_level=node.get("isFinalLevel", False),
                        )
                        break  # success
                    except DuolingoAPIError:
                        continue

                if session is None:
                    print_warning("Duolingo's server rejected the path lesson request.")
                    print_info("Falling back to a Global Practice session instead.")
                    console.print()
                    session = client.start_practice_session(session_type="GLOBAL_PRACTICE")

            from .practice import run_practice_session
            results = run_practice_session(session, client, play_audio=audio)

            # Try to complete the session on the server
            if len(results.get("answers", [])) > 0:
                try:
                    client.complete_session(
                        session, 
                        results.get("answers", []), 
                        path_level_specifics=node.get("pathLevelSpecifics"),
                        hearts_left=results.get("hearts_left")
                    )
                    
                    if results.get("hearts_left") == 0:
                        print_warning("Lesson submitted as failed (out of hearts).")
                    else:
                        print_success("Lesson submitted to Duolingo! Progress saved. 🎉")
                except Exception:
                    print_warning(
                        "Could not submit lesson to server. "
                        "Your progress may not be saved."
                    )

    except DuolingoAPIError as e:
        _handle_api_error(e)
    except KeyboardInterrupt:
        console.print()
        print_warning("Lesson cancelled.")
        sys.exit(0)


# ────────────────────────────────────────────
# Practice command
# ────────────────────────────────────────────


@cli.command()
@click.option(
    "--type", "-t", "session_type",
    type=click.Choice(["practice", "listen", "speak"], case_sensitive=False),
    default="practice",
    help="Type of session.",
)
@click.option("--audio/--no-audio", default=False, help="Play audio for challenges (requires playsound package).")
def practice(session_type: str, audio: bool):
    """🦉 Start an interactive practice session.

    Practice your current language with various challenge types
    directly in your terminal. Translation, multiple choice,
    matching, fill-in-the-blank, and more!

    \b
    Session types:
      practice  — General practice (default)
      listen    — Listening-focused practice
      speak     — Speaking-focused practice
    """
    type_map = {
        "practice": "GLOBAL_PRACTICE",
        "listen": "LISTENING_PRACTICE",
        "speak": "SPEAKING_PRACTICE",
    }

    try:
        with _get_client() as client:
            console.print()
            print_info("Starting practice session...")
            console.print()

            # Get current course info
            course = client.get_current_course()
            if course:
                from .ui import get_flag
                lang = course.get("learningLanguage", "?")
                title = course.get("title", lang)
                flag = get_flag(lang)
                print_info(f"Course: {flag} {title}")

            api_type = type_map.get(session_type, "GLOBAL_PRACTICE")
            session = client.start_practice_session(session_type=api_type)

            from .practice import run_practice_session
            results = run_practice_session(session, client, play_audio=audio)

            # Try to complete the session on the server
            if len(results.get("answers", [])) > 0:
                try:
                    client.complete_session(
                        session, 
                        results.get("answers", []),
                        hearts_left=results.get("hearts_left")
                    )
                    if results.get("hearts_left") == 0:
                        print_warning("Session submitted as failed (out of hearts).")
                    else:
                        print_success("Session submitted to Duolingo! XP earned. 🎉")
                        # Show updated hearts if applicable
                        try:
                            h = client.get_health()
                            if h.get("useHealth") and not h.get("unlimitedHeartsAvailable"):
                                print_success(f"Current Hearts: ❤️ {h.get('hearts', 0)}")
                        except Exception:
                            pass
                except Exception:
                    print_warning(
                        "Could not submit session to server. "
                        "Your progress may not be saved."
                    )

    except DuolingoAPIError as e:
        _handle_api_error(e)
    except KeyboardInterrupt:
        console.print()
        print_warning("Session cancelled.")
        sys.exit(0)


# ────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────


if __name__ == "__main__":
    cli()
