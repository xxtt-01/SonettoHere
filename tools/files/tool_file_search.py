"""Tool: file_search — 列出目录内容、搜索文件。"""

from pathlib import Path

from pydantic import BaseModel, Field

from tools.base import ToolBase, check_path_access, format_error, format_success


class FileSearchInput(BaseModel):
    get_doc: bool = Field(
        default=False, description="设为 true 以获取使用说明和领域知识"
    )
    operation: str = Field(
        default="",
        description="操作类型: list_directory / search_files",
    )
    directory_path: str = Field(
        default="", description="目录路径（list_directory 操作）"
    )
    search_pattern: str = Field(
        default="", description="搜索模式（search_files 操作），支持 glob 通配符"
    )
    recursive: bool = Field(
        default=False, description="是否递归搜索（search_files 操作）"
    )
    file_filter: str = Field(
        default="all",
        description="过滤器: all / files_only / directories_only / by_extension",
    )
    extension: str = Field(default="", description="扩展名过滤，如 '.py'")


class FileSearchTool(ToolBase):
    name: str = "file_search"
    description: str = (
        "列出目录内容或使用 glob 通配符搜索文件。"
        "[调用积极性: 可自由看情况调用] [get_doc: 仅在发生错误时 get_doc]"
    )
    args_schema: type[BaseModel] = FileSearchInput

    def _run(
        self,
        get_doc: bool = False,
        operation: str = "",
        directory_path: str = "",
        search_pattern: str = "",
        recursive: bool = False,
        file_filter: str = "all",
        extension: str = "",
    ) -> str:
        if get_doc:
            return self._load_doc()
        if not operation:
            return format_error("operation 不能为空")

        if operation == "list_directory":
            return self._list_directory(directory_path)
        elif operation == "search_files":
            return self._search_files(
                search_pattern, directory_path, recursive, file_filter, extension
            )
        else:
            return format_error(f"未知的操作类型: {operation}")

    def _list_directory(self, directory_path: str) -> str:
        if not directory_path:
            directory_path = "."
        dp = Path(directory_path)
        if not dp.exists():
            return format_error(f"目录不存在: {directory_path}")
        if not dp.is_dir():
            return format_error(f"路径不是目录: {directory_path}")

        err = check_path_access(directory_path)
        if err:
            return format_error(err)

        items = []
        for fp in dp.iterdir():
            items.append({
                "name": fp.name,
                "path": str(fp),
                "is_file": fp.is_file(),
                "is_dir": fp.is_dir(),
                "size": fp.stat().st_size if fp.is_file() else 0,
            })

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        return format_success({
            "directory": str(dp.resolve()),
            "items": items,
            "count": len(items),
            "file_count": sum(1 for i in items if i["is_file"]),
            "dir_count": sum(1 for i in items if i["is_dir"]),
        })

    def _search_files(
        self,
        pattern: str,
        directory: str,
        recursive: bool,
        file_filter: str,
        extension: str,
    ) -> str:
        if not pattern:
            pattern = "*"
        if not directory:
            directory = "."
        if not Path(directory).exists():
            return format_error(f"搜索目录不存在: {directory}")

        err = check_path_access(directory)
        if err:
            return format_error(err)

        search_dir = Path(directory)
        glob_pattern = "**/" + pattern if recursive else pattern

        found = []
        for fp in sorted(search_dir.glob(glob_pattern)):
            if file_filter == "files_only" and not fp.is_file():
                continue
            if file_filter == "directories_only" and not fp.is_dir():
                continue
            if (
                file_filter == "by_extension"
                and extension
                and not fp.suffix.lower() == extension.lower()
                and not fp.name.lower().endswith(extension.lower())
            ):
                continue

            st = fp.stat()
            found.append({
                "path": str(fp),
                "name": fp.name,
                "is_file": fp.is_file(),
                "is_dir": fp.is_dir(),
                "size": st.st_size if fp.is_file() else 0,
            })

        found.sort(key=lambda x: x["path"].lower())
        return format_success({
            "search_pattern": pattern,
            "search_directory": str(search_dir.resolve()),
            "recursive": recursive,
            "file_filter": file_filter,
            "found_files": found,
            "count": len(found),
        })
