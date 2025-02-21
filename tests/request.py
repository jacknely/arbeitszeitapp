from typing import Dict, Optional


class FakeRequest:
    def __init__(self) -> None:
        self._args: Dict[str, str] = dict()
        self._form: Dict[str, str] = dict()
        self._environ: Dict[str, str] = dict()

    def get_arg(self, arg: str) -> Optional[str]:
        return self._args.get(arg, None)

    def get_form(self, key: str) -> Optional[str]:
        return self._form.get(key, None)

    def get_environ(self, key: str) -> Optional[str]:
        return self._environ.get(key, None)

    def set_arg(self, arg: str, value: str) -> None:
        self._args[arg] = value

    def set_form(self, key: str, value: str) -> None:
        self._form[key] = value

    def set_environ(self, key: str, value: str) -> None:
        self._environ[key] = value
