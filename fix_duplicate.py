import json
import shutil
import sqlite3
from enum import IntEnum
from pathlib import Path

import click
from colorama import Fore
from tqdm import tqdm


class OutputLevel(IntEnum):
    INFO = 0
    WARN = 1
    ERROR = 2


def style(msg, level=0):
    colors = [Fore.RESET, Fore.YELLOW, Fore.RED]
    return colors[level] + msg + Fore.RESET


def find_first_relative(paths, roots):
    for rf in roots:
        for p in paths:
            if p.is_relative_to(rf):
                return p


@click.command()
@click.argument("folder_path", nargs=1)
@click.option("-d", "--dry-run", default=False, is_flag=True)
@click.option("-q/-v", "--quiet/--verbose", default=True, is_flag=True)
def concat(folder_path, dry_run, quiet):
    body_path = Path(folder_path)
    if not body_path.exists():
        print(
            style(
                f"E: The provided path {body_path} does not exist. aborting.",
                OutputLevel.ERROR,
            )
        )
        exit()

    config_path = body_path / "config_sys.json"
    config_path_alt = body_path / "config.json"

    config_path = (config_path.exists() and config_path) or (
        config_path_alt.exists() and config_path_alt
    )
    if not config_path:
        print(style(f"E: Cannot find config file. aborting.", OutputLevel.ERROR))
        exit()

    with open(config_path, "r", encoding="utf-8") as f:
        # get root folders
        config = json.load(f)
        root_folders = [Path(pathstr) for pathstr in config["bmsroot"]]

    db_path = body_path / "songdata.db"
    if not db_path.exists():
        print(style(f"E: Cannot find song DB. aborting.", OutputLevel.ERROR))
        exit()

    with sqlite3.connect(db_path) as con:
        # find duplicate files
        res = con.execute(
            "select `sha256`, `path` from song where `sha256` in "
            "(select `sha256` from song group by `sha256` having count(`sha256`) > 1) "
            "order by `sha256` asc;"
        )

        songs = {}
        for row in res.fetchall():
            if (hash := row[0]) in songs:
                songs[hash].append(Path(row[1]))
            else:
                songs[hash] = [Path(row[1])]

    total_len = sum([len(paths) - 1 for paths in songs.values()])
    print(f"I: Found {total_len} duplicated charts.")
    denied_set = set()

    with tqdm(
        total=total_len,
        unit="file",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} eta. {remaining}, {rate_fmt}{postfix}]",
    ) as bar:
        for hash, paths in songs.items():
            primary = find_first_relative(paths, root_folders)

            for dup_path in paths:
                if dup_path == primary:
                    continue
                if not dup_path.exists():
                    if not quiet:
                        bar.write(
                            style(
                                f"W: Path:{dup_path}, does not exist. skipped.",
                                OutputLevel.WARN,
                            )
                        )
                    bar.update()
                    continue

                src_dir = dup_path.parent
                dst_dir = primary.parent
                try:
                    if src_dir == dst_dir:
                        # same file in same folder
                        if not dry_run:
                            dup_path.unlink()
                        if not quiet:
                            bar.write(
                                style(
                                    f"I: {dup_path} removed as the same file exists in the same folder.",
                                    OutputLevel.INFO,
                                )
                            )
                    else:
                        if not dry_run:
                            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                            shutil.rmtree(src_dir)
                        if not quiet:
                            bar.write(
                                style(
                                    f"I: {src_dir} merged to {dst_dir}",
                                    OutputLevel.INFO,
                                )
                            )
                except (shutil.Error, PermissionError):
                    bar.write(
                        style(
                            f"E: path:{src_dir}, permission denied. skipped.",
                            OutputLevel.ERROR,
                        )
                    )
                    denied_set.add((src_dir, dst_dir))
                bar.update()
    if len(denied_set) > 0:
        print(
            style(
                f"E: Cannot move following directories as permission denied. Please move manually.",
                OutputLevel.ERROR,
            )
        )
        print("\n".join([f"{s}->{d}" for s, d in denied_set]))


if __name__ == "__main__":
    concat()
