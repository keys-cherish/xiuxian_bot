"""命令注册表 - 统一管理所有跨平台命令。"""

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CommandDef:
    """命令定义。"""
    name: str
    description: str
    category: str  # game / social / admin
    handler: Callable
    aliases: List[str] = field(default_factory=list)
    cooldown: int = 0
    require_account: bool = True
    admin_only: bool = False


class CommandRegistry:
    """命令注册表单例。"""

    _instance: Optional["CommandRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._commands: Dict[str, CommandDef] = {}
            cls._instance._alias_map: Dict[str, str] = {}
        return cls._instance

    def register(self, cmd: CommandDef) -> None:
        """注册一个命令。"""
        self._commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self._alias_map[alias] = cmd.name

    def get(self, name: str) -> Optional[CommandDef]:
        """通过命令名或别名查找命令。"""
        real_name = self._alias_map.get(name, name)
        return self._commands.get(real_name)

    def list_by_category(self, category: str) -> List[CommandDef]:
        """按分类列出命令。"""
        return [c for c in self._commands.values() if c.category == category]

    @property
    def all_commands(self) -> Dict[str, CommandDef]:
        return dict(self._commands)


# 全局注册表
registry = CommandRegistry()


def command(name: str, *, description: str = "", category: str = "game",
            aliases: list = None, cooldown: int = 0,
            require_account: bool = True, admin_only: bool = False):
    """装饰器：将函数注册为命令。

    用法::

        @command("hunt", description="狩猎怪物", aliases=["h", "dy"])
        async def handle_hunt(user_id: str, **kwargs):
            ...
    """
    def decorator(func):
        cmd = CommandDef(
            name=name,
            description=description,
            category=category,
            handler=func,
            aliases=aliases or [],
            cooldown=cooldown,
            require_account=require_account,
            admin_only=admin_only,
        )
        registry.register(cmd)
        return func
    return decorator
