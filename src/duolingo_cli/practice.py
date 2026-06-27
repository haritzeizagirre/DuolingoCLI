"""
Interactive practice session handler.

Renders Duolingo challenges in the terminal and handles
user input for answering questions.
"""

from __future__ import annotations

import random
import time
import unicodedata
import string
from typing import Optional

def _normalize_text(text: str) -> str:
    """Normalize text: lowercase, remove accents, and punctuation."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.translate(str.maketrans('', '', string.punctuation + '¿¡'))
    return " ".join(text.split())

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule
from rich import box

from .ui import (
    DUO_GREEN, DUO_BLUE, DUO_RED, DUO_ORANGE,
    DUO_PURPLE, DUO_GOLD, DUO_GRAY,
    console, print_success, print_error, print_info, get_flag,
)

def _play_audio_url(url: str):
    """Download and play an audio URL using playsound."""
    if not url:
        return
    import urllib.request
    import tempfile
    import os
    try:
        from playsound import playsound
    except ImportError:
        console.print("[dim yellow]  (Install 'playsound' package to hear audio)[/dim yellow]")
        return
        
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            path = f.name
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(path, 'wb') as f:
            f.write(response.read())
        playsound(path)
        os.remove(path)
    except Exception:
        # Silently fail if audio can't be played
        pass

# Challenge types that we can handle in CLI
SUPPORTED_TYPES = {
    "translate",
    "judge",
    "select",
    "name",
    "completeReverseTranslation",
    "assist",
    "form",
    "gapFill",
    "match",
    "definition",
    "tapComplete",
    "typeCloze",
    "selectTranscription",
    "selectPronunciation",
    "listenTap",
    "readComprehension",
    "characterSelect",
    "characterMatch",
    "dialogue",
    "freeResponse",
    "listen",
    "partialReverseTranslate",
    "reverseAssist",
    "tapCloze",
    "typeComplete",
    "writeComprehension",
}


def run_practice_session(
    session: dict,
    client: object,
    use_hearts: bool = True,
    play_audio: bool = False
) -> dict:
    """
    Run an interactive practice session in the terminal.

    Args:
        session: Session data from the API (contains challenges)
        client: DuolingoClient instance

    Returns:
        Results dict with score and answers
    """
    challenges = list(session.get("challenges", []))
    adaptive = session.get("adaptiveChallenges", [])
    if adaptive:
        challenges.extend(adaptive)

    if not challenges:
        print_error("No challenges found in this session.")
        return {"correct": 0, "total": 0, "xp": 0}

    # Initialize health tracking if enabled
    current_hearts = 5
    unlimited = False
    try:
        health_data = client.get_health()
        use_hearts = health_data.get("useHealth", False) and health_data.get("healthEnabled", False)
        unlimited = health_data.get("unlimitedHeartsAvailable", False)
        if use_hearts and not unlimited:
            current_hearts = health_data.get("hearts", 0)
    except Exception:
        pass

    total = len(challenges)
    correct = 0
    answers = []
    start_time = time.time()

    console.print()
    header_text = f"[bold {DUO_GREEN}]🦉 Practice Session[/bold {DUO_GREEN}] — {total} challenges"
    if use_hearts and not unlimited:
        header_text += f" (❤️ {current_hearts})"
    elif unlimited:
        header_text += " (❤️ ∞)"
    console.print(Rule(header_text, style=DUO_GREEN))
    console.print()

    if use_hearts and not unlimited and current_hearts <= 0:
        print_error("You have 0 hearts left! Practice to earn more before starting new lessons.")
        return {
            "correct": 0,
            "total": total,
            "elapsed_seconds": 0,
            "answers": [],
            "hearts_left": 0
        }

    for i, challenge in enumerate(challenges):
        challenge_type = challenge.get("type", "unknown")

        # Header
        progress_pct = ((i) / total) * 100
        progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
        
        status_text = f"  [{DUO_BLUE}]{progress_bar}[/{DUO_BLUE}]  [dim]{i + 1}/{total}[/dim]  [dim italic]{challenge_type}[/dim italic]"
        if use_hearts and not unlimited:
            status_text += f"  [red]❤️ {current_hearts}[/red]"
            
        console.print(status_text)
        console.print()

        result = _handle_challenge(challenge, i + 1, total, play_audio=play_audio)
        answers.append(result)

        if result.get("correct"):
            correct += 1
            print_success("Correct! " + _random_encouragement())
        else:
            correct_answer = result.get("expected", "?")
            print_error(f"Wrong! The answer was: [bold]{correct_answer}[/bold]")
            if use_hearts and not unlimited:
                current_hearts -= 1
                if current_hearts <= 0:
                    console.print()
                    print_error("You ran out of hearts! ❤️ 0")
                    break

        console.print()
        time.sleep(0.3)

    elapsed = time.time() - start_time

    # Summary
    _print_session_summary(correct, total, elapsed)

    return {
        "correct": correct,
        "total": total,
        "elapsed_seconds": elapsed,
        "answers": answers,
        "hearts_left": current_hearts if (use_hearts and not unlimited) else None,
    }


def _handle_challenge(challenge: dict, num: int, total: int, play_audio: bool = False) -> dict:
    """
    Route a challenge to the appropriate handler.

    Returns dict with 'correct' (bool), 'answer' (str), 'expected' (str).
    """
    ctype = challenge.get("type", "unknown")

    if play_audio:
        tts = challenge.get("tts") or challenge.get("slowTts")
        if tts:
            console.print(f"  🎵 [dim]Playing audio...[/dim]")
            _play_audio_url(tts)

    if ctype in ("translate",):
        return _challenge_translate(challenge)
    elif ctype in ("judge",):
        return _challenge_judge(challenge)
    elif ctype in ("select", "characterSelect", "selectTranscription", "selectPronunciation"):
        return _challenge_select(challenge)
    elif ctype in ("name",):
        return _challenge_name(challenge)
    elif ctype in ("assist", "reverseAssist"):
        return _challenge_assist(challenge)
    elif ctype in ("match", "characterMatch", "listenMatch", "extendedMatch", "extendedListenMatch"):
        return _challenge_match(challenge)
    elif ctype in ("listenTap",):
        return _challenge_word_bank(challenge)
    elif ctype in ("speak", "listenSpeak"):
        return _challenge_speak(challenge)
    elif ctype in ("gapFill", "tapCloze", "tapComplete", "typeCloze", "typeComplete", "completeReverseTranslation", "partialReverseTranslate", "listenComplete"):
        return _challenge_gap_fill(challenge)
    elif ctype in ("form",):
        return _challenge_form(challenge)
    elif ctype in ("definition",):
        return _challenge_definition(challenge)
    elif ctype in ("listen",):
        return _challenge_listen(challenge)
    elif ctype in ("listenIsolation",):
        return _challenge_listen_isolation(challenge)
    elif ctype in ("readComprehension", "writeComprehension"):
        return _challenge_comprehension(challenge)
    elif ctype in ("dialogue",):
        return _challenge_dialogue(challenge)
    elif ctype in ("freeResponse",):
        return _challenge_free_response(challenge)
    else:
        return _challenge_generic(challenge)


def _challenge_translate(challenge: dict) -> dict:
    """Handle translation challenges (with optional word bank tiles)."""
    prompt = challenge.get("prompt", "")
    source_lang = challenge.get("sourceLanguage", "?")
    target_lang = challenge.get("targetLanguage", "?")
    correct_solutions = challenge.get("correctSolutions", [])
    compact = challenge.get("compactTranslations", [])
    correct_answers = challenge.get("correctAnswers", [])
    choices = challenge.get("choices", [])  # word bank tiles if present

    # Get all possible correct answers
    valid_answers = set()
    if correct_solutions:
        valid_answers.update(_normalize_text(s) for s in correct_solutions)
    if compact:
        for group in compact:
            if isinstance(group, list):
                for item in group:
                    if isinstance(item, str):
                        valid_answers.add(_normalize_text(item))
            elif isinstance(group, str):
                valid_answers.add(_normalize_text(group))
    if correct_answers:
        valid_answers.update(_normalize_text(a) for a in correct_answers)

    expected = correct_solutions[0] if correct_solutions else (
        correct_answers[0] if correct_answers else "?"
    )

    console.print(Panel(
        f"  {get_flag(source_lang)} → {get_flag(target_lang)}\n\n"
        f"  [bold]{prompt}[/bold]",
        title=f"[{DUO_BLUE}]📝 Translate[/{DUO_BLUE}]",
        border_style=DUO_BLUE,
        padding=(1, 1),
    ))

    # If there are word bank tiles, show them
    if choices:
        console.print()
        console.print(f"  [dim]Word bank:[/dim]")
        
        import random
        # We store tuples of (shuffled_index, original_choice) so we can display them
        shuffled_choices = list(choices)
        random.shuffle(shuffled_choices)
        
        tiles = []
        for i, choice in enumerate(shuffled_choices):
            text = choice if isinstance(choice, str) else choice.get("text", str(choice))
            tiles.append(text)
            console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")
        console.print()
        console.print(f"  [dim]Type the numbers in order (e.g. '2 5 1') or type the full answer:[/dim]")
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your answer[/{DUO_GREEN}]")
        # Try to resolve number choices to words
        parts = answer.strip().split()
        resolved_parts = []
        all_numbers = all(p.isdigit() for p in parts)
        if all_numbers and parts:
            for p in parts:
                idx = int(p) - 1
                if 0 <= idx < len(tiles):
                    resolved_parts.append(tiles[idx])
            answer = " ".join(resolved_parts)
    else:
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your translation[/{DUO_GREEN}]")

    is_correct = _normalize_text(answer) in valid_answers
    return {"correct": is_correct, "answer": answer, "expected": expected}


def _challenge_word_bank(challenge: dict) -> dict:
    """Handle word-bank tap challenges (listenTap, etc.).
    
    Shows the sentence/prompt and a numbered list of word tiles.
    The user picks the correct tiles in order by number.
    """
    prompt = challenge.get("prompt", "")
    choices = challenge.get("choices", [])
    correct_tokens = challenge.get("correctTokens", [])
    correct_indices = challenge.get("correctIndices", [])
    solution_translation = challenge.get("solutionTranslation", "")

    # Build display: show audio note + sentence (since CLI has no audio)
    panel_text = ""
    if prompt:
        panel_text += f"  🎵 [dim](Listen and tap)[/dim]\n\n  [bold]{prompt}[/bold]"
    if solution_translation:
        panel_text += f"\n\n  [dim]Translation: {solution_translation}[/dim]"

    console.print(Panel(
        panel_text or "  Select the correct words in order",
        title=f"[{DUO_ORANGE}]🎵 Tap the Words[/{DUO_ORANGE}]",
        border_style=DUO_ORANGE,
        padding=(1, 1),
    ))

    # Show word tiles
    console.print()
    import random
    
    # Store tuples of (original_index, choice) to keep track after shuffling
    shuffled_choices = list(enumerate(choices))
    random.shuffle(shuffled_choices)
    
    tiles = []
    row_parts = []
    for display_idx, (orig_idx, choice) in enumerate(shuffled_choices):
        text = choice if isinstance(choice, str) else choice.get("text", str(choice))
        tiles.append(text)
        row_parts.append(f"[{DUO_BLUE}]{display_idx + 1}[/{DUO_BLUE}]:[bold]{text}[/bold]")

    # Print tiles in rows of 4
    for k in range(0, len(row_parts), 4):
        console.print("    " + "   ".join(row_parts[k:k+4]))

    console.print()
    console.print(f"  [dim]Enter the numbers of the correct tiles in order (e.g. '1 3 2'):[/dim]")
    answer = Prompt.ask(f"  [{DUO_GREEN}]Your selection[/{DUO_GREEN}]")

    # Parse the chosen indices
    try:
        chosen_display_indices = [int(x.strip()) - 1 for x in answer.split()]
        chosen_words = [tiles[i] for i in chosen_display_indices if 0 <= i < len(tiles)]
        answer_text = " ".join(chosen_words)
        
        # Map display indices to original indices to check against correct_indices
        chosen_orig_indices = [shuffled_choices[i][0] for i in chosen_display_indices if 0 <= i < len(shuffled_choices)]
        
        # In listenTap, there can be multiple valid orderings or just correct_indices
        if correct_indices:
            is_correct = chosen_orig_indices == correct_indices
        elif correct_tokens:
            is_correct = _normalize_text(answer_text) == _normalize_text(" ".join(correct_tokens))
        else:
            is_correct = False
    except (ValueError, IndexError):
        answer_text = answer
        if correct_tokens:
            is_correct = _normalize_text(answer) == _normalize_text(" ".join(correct_tokens))
        else:
            is_correct = False

    expected_words = []
    if correct_indices:
        expected_words = [choices[i] if isinstance(choices[i], str) else choices[i].get("text", str(choices[i])) for i in correct_indices if 0 <= i < len(choices)]
    
    return {
        "correct": is_correct,
        "answer": answer_text,
        "expected": " ".join(expected_words) if expected_words else " ".join(correct_tokens),
    }


def _challenge_judge(challenge: dict) -> dict:
    """Handle 'judge' challenges (pick the correct sentence)."""
    prompt = challenge.get("prompt", "")
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)

    console.print(Panel(
        f"  [bold]{prompt}[/bold]\n",
        title=f"[{DUO_PURPLE}]🧑‍⚖️ Judge[/{DUO_PURPLE}]",
        border_style=DUO_PURPLE,
        padding=(1, 1),
    ))

    for i, choice in enumerate(choices):
        text = choice if isinstance(choice, str) else choice.get("sentence", str(choice))
        console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")

    console.print()
    answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")

    try:
        chosen_idx = int(answer) - 1
        is_correct = chosen_idx == correct_idx
    except ValueError:
        is_correct = False
        chosen_idx = -1

    expected_text = choices[correct_idx] if isinstance(choices[correct_idx], str) else choices[correct_idx].get("sentence", "?")
    # The 'guess' field must be the index as a string (e.g. "2"), matching the browser
    return {"correct": is_correct, "answer": str(chosen_idx), "expected": f"{correct_idx + 1}) {expected_text}"}


def _challenge_select(challenge: dict) -> dict:
    """Handle select-from-options challenges."""
    prompt = challenge.get("prompt", "")
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)

    console.print(Panel(
        f"  [bold]{prompt}[/bold]",
        title=f"[{DUO_PURPLE}]🔤 Select[/{DUO_PURPLE}]",
        border_style=DUO_PURPLE,
        padding=(1, 1),
    ))

    for i, choice in enumerate(choices):
        text = choice if isinstance(choice, str) else choice.get("text", choice.get("phrase", str(choice)))
        console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")

    console.print()
    answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")

    try:
        chosen_idx = int(answer) - 1
        is_correct = chosen_idx == correct_idx
    except ValueError:
        is_correct = False

    expected_text = choices[correct_idx] if isinstance(choices[correct_idx], str) else choices[correct_idx].get("text", choices[correct_idx].get("phrase", "?"))
    # The 'guess' field must be the index as a string (e.g. "2"), matching the browser
    return {"correct": is_correct, "answer": str(chosen_idx), "expected": f"{correct_idx + 1}) {expected_text}"}


def _challenge_name(challenge: dict) -> dict:
    """Handle 'name this' challenges (type what you see/hear)."""
    prompt = challenge.get("prompt", "")
    correct_solutions = challenge.get("correctSolutions", [])
    correct_answers = challenge.get("correctAnswers", [])

    valid = set()
    if correct_solutions:
        valid.update(_normalize_text(s) for s in correct_solutions)
    if correct_answers:
        valid.update(_normalize_text(a) for a in correct_answers)

    expected = correct_solutions[0] if correct_solutions else (
        correct_answers[0] if correct_answers else "?"
    )

    console.print(Panel(
        f"  [bold]{prompt}[/bold]",
        title=f"[{DUO_ORANGE}]🏷️ Name[/{DUO_ORANGE}]",
        border_style=DUO_ORANGE,
        padding=(1, 1),
    ))

    answer = Prompt.ask(f"  [{DUO_GREEN}]Your answer[/{DUO_GREEN}]")
    is_correct = _normalize_text(answer) in valid

    return {"correct": is_correct, "answer": answer, "expected": expected}


def _challenge_assist(challenge: dict) -> dict:
    """Handle 'assist' challenges (choose the meaning)."""
    prompt = challenge.get("prompt", "")
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)

    console.print(Panel(
        f"  What does this mean?\n\n  [bold]{prompt}[/bold]",
        title=f"[{DUO_BLUE}]💡 Assist[/{DUO_BLUE}]",
        border_style=DUO_BLUE,
        padding=(1, 1),
    ))

    for i, choice in enumerate(choices):
        text = choice if isinstance(choice, str) else choice.get("text", str(choice))
        console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")

    console.print()
    answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")

    try:
        chosen_idx = int(answer) - 1
        is_correct = chosen_idx == correct_idx
    except ValueError:
        is_correct = False

    expected_text = choices[correct_idx] if isinstance(choices[correct_idx], str) else choices[correct_idx].get("text", "?")
    return {"correct": is_correct, "answer": answer, "expected": f"{correct_idx + 1}) {expected_text}"}


def _challenge_match(challenge: dict) -> dict:
    """Handle match challenges (pair items)."""
    pairs = challenge.get("pairs", [])
    correct_answers = challenge.get("correctAnswers", [])

    if not pairs:
        return _challenge_generic(challenge)

    # Show the pairs to match
    left_items = []
    right_items = []
    for pair in pairs:
        from_text = pair.get("fromToken", pair.get("learningWord", "?"))
        to_text = pair.get("learningToken", pair.get("toToken", pair.get("translation", "?")))
        left_items.append(from_text)
        right_items.append(to_text)

    # Shuffle right side for the quiz
    shuffled_right = list(enumerate(right_items))
    random.shuffle(shuffled_right)

    console.print(Panel(
        "  [bold]Match the pairs![/bold]",
        title=f"[{DUO_GOLD}]🔗 Match[/{DUO_GOLD}]",
        border_style=DUO_GOLD,
        padding=(1, 1),
    ))

    table = Table(box=None, show_header=True, padding=(0, 3))
    table.add_column("Left", style=f"bold {DUO_GREEN}")
    table.add_column("Options", style=DUO_BLUE)

    for i, left in enumerate(left_items):
        opts = ", ".join(f"{chr(65+j)}={shuffled_right[j][1]}" for j in range(len(shuffled_right)))
        table.add_row(f"{i+1}. {left}", "")

    console.print(table)

    console.print()
    console.print(f"  [dim]Options:[/dim]")
    for j, (orig_idx, text) in enumerate(shuffled_right):
        console.print(f"    [{DUO_BLUE}]{chr(65+j)}[/{DUO_BLUE}]) {text}")

    console.print()
    console.print(f"  [dim]Enter matches like: 1A 2C 3B[/dim]")
    answer = Prompt.ask(f"  [{DUO_GREEN}]Your matches[/{DUO_GREEN}]")

    # Parse and check
    correct_count = 0
    try:
        match_pairs = answer.strip().split()
        for mp in match_pairs:
            num = int(mp[:-1]) - 1
            letter = ord(mp[-1].upper()) - 65
            if 0 <= num < len(left_items) and 0 <= letter < len(shuffled_right):
                orig_idx = shuffled_right[letter][0]
                if orig_idx == num:
                    correct_count += 1
    except (ValueError, IndexError):
        pass

    is_correct = correct_count == len(pairs)
    return {
        "correct": is_correct,
        "answer": answer,
        "expected": " ".join(f"{i+1}{chr(65+shuffled_right.index((i, right_items[i])))}" for i in range(len(left_items)))
    }


def _challenge_gap_fill(challenge: dict) -> dict:
    """Handle gap fill / cloze challenges."""
    prompt = challenge.get("displayTokens", [])
    correct_answers = challenge.get("correctAnswers", [])
    correct_solutions = challenge.get("correctSolutions", [])
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", -1)

    # Build display string and extract blank answers
    display_parts = []
    blank_answers = []
    for token in prompt:
        if isinstance(token, dict):
            if token.get("isBlank"):
                display_parts.append("[___]")
                if token.get("text"):
                    blank_answers.append(token.get("text"))
            else:
                display_parts.append(token.get("text", ""))
        else:
            display_parts.append(str(token))

    display_str = " ".join(display_parts).strip()
    if not display_str:
        display_str = challenge.get("prompt", "Fill in the blank")

    # Prepare content with optional translation
    translation = challenge.get("solutionTranslation", "")
    if not translation and challenge.get("prompt") and challenge.get("displayTokens"):
        # In reverse translation gap fills, the prompt is the translation hint
        translation = challenge.get("prompt")

    content = f"  [bold]{display_str}[/bold]"
    if translation:
        content += f"\n\n  [dim]Translation: {translation}[/dim]"

    # If it's a multiple choice gap fill
    if choices:
        console.print(Panel(
            content,
            title=f"[{DUO_ORANGE}]✏️ Fill the Gap[/{DUO_ORANGE}]",
            border_style=DUO_ORANGE,
            padding=(1, 1),
        ))
        for i, choice in enumerate(choices):
            text = choice if isinstance(choice, str) else choice.get("text", str(choice))
            console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")
        
        correct_indices = challenge.get("correctIndices", [])
        if not correct_indices and correct_idx != -1:
            correct_indices = [correct_idx]
            
        console.print()
        if len(correct_indices) > 1:
            answer = Prompt.ask(f"  [{DUO_GREEN}]Your choices (numbers, space separated)[/{DUO_GREEN}]")
            try:
                chosen_indices = [int(x.strip()) - 1 for x in answer.split()]
                is_correct = chosen_indices == correct_indices
            except ValueError:
                is_correct = False
        else:
            answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")
            try:
                chosen_idx = int(answer.strip()) - 1
                is_correct = chosen_idx == (correct_indices[0] if correct_indices else -1)
            except ValueError:
                is_correct = False
            
        expected_texts = []
        for idx in correct_indices:
            if 0 <= idx < len(choices):
                expected_texts.append(choices[idx] if isinstance(choices[idx], str) else choices[idx].get("text", "?"))
            else:
                expected_texts.append("?")
                
        if len(correct_indices) > 1:
            expected_str = " ".join(f"{idx+1}){text}" for idx, text in zip(correct_indices, expected_texts))
        else:
            expected_str = f"{correct_indices[0]+1}) {expected_texts[0]}" if correct_indices else "?"

        return {"correct": is_correct, "answer": answer, "expected": expected_str}

    # If it's a text entry gap fill
    valid = set()
    if correct_answers:
        valid.update(_normalize_text(a) for a in correct_answers)
    if correct_solutions:
        valid.update(_normalize_text(s) for s in correct_solutions)
    if blank_answers:
        valid.update(_normalize_text(b) for b in blank_answers)

    expected = correct_answers[0] if correct_answers else (
        correct_solutions[0] if correct_solutions else (
            blank_answers[0] if blank_answers else "?"
        )
    )

    console.print(Panel(
        content,
        title=f"[{DUO_ORANGE}]✏️ Fill the Gap[/{DUO_ORANGE}]",
        border_style=DUO_ORANGE,
        padding=(1, 1),
    ))

    answer = Prompt.ask(f"  [{DUO_GREEN}]Fill in[/{DUO_GREEN}]")
    is_correct = _normalize_text(answer) in valid

    return {"correct": is_correct, "answer": answer, "expected": expected}


def _challenge_form(challenge: dict) -> dict:
    """Handle form/conjugation challenges."""
    prompt = challenge.get("prompt", "")
    correct_solutions = challenge.get("correctSolutions", [])
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)

    if choices:
        console.print(Panel(
            f"  [bold]{prompt}[/bold]",
            title=f"[{DUO_PURPLE}]📋 Form[/{DUO_PURPLE}]",
            border_style=DUO_PURPLE,
            padding=(1, 1),
        ))

        for i, choice in enumerate(choices):
            text = choice if isinstance(choice, str) else choice.get("text", str(choice))
            console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")

        console.print()
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")

        try:
            chosen_idx = int(answer) - 1
            is_correct = chosen_idx == correct_idx
        except ValueError:
            is_correct = False

        expected_text = choices[correct_idx] if isinstance(choices[correct_idx], str) else choices[correct_idx].get("text", "?")
        return {"correct": is_correct, "answer": answer, "expected": f"{correct_idx + 1}) {expected_text}"}
    else:
        console.print(Panel(
            f"  [bold]{prompt}[/bold]",
            title=f"[{DUO_PURPLE}]📋 Form[/{DUO_PURPLE}]",
            border_style=DUO_PURPLE,
            padding=(1, 1),
        ))
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your answer[/{DUO_GREEN}]")
        valid = set(_normalize_text(s) for s in correct_solutions) if correct_solutions else set()
        expected = correct_solutions[0] if correct_solutions else "?"
        is_correct = _normalize_text(answer) in valid
        return {"correct": is_correct, "answer": answer, "expected": expected}


def _challenge_definition(challenge: dict) -> dict:
    """Handle definition challenges."""
    prompt = challenge.get("prompt", "")
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)

    console.print(Panel(
        f"  What is the definition of:\n\n  [bold]{prompt}[/bold]",
        title=f"[{DUO_BLUE}]📖 Definition[/{DUO_BLUE}]",
        border_style=DUO_BLUE,
        padding=(1, 1),
    ))

    for i, choice in enumerate(choices):
        text = choice if isinstance(choice, str) else choice.get("text", str(choice))
        console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")

    console.print()
    answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")

    try:
        chosen_idx = int(answer) - 1
        is_correct = chosen_idx == correct_idx
    except ValueError:
        is_correct = False

    expected_text = choices[correct_idx] if isinstance(choices[correct_idx], str) else choices[correct_idx].get("text", "?")
    return {"correct": is_correct, "answer": answer, "expected": f"{correct_idx + 1}) {expected_text}"}


def _challenge_listen(challenge: dict) -> dict:
    """Handle listen challenges (type what you hear — no audio in CLI)."""
    prompt = challenge.get("prompt", "")
    correct_solutions = challenge.get("correctSolutions", [])
    correct_answers = challenge.get("correctAnswers", [])
    # In CLI we show the sentence since there's no audio
    tts = challenge.get("tts", "")

    valid = set()
    if correct_solutions:
        valid.update(_normalize_text(s) for s in correct_solutions)
    if correct_answers:
        valid.update(_normalize_text(a) for a in correct_answers)

    expected = correct_solutions[0] if correct_solutions else (
        correct_answers[0] if correct_answers else "?"
    )

    console.print(Panel(
        f"  [dim]🔊 (Audio not available in CLI — hint below)[/dim]\n\n"
        f"  [bold italic]{prompt}[/bold italic]",
        title=f"[{DUO_ORANGE}]👂 Listen & Type[/{DUO_ORANGE}]",
        border_style=DUO_ORANGE,
        padding=(1, 1),
    ))

    answer = Prompt.ask(f"  [{DUO_GREEN}]Type what you hear[/{DUO_GREEN}]")
    is_correct = _normalize_text(answer) in valid

    return {"correct": is_correct, "answer": answer, "expected": expected}


def _challenge_listen_isolation(challenge: dict) -> dict:
    """Handle listenIsolation challenges (fill missing audio token)."""
    tokens = challenge.get("tokens", [])
    start = challenge.get("blankRangeStart", 0)
    end = challenge.get("blankRangeEnd", 0)
    options = challenge.get("options", [])
    correct_idx = challenge.get("correctIndex", 0)
    translation = challenge.get("solutionTranslation", "")
    
    display_parts = []
    for i, token in enumerate(tokens):
        if start <= i < end:
            if i == start:
                display_parts.append("[___]")
        else:
            val = token if isinstance(token, str) else token.get("value", "")
            display_parts.append(val)
            
    display_str = "".join(display_parts).strip()
    
    console.print(Panel(
        f"  [dim]🎵 (Audio missing in CLI)[/dim]\n\n"
        f"  [bold]{display_str}[/bold]\n\n"
        f"  [dim]Translation: {translation}[/dim]",
        title=f"[{DUO_ORANGE}]👂 Listen & Select[/{DUO_ORANGE}]",
        border_style=DUO_ORANGE,
        padding=(1, 1),
    ))

    for i, opt in enumerate(options):
        text = opt if isinstance(opt, str) else opt.get("text", str(opt))
        console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")

    console.print()
    answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")

    try:
        chosen_idx = int(answer) - 1
        is_correct = chosen_idx == correct_idx
    except ValueError:
        is_correct = False
        chosen_idx = -1

    expected_text = options[correct_idx] if isinstance(options[correct_idx], str) else options[correct_idx].get("text", "?")
    # For options style guess, return the chosen index as a string
    return {"correct": is_correct, "answer": str(chosen_idx), "expected": f"{correct_idx + 1}) {expected_text}"}


def _challenge_comprehension(challenge: dict) -> dict:
    """Handle reading/writing comprehension."""
    prompt = challenge.get("prompt", "")
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)

    console.print(Panel(
        f"  [bold]{prompt}[/bold]",
        title=f"[{DUO_PURPLE}]📖 Comprehension[/{DUO_PURPLE}]",
        border_style=DUO_PURPLE,
        padding=(1, 1),
    ))

    if choices:
        for i, choice in enumerate(choices):
            text = choice if isinstance(choice, str) else choice.get("text", str(choice))
            console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")

        console.print()
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice (number)[/{DUO_GREEN}]")

        try:
            chosen_idx = int(answer) - 1
            is_correct = chosen_idx == correct_idx
        except ValueError:
            is_correct = False

        expected_text = choices[correct_idx] if isinstance(choices[correct_idx], str) else choices[correct_idx].get("text", "?")
        return {"correct": is_correct, "answer": answer, "expected": f"{correct_idx + 1}) {expected_text}"}
    else:
        correct_solutions = challenge.get("correctSolutions", [])
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your answer[/{DUO_GREEN}]")
        valid = set(_normalize_text(s) for s in correct_solutions) if correct_solutions else set()
        expected = correct_solutions[0] if correct_solutions else "?"
        is_correct = _normalize_text(answer) in valid
        return {"correct": is_correct, "answer": answer, "expected": expected}


def _challenge_dialogue(challenge: dict) -> dict:
    """Handle dialogue challenges."""
    prompt = challenge.get("prompt", "")
    dialogue_turns = challenge.get("dialogue", [])
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)

    # Build the dialogue context: show all turns EXCEPT the last one,
    # because the last turn IS the correct answer (showing it would spoil it).
    if dialogue_turns:
        # Show all context turns (all but the last if last matches a choice)
        context_turns = dialogue_turns[:-1] if len(dialogue_turns) > 1 else dialogue_turns
        lines = []
        for turn in context_turns:
            text = turn.get("text", "")
            if not text and "displayTokens" in turn:
                text = "".join(t.get("text", "") for t in turn["displayTokens"])
            if text:
                lines.append(text)
        if lines:
            prompt = "\n  💬 ".join(lines)
        elif not prompt:
            # fallback: show full dialogue if context is empty
            for turn in dialogue_turns:
                text = turn.get("text", "")
                if not text and "displayTokens" in turn:
                    text = "".join(t.get("text", "") for t in turn["displayTokens"])
                if text:
                    lines.append(text)
            prompt = "\n  💬 ".join(lines)
    elif not prompt:
        prompt = "What would you say next?"

    console.print(Panel(
        f"  💬 [bold]{prompt}[/bold]",
        title=f"[{DUO_BLUE}]🗣️ Dialogue[/{DUO_BLUE}]",
        border_style=DUO_BLUE,
        padding=(1, 1),
    ))

    if choices:
        for i, choice in enumerate(choices):
            text = choice if isinstance(choice, str) else choice.get("text", str(choice))
            console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")
        console.print()
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your response (number)[/{DUO_GREEN}]")
        try:
            chosen_idx = int(answer) - 1
            is_correct = chosen_idx == correct_idx
        except ValueError:
            is_correct = False
        expected_text = choices[correct_idx] if isinstance(choices[correct_idx], str) else choices[correct_idx].get("text", "?")
        return {"correct": is_correct, "answer": answer, "expected": f"{correct_idx + 1}) {expected_text}"}
    else:
        return _challenge_generic(challenge)


def _challenge_free_response(challenge: dict) -> dict:
    """Handle free response challenges."""
    prompt = challenge.get("prompt", "")
    correct_solutions = challenge.get("correctSolutions", [])
    correct_answers = challenge.get("correctAnswers", [])

    valid = set()
    if correct_solutions:
        valid.update(_normalize_text(s) for s in correct_solutions)
    if correct_answers:
        valid.update(_normalize_text(a) for a in correct_answers)

    expected = correct_solutions[0] if correct_solutions else (
        correct_answers[0] if correct_answers else "?"
    )

    console.print(Panel(
        f"  [bold]{prompt}[/bold]",
        title=f"[{DUO_GREEN}]✍️ Free Response[/{DUO_GREEN}]",
        border_style=DUO_GREEN,
        padding=(1, 1),
    ))

    answer = Prompt.ask(f"  [{DUO_GREEN}]Your answer[/{DUO_GREEN}]")
    is_correct = _normalize_text(answer) in valid

    return {"correct": is_correct, "answer": answer, "expected": expected}


def _challenge_speak(challenge: dict) -> dict:
    """Handle speak/listenSpeak challenges (no microphone in CLI — auto-accepted)."""
    prompt = challenge.get("prompt", "")
    correct_solutions = challenge.get("correctSolutions", [])
    expected = correct_solutions[0] if correct_solutions else prompt

    ctype = challenge.get("type", "speak")
    if ctype == "listenSpeak":
        title = f"[{DUO_ORANGE}]🎤 Speak (Listen)[/{DUO_ORANGE}]"
        hint = "[dim]🎵 Listen, then speak — no audio/mic in CLI[/dim]"
    else:
        title = f"[{DUO_ORANGE}]🎤 Speak[/{DUO_ORANGE}]"
        hint = "[dim]🎤 Say this out loud — no microphone in CLI[/dim]"

    console.print(Panel(
        f"  {hint}\n\n  [bold]{prompt or expected}[/bold]",
        title=title,
        border_style=DUO_ORANGE,
        padding=(1, 1),
    ))
    console.print(f"  [dim]Press Enter to continue (auto-accepted) ↵[/dim]")
    Prompt.ask(f"  [{DUO_GREEN}]Press Enter[/{DUO_GREEN}]", default="")

    return {"correct": True, "answer": expected, "expected": expected}


def _challenge_generic(challenge: dict) -> dict:
    """
    Fallback handler for unsupported challenge types.
    Shows available info and lets the user try to answer.
    """
    ctype = challenge.get("type", "unknown")
    prompt = challenge.get("prompt", "")
    choices = challenge.get("choices", [])
    correct_idx = challenge.get("correctIndex", 0)
    correct_solutions = challenge.get("correctSolutions", [])
    correct_answers = challenge.get("correctAnswers", [])

    console.print(Panel(
        f"  [dim]Challenge type: {ctype}[/dim]\n\n  [bold]{prompt}[/bold]",
        title=f"[{DUO_GRAY}]❓ Challenge[/{DUO_GRAY}]",
        border_style=DUO_GRAY,
        padding=(1, 1),
    ))

    if choices:
        for i, choice in enumerate(choices):
            text = choice if isinstance(choice, str) else choice.get("text", str(choice))
            console.print(f"    [{DUO_BLUE}]{i + 1}[/{DUO_BLUE}]) {text}")
        console.print()
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your choice/answer[/{DUO_GREEN}]")
        try:
            chosen_idx = int(answer) - 1
            is_correct = chosen_idx == correct_idx
        except ValueError:
            valid = set()
            if correct_solutions:
                valid.update(_normalize_text(s) for s in correct_solutions)
            if correct_answers:
                valid.update(_normalize_text(a) for a in correct_answers)
            is_correct = _normalize_text(answer) in valid
    else:
        answer = Prompt.ask(f"  [{DUO_GREEN}]Your answer[/{DUO_GREEN}]")
        valid = set()
        if correct_solutions:
            valid.update(_normalize_text(s) for s in correct_solutions)
        if correct_answers:
            valid.update(_normalize_text(a) for a in correct_answers)
        is_correct = _normalize_text(answer) in valid

    expected = correct_solutions[0] if correct_solutions else (
        correct_answers[0] if correct_answers else "?"
    )
    return {"correct": is_correct, "answer": answer, "expected": expected}


def _print_session_summary(correct: int, total: int, elapsed: float) -> None:
    """Print session results summary."""
    pct = (correct / total * 100) if total > 0 else 0
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    if pct >= 90:
        grade_emoji = "🌟"
        grade_text = "Perfect!"
        grade_color = DUO_GOLD
    elif pct >= 70:
        grade_emoji = "✨"
        grade_text = "Great job!"
        grade_color = DUO_GREEN
    elif pct >= 50:
        grade_emoji = "👍"
        grade_text = "Good effort!"
        grade_color = DUO_BLUE
    else:
        grade_emoji = "💪"
        grade_text = "Keep practicing!"
        grade_color = DUO_ORANGE

    console.print(Rule(style=DUO_GREEN))
    console.print()

    lines = []
    lines.append(Text(f"  {grade_emoji} {grade_text}", style=f"bold {grade_color}"))
    lines.append(Text(""))
    lines.append(Text(f"  Score: ", style="dim").append(f"{correct}/{total} ({pct:.0f}%)", style=f"bold {grade_color}"))
    lines.append(Text(f"  Time:  ", style="dim").append(f"{minutes}m {seconds}s", style="bold"))
    lines.append(Text(""))

    # Score bar
    filled = int(pct / 5)
    bar = f"  {'█' * filled}{'░' * (20 - filled)}"
    lines.append(Text(bar, style=grade_color))

    from rich.console import Group
    console.print(Panel(
        Group(*lines),
        title=f"[{DUO_GREEN}]📊 Session Results[/{DUO_GREEN}]",
        border_style=DUO_GREEN,
        padding=(1, 1),
    ))


def _random_encouragement() -> str:
    """Return a random encouragement message."""
    messages = [
        "🎉 Amazing!", "👏 Well done!", "🌟 Fantastic!",
        "💪 You got it!", "🔥 On fire!", "⭐ Brilliant!",
        "🎯 Spot on!", "✨ Excellent!", "🏆 Champion!",
        "🚀 Incredible!", "💫 Superb!", "🦉 Duo approves!",
    ]
    return random.choice(messages)
