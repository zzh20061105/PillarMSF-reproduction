"""Read-only source checks; no model imports, downloads, or training."""

# 工程用途：比较来源锁中的预期记录与本机 Git 实际状态，只报告问题。
# 本文件全部使用 Python 标准库，不加载模型、CUDA 或数据集。
import argparse  # 解析 --project-root、--help 等命令行参数。
import json  # 读取 JSON 格式的来源锁。
import re  # 用正则表达式检查名称、提交编号等字段格式。
import shutil  # 在 PATH 中查找 Git 程序。
import subprocess  # 启动 Git 子进程，取得查询结果与退出码。
from pathlib import Path  # 以路径对象处理文件位置，兼容 Windows/Linux。
from urllib.parse import urlsplit  # 拆分 URL，分别检查协议、主机和路径。


class CheckError(Exception):
    """A Git query could not be completed."""
    # 用于汇总锁文件读取/校验或 Git 查询失败，由调用方决定退出码。


def repository_key(url):
    """Normalize supported GitHub URLs without returning embedded credentials."""
    # 输入：仓库地址。输出：小写 owner/repo；无法识别时抛出 ValueError。
    # HTTPS 和 SSH 地址可能表示同一仓库，因此先统一身份再比较。
    if not isinstance(url, str):
        raise ValueError("invalid repository URL")
    if url.startswith("git@github.com:"):
        path = url[len("git@github.com:"):]
    else:
        parsed = urlsplit(url)
        allowed_port = {"https": (None, 443), "ssh": (None, 22)}
        # 本工具只接受约定的 GitHub 地址形式，不联网验证远程仓库。
        if (parsed.hostname != "github.com" or parsed.scheme not in allowed_port
                or parsed.port not in allowed_port[parsed.scheme]
                or parsed.query or parsed.fragment):
            raise ValueError("unsupported repository URL")
        path = parsed.path.lstrip("/")
    path = path.rstrip("/").removesuffix(".git")
    # 只返回仓库路径，不返回 URL 中可能存在的用户名或密码。
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path):
        raise ValueError("invalid repository path")
    return path.lower()


def load_lock(project_root):
    # 输入：项目根目录。输出：校验过的来源记录列表；此处不查询实际仓库。
    lock_path = project_root / "environment" / "source-lock.json"
    try:
        # utf-8-sig 同时兼容普通 UTF-8 文件及带 BOM 的 UTF-8 文件。
        entries = json.loads(lock_path.read_text(encoding="utf-8-sig"))
        if not isinstance(entries, list) or not entries:
            raise ValueError("expected a nonempty list")
        names = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("expected an object")
            name, commit = entry.get("name"), entry.get("commit")
            # 名称随后用于拼接目录：禁止路径分隔符、路径跳转和重复名称。
            if (not isinstance(name, str)
                    or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name)
                    or name.lower() in names):
                raise ValueError("invalid or duplicate name")
            if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
                raise ValueError("expected a full commit SHA")
            # 这里只校验地址格式；clean 是历史记录，不用它决定当前状态。
            repository_key(entry.get("url"))
            names.add(name.lower())
        return entries
    except (OSError, UnicodeError, ValueError) as error:
        # 锁内容可能含凭据，只报告固定的失败摘要；from error 保留异常来源供调试。
        raise CheckError("cannot read or validate environment/source-lock.json") from error


def git_query(repo, *args):
    # 输入：仓库目录和 Git 参数。输出：去掉首尾空白的标准输出。
    # 当前调用均是查询；--no-optional-locks 减少可选锁及索引刷新。
    try:
        result = subprocess.run(
            # 使用参数列表，不拼接 shell 命令；-C 指定在哪个仓库查询。
            ["git", "--no-optional-locks", "-C", str(repo), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CheckError(f"Git query could not run: {args[0]}") from error
    if result.returncode:
        # Git 非零退出表示查询失败；不回显可能含原始地址的错误内容。
        raise CheckError(f"Git query failed: {args[0]}")
    return result.stdout.strip()


def check_source(project_root, entry):
    # 输入：根目录和一条来源记录。输出：问题列表；空列表表示本项通过。
    name = entry["name"]
    references = (project_root / "references").resolve()
    repo = (references / name).resolve()
    expected_key = repository_key(entry["url"])
    issues = []
    # resolve 解析实际路径；目录必须仍是 references 下的直接子目录。
    if repo.parent != references or not repo.is_dir():
        return ["reference directory is missing or outside references"]
    try:
        actual_root = Path(git_query(repo, "rev-parse", "--show-toplevel")).resolve()
        # Git 会向父目录寻找仓库，必须防止把项目主仓库误认成参考仓库。
        if actual_root != repo:
            return ["directory is not the root of its own Git repository"]
        actual_sha = git_query(repo, "rev-parse", "--verify", "HEAD")
        # HEAD 是当前实际提交；与来源锁里的完整 SHA 比较。
        if actual_sha.lower() != entry["commit"].lower():
            issues.append(f"HEAD mismatch: expected {entry['commit']}, found {actual_sha}")
        try:
            # origin 来自本地配置，比较规范化后的仓库身份，不访问网络。
            actual_key = repository_key(git_query(repo, "remote", "get-url", "origin"))
            if actual_key != expected_key:
                issues.append(f"origin mismatch: expected github.com/{expected_key}")
        except ValueError:
            issues.append("origin is not a supported GitHub repository URL")
        status = git_query(repo, "status", "--porcelain=v1", "--untracked-files=all")
        # 查询涵盖暂存、未暂存和未跟踪改动；Git 忽略的文件不在此范围。
        if status:
            issues.append(f"worktree is not clean: {len(status.splitlines())} status entries")
    except CheckError as error:
        # 一份仓库查询失败也记为该项问题，其他仓库仍可继续检查。
        issues.append(str(error))
    return issues


def main():
    # 总入口：组织参数、来源锁读取、逐仓库检查，以及结果汇总。
    parser = argparse.ArgumentParser(
        description="Check pinned reference sources without importing model packages.")
    parser.add_argument(
        # 默认从本脚本的位置推算根目录，避免依赖终端当前所在目录。
        "--project-root", type=Path, default=Path(__file__).resolve().parents[1],
        help="project containing environment/source-lock.json and references/",
    )
    args = parser.parse_args()
    # expanduser 展开 ~，resolve 转成解析后的绝对路径。
    project_root = args.project_root.expanduser().resolve()
    try:
        entries = load_lock(project_root)
        if shutil.which("git") is None:
            raise CheckError("Git is not available on PATH")
    except CheckError as error:
        print(f"[ERROR] {error}")
        # 退出码 2：锁无法使用或找不到 Git，不能开始正常来源核验。
        return 2
    failures = 0
    for entry in entries:
        issues = check_source(project_root, entry)
        label = "FAIL" if issues else "PASS"
        print(f"[{label}] {entry['name']} | github.com/{repository_key(entry['url'])}")
        if issues:
            # failures 统计失败的仓库数，而不是问题条数。
            failures += 1
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"  HEAD {entry['commit']} | clean")
    print(f"Sources checked: {len(entries)}; passed: {len(entries) - failures}; failed: {failures}")
    print("Scope: source identity/version/worktree only; model and server runtime are unverified.")
    # 退出码 0：全部来源通过；1：至少一个来源有问题。均不代表模型验收。
    return 1 if failures else 0


if __name__ == "__main__":
    # 直接运行本文件时调用 main；被其他文件 import 时不自动开始核验。
    # main 返回退出码，再由 SystemExit 将其交给调用本程序的终端或工具。
    raise SystemExit(main())
