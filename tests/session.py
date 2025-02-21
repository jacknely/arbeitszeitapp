from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


class FakeSession:
    class UserRole(enum.Enum):
        member = enum.auto()
        company = enum.auto()
        accountant = enum.auto()

    @dataclass
    class LoginAttempt:
        user_role: FakeSession.UserRole
        email: str
        is_remember: bool

    def __init__(self) -> None:
        self._current_user_id: Optional[UUID] = None
        self._is_logged_in = False
        self._recent_logins: List[FakeSession.LoginAttempt] = []
        self._next_url: Optional[str] = None

    def is_logged_in(self) -> bool:
        return self._is_logged_in

    def set_current_user_id(self, user_id: Optional[UUID]) -> None:
        self._current_user_id = user_id

    def get_current_user(self) -> Optional[UUID]:
        return self._current_user_id

    def login_member(self, email: str, remember: bool = False) -> None:
        self._recent_logins.append(
            self.LoginAttempt(
                user_role=self.UserRole.member,
                email=email,
                is_remember=remember,
            )
        )
        self._is_logged_in = True

    def login_company(self, email: str, remember: bool = False) -> None:
        self._recent_logins.append(
            self.LoginAttempt(
                user_role=self.UserRole.company,
                email=email,
                is_remember=remember,
            )
        )
        self._is_logged_in = True

    def login_accountant(self, email: str, remember: bool = False) -> None:
        self._recent_logins.append(
            self.LoginAttempt(
                user_role=self.UserRole.accountant,
                email=email,
                is_remember=remember,
            )
        )
        self._is_logged_in = True

    def get_most_recent_login(self) -> Optional[LoginAttempt]:
        if not self._recent_logins:
            return None
        else:
            return self._recent_logins[-1]

    def set_next_url(self, url: Optional[str]) -> None:
        self._next_url = url

    def pop_next_url(self) -> Optional[str]:
        next_url = self._next_url
        self._next_url = None
        return next_url

    def logout(self) -> None:
        self._is_logged_in = False
