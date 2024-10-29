from __future__ import annotations

from typing import TYPE_CHECKING, Union, cast, List, Type

from git import Repo

from wexample_filestate.operation.abstract_operation import AbstractOperation
from wexample_filestate.operation.file_create_operation import FileCreateOperation
from wexample_filestate.operation.mixin.file_manipulation_operation_mixin import FileManipulationOperationMixin
from wexample_filestate.option.should_exist_option import ShouldExistOption
from wexample_filestate_git.operation.abstract_git_operation import AbstractGitOperation
from wexample_helpers.const.globals import DIR_GIT

if TYPE_CHECKING:
    from wexample_filestate.item.file_state_item_directory_target import FileStateItemDirectoryTarget
    from wexample_filestate.item.file_state_item_file_target import FileStateItemFileTarget


class GitInitOperation(FileManipulationOperationMixin, AbstractGitOperation):
    _original_path_str: str
    _has_initialized_git: bool = False

    def dependencies(self) -> List[Type["AbstractOperation"]]:
        return [
            FileCreateOperation
        ]

    @staticmethod
    def applicable(target: Union["FileStateItemDirectoryTarget", "FileStateItemFileTarget"]) -> bool:
        from wexample_filestate_git.option.git_option import GitOption
        from wexample_helpers.helpers.git_helper import git_is_init

        option = cast(GitOption, target.get_option(GitOption))

        return option and option.should_have_git() and not git_is_init(target.path)

    def describe_before(self) -> str:
        return 'No initialized .git directory'

    def describe_after(self) -> str:
        return 'Initialized .git directory'

    def description(self) -> str:
        return 'Initialize .git directory'

    def apply(self) -> None:
        path = self._get_target_file_path(target=self.target)
        self._has_initialized_git = True

        repo = Repo.init(path)
        repo.init()

    def undo(self) -> None:
        import shutil

        if self._has_initialized_git:
            shutil.rmtree(self._get_target_file_path(target=self.target) + DIR_GIT)
