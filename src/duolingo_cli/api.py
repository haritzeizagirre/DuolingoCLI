"""
Duolingo API client.

Reverse-engineered unofficial API client that communicates with
Duolingo's internal endpoints. Uses the versioned API at
https://www.duolingo.com/2017-06-30/

⚠️  This is unofficial and may break at any time.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

BASE_URL = "https://www.duolingo.com"
API_URL = f"{BASE_URL}/2017-06-30"

# Default challenge types for practice sessions - exact match with browser payload
DEFAULT_CHALLENGE_TYPES = [
    "assist",
    "characterIntro",
    "characterMatch",
    "characterPuzzle",
    "characterSelect",
    "characterTrace",
    "characterWrite",
    "completeReverseTranslation",
    "definition",
    "dialogue",
    "extendedMatch",
    "extendedListenMatch",
    "form",
    "freeResponse",
    "gapFill",
    "judge",
    "listen",
    "listenComplete",
    "listenMatch",
    "match",
    "name",
    "listenComprehension",
    "listenIsolation",
    "listenSpeak",
    "listenTap",
    "mathChallengeBlob",
    "orderTapComplete",
    "partialListen",
    "partialReverseTranslate",
    "patternTapComplete",
    "radioBinary",
    "radioImageSelect",
    "radioListenMatch",
    "radioListenRecognize",
    "radioSelect",
    "readComprehension",
    "reverseAssist",
    "sameDifferent",
    "select",
    "selectPronunciation",
    "selectTranscription",
    "svgPuzzle",
    "syllableTap",
    "syllableListenTap",
    "speak",
    "tapCloze",
    "tapClozeTable",
    "tapComplete",
    "tapCompleteTable",
    "tapDescribe",
    "translate",
    "transliterate",
    "transliterationAssist",
    "typeCloze",
    "typeClozeTable",
    "typeComplete",
    "typeCompleteTable",
    "writeComprehension",
    "star",
    "normal",
    "fictional_board",
    "chessMatch",
    "chessPvpMatch",
    "chessMiniMatch",
    "mathProductSelect",
    "mathMatch",
    "mathMultiSelect",
    "mathPatternTable",
    "mathTypeFill",
    "mathIntegerNumberLineFill",
    "mathEstimateNumberLine",
    "mathExpressionBuild",
    "mathFactorTree",
    "mathFractionFill",
]

# Path experiments sent by the browser
PATH_EXPERIMENTS = [
    "BACKEND_REACTIVATION_REVIEW_NODE_ANDROID",
    "BACKEND_REACTIVATION_REVIEW_NODE_IOS",
    "BACKEND_RESURRECTION_REVIEW_NODE_ANDROID",
    "BACKEND_RESURRECTION_REVIEW_NODE_IOS",
]


class DuolingoAPIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class DuolingoClient:
    """
    Client for Duolingo's unofficial API.

    Requires a JWT token obtained from browser cookies.
    """

    def __init__(self, jwt_token: str):
        self.jwt_token = jwt_token
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Origin": "https://www.duolingo.com",
                "Referer": "https://www.duolingo.com/",
                "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
            },
            timeout=30.0,
            follow_redirects=True,
        )
        self._user_data: Optional[dict] = None

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ────────────────────────────────────────────
    # Internal helpers
    # ────────────────────────────────────────────

    def _request(
        self, method: str, path: str, **kwargs
    ) -> Any:
        """Make a request and handle errors."""
        url = path if path.startswith("http") else path
        response = self._client.request(method, url, **kwargs)

        if response.status_code == 401:
            raise DuolingoAPIError(
                401,
                "Token expired or invalid. Please update your JWT token with: duo auth login",
            )
        if response.status_code == 403:
            raise DuolingoAPIError(
                403,
                "Access forbidden. Your account may be restricted.",
            )
        if response.status_code >= 400:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            raise DuolingoAPIError(response.status_code, str(error_body))

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except Exception:
            raise DuolingoAPIError(
                response.status_code, 
                "Received a non-JSON response from Duolingo. The endpoint might be deprecated."
            )

    def _get(self, path: str, **kwargs) -> Any:
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs) -> Any:
        return self._request("POST", path, **kwargs)

    def _put(self, path: str, **kwargs) -> Any:
        return self._request("PUT", path, **kwargs)

    # ────────────────────────────────────────────
    # User & Profile
    # ────────────────────────────────────────────

    def get_user_id_from_token(self) -> str:
        """Decode the JWT token to extract the user ID."""
        import base64
        import json
        try:
            payload = self.jwt_token.split('.')[1]
            # Add padding if necessary
            payload += '=' * (-len(payload) % 4)
            decoded = base64.b64decode(payload).decode('utf-8')
            claims = json.loads(decoded)
            return str(claims.get('sub', ''))
        except Exception:
            return ""

    def get_user_info(self) -> dict:
        """
        Get current user info from the JWT token claims.
        Fetches the /users/{id} endpoint.
        """
        if self._user_data:
            return self._user_data
            
        user_id = self.get_user_id_from_token()
        if not user_id:
            raise DuolingoAPIError(400, "Could not extract user ID from JWT token. Make sure it's copied completely.")

        data = self._get(
            f"/2017-06-30/users/{user_id}",
            params={"fields": ",".join([
                "acquisitionSurveyReason",
                "adsConfig",
                "betaStatus",
                "bio",
                "blockedUserIds",
                "canUseModerationTools",
                "classroomLeaderboardsEnabled",
                "courses",
                "currentCourse",
                "creationDate",
                "currentCourseId",
                "email",
                "emailAnnouncement",
                "emailAssignment",
                "emailAssignmentComplete",
                "emailClassroomJoin",
                "emailClassroomLeave",
                "emailEditSuggested",
                "emailEventsDigest",
                "emailFollow",
                "emailPass",
                "emailPromotion",
                "emailResearch",
                "emailSchoolsAnnouncement",
                "emailSchoolsNewActivity",
                "emailSchoolsReport",
                "emailSchoolsSchedule",
                "emailStreakFreezeUsed",
                "emailStreamPost",
                "emailVerified",
                "emailWeeklyProgressReport",
                "emailWeeklyReport",
                "enableMicrophone",
                "enableSoundEffects",
                "enableSpeaker",
                "experiments",
                "facebookId",
                "fromLanguage",
                "gemsConfig",
                "globalAmbassadorStatus",
                "googleId",
                "hasPlus",
                "health",
                "id",
                "inviteURL",
                "joinedClassroomIds",
                "lastResurrectionTimestamp",
                "lastStreak",
                "learningLanguage",
                "lingots",
                "location",
                "monthlyXp",
                "name",
                "observedClassroomIds",
                "persistentNotifications",
                "picture",
                "plusDiscounts",
                "practiceReminderSettings",
                "privacySettings",
                "referralInfo",
                "rewardBundles",
                "roles",
                "sessionCount",
                "streak",
                "streakData",
                "subscription",
                "timezone",
                "timezoneOffset",
                "totalXp",
                "trackingProperties",
                "username",
                "webNotificationIds",
                "weeklyXp",
                "xpGains",
                "xpGoal",
                "zhTw",
            ])}
        )
        self._user_data = data
        return data

    def get_user_id(self) -> str:
        """Get the current user's ID."""
        info = self.get_user_info()
        return str(info.get("id", ""))

    def get_username(self) -> str:
        """Get the current user's username."""
        info = self.get_user_info()
        return info.get("username", "")

    def get_streak(self) -> dict:
        """Get streak information."""
        info = self.get_user_info()
        return {
            "streak": info.get("streak", 0),
            "streak_data": info.get("streakData", {}),
        }

    def get_courses(self) -> list[dict]:
        """Get user's courses (languages being learned)."""
        info = self.get_user_info()
        return info.get("courses", [])

    def get_current_course(self) -> Optional[dict]:
        """Get the current active course."""
        info = self.get_user_info()
        current_id = info.get("currentCourseId")
        courses = info.get("courses", [])
        for course in courses:
            if course.get("id") == current_id:
                return course
        return courses[0] if courses else None

    def get_xp_info(self) -> dict:
        """Get XP information."""
        info = self.get_user_info()
        return {
            "total_xp": info.get("totalXp", 0),
            "monthly_xp": info.get("monthlyXp", 0),
            "weekly_xp": info.get("weeklyXp", 0),
            "xp_goal": info.get("xpGoal", 0),
            "lingots": info.get("lingots", 0),
        }

    def get_health(self) -> dict:
        """Get health/hearts information."""
        info = self.get_user_info()
        return info.get("health", {})

    # ────────────────────────────────────────────
    # Leaderboard
    # ────────────────────────────────────────────

    def get_shop_items(self) -> dict:
        """Fetch available shop items and user balances."""
        try:
            return self._get(f"/2017-06-30/shop-items")
        except Exception:
            return {}

    def get_leaderboard(self) -> list[dict]:
        """Get the user's weekly leaderboard."""
        user_id = self.get_user_id()
        data = self._get(
            f"/2017-06-30/users/{user_id}/leaderboard",
        )
        # The response has an "active" key with leaderboard info
        if isinstance(data, dict):
            active = data.get("active", data)
            if isinstance(active, dict):
                return active.get("cohort", {}).get("rankings", [])
            return []
        return data if isinstance(data, list) else []

    # ────────────────────────────────────────────
    # Practice / Lessons
    # ────────────────────────────────────────────

    def get_next_lesson(self) -> Optional[dict]:
        """Find the next active lesson node in the user's current course path."""
        info = self.get_user_info()
        course = info.get("currentCourse", {})
        sections = course.get("pathSectioned", [])
        
        for section in sections:
            units = section.get("units", [])
            for u_idx, unit in enumerate(units):
                levels = unit.get("levels", [])
                for level_idx, level in enumerate(levels):
                    if level.get("state") in ["active", "accessible"]:
                        # Use pathLevelMetadata (not pathLevelClientData) — this is what
                        # the browser sends as pathLevelSpecifics in the PUT payload.
                        metadata = level.get("pathLevelMetadata", {})
                        skill_id = metadata.get("skillId")
                        if not skill_id:
                            client_data = level.get("pathLevelClientData", {})
                            skill_id = client_data.get("skillId")

                        # Build pathLevelSpecifics exactly as the browser does:
                        # from pathLevelMetadata + nodeState field
                        path_level_specifics = {
                            "skillId": metadata.get("skillId"),
                            "crownLevelIndex": metadata.get("crownLevelIndex", 0),
                            "treeId": metadata.get("treeId"),
                            "nodeState": level.get("state", "active"),
                            "lessonNumber": metadata.get("lessonNumber"),
                        }

                        return {
                            "id": level.get("id"),
                            "type": level.get("type"),
                            "debugName": level.get("debugName"),
                            "skillId": skill_id,
                            "levelId": level.get("id"),
                            "levelIndex": metadata.get("crownLevelIndex", 0),
                            "levelSessionIndex": level.get("finishedSessions", 0),
                            "isFinalLevel": level.get("finishedSessions", 0) >= level.get("totalSessions", 1) - 1,
                            "treeId": metadata.get("treeId") or course.get("id"),
                            "pathLevelSpecifics": path_level_specifics,
                            "sectionIndex": section.get("index", 0) + 1,  # 1-indexed for display
                            "unitIndex": u_idx + 1,  # 1-indexed relative to section
                        }
        return None

    def start_practice_session(
        self,
        from_language: Optional[str] = None,
        learning_language: Optional[str] = None,
        challenge_types: Optional[list[str]] = None,
        session_type: str = "GLOBAL_PRACTICE",
        skill_id: Optional[str] = None,
        level_id: Optional[str] = None,
        level_index: Optional[int] = None,
        level_session_index: Optional[int] = None,
        tree_id: Optional[str] = None,
        is_final_level: bool = False,
    ) -> dict:
        """
        Start a new practice session.

        Returns a session object containing challenges to solve.

        Args:
            from_language: Interface language (e.g., "en")
            learning_language: Target language (e.g., "es")
            challenge_types: List of challenge types to include
            session_type: "GLOBAL_PRACTICE", "LESSON", or "SKILL_PRACTICE"
            skill_id: Optional ID of the specific skill/lesson to start
            is_final_level: Whether this is the final session of the node

        Returns:
            Session dict with 'id', 'challenges', etc.
        """
        info = self.get_user_info()

        if not from_language:
            from_language = info.get("fromLanguage", "en")
        if not learning_language:
            learning_language = info.get("learningLanguage", "es")

        body = {
            "challengeTypes": challenge_types or DEFAULT_CHALLENGE_TYPES,
            "fromLanguage": from_language,
            "isCustomIntroSkill": False,
            "isFinalLevel": is_final_level,
            "isGrammarSkill": False,
            "isRedoingPassedNode": False,
            "isV2": True,
            "juicy": True,
            "learningLanguage": learning_language,
            "pathExperiments": PATH_EXPERIMENTS,
            "pathLevelSessionMetadata": {},
            "shakeToReportEnabled": True,
            "showGrammarSkillSplash": False,
            "smartTipsVersion": 2,
            "type": session_type,
        }
        
        if skill_id:
            body["skillId"] = skill_id
        if level_id is not None:
            body["levelId"] = level_id
        if level_index is not None:
            body["levelIndex"] = level_index
        if level_session_index is not None:
            body["levelSessionIndex"] = level_session_index
        if tree_id is not None:
            body["treeId"] = tree_id

        return self._post("/2017-06-30/sessions", json=body)

    def complete_session(
        self,
        session: dict,
        answers: list[dict],
        path_level_specifics: Optional[dict] = None,
        hearts_left: Optional[int] = None,
    ) -> dict:
        """
        Submit a completed session with answers.

        Args:
            session: The session object from start_practice_session
            answers: List of answer objects for each challenge
            path_level_specifics: The pathLevelSpecifics dict from the path node
            hearts_left: Number of hearts remaining, if applicable

        Returns:
            Session completion result with XP earned, etc.
        """
        session_id = session.get("id", "")

        # Inject answers into challenges
        idx = 0
        for c in session.get("challenges", []):
            if idx < len(answers):
                c["correct"] = answers[idx].get("correct", False)
                c["guess"] = answers[idx].get("answer", "")
                c["timeTaken"] = 5000
                idx += 1
                
        for c in session.get("adaptiveChallenges", []):
            if idx < len(answers):
                c["correct"] = answers[idx].get("correct", False)
                c["guess"] = answers[idx].get("answer", "")
                c["timeTaken"] = 5000
                idx += 1

        info = self.get_user_info()
        course_id = info.get("currentCourseId")

        import time
        end_time = int(time.time())
        start_time = session.get("startTime") or (end_time - 180)

        # Ensure heartsLeft is correctly specified
        final_hearts_left = hearts_left if hearts_left is not None else session.get("heartsLeft", 0)

        body = {
            **session,
            "heartsLeft": final_hearts_left,
            "startTime": start_time,
            "enableBonusPoints": True,
            "endTime": end_time,
            "failed": final_hearts_left <= 0 and hearts_left is not None,
            "maxInLessonStreak": len(answers),
            "shouldLearnThings": True,
            "courseId": course_id,
            "dailyRefreshInfo": None,
        }
        
        # Inject pathLevelSpecifics from the node
        if path_level_specifics:
            body["pathLevelSpecifics"] = path_level_specifics.copy()
        elif "pathLevelSpecifics" not in body and "metadata" in session:
            md = session.get("metadata", {})
            body["pathLevelSpecifics"] = {
                "skillId": md.get("skill_id"),
                "crownLevelIndex": 0,
                "levelIndex": md.get("level_index", 0),
                "lessonNumber": session.get("levelSessionIndex", 0) + 1,
            }

        return self._put(
            f"/2017-06-30/sessions/{session_id}",
            json=body,
        )

    # ────────────────────────────────────────────
    # XP Gains / Activity
    # ────────────────────────────────────────────

    def get_xp_summaries(self, days: int = 7) -> list[dict]:
        """Get daily XP summaries for the last N days."""
        user_id = self.get_user_id()
        import datetime
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days)

        return self._get(
            f"/2017-06-30/users/{user_id}/xp_summaries",
            params={
                "startDate": start_date.isoformat(),
                "endDate": today.isoformat(),
                "timezone": "UTC",
            },
        )
