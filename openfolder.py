import sqlite3
from pathlib import Path

import click


def validate_func(n):
    def f(x):
        try:
            v = int(x)
            if 0 <= v < n:
                return v
        except ValueError:
            pass

        raise click.UsageError(f"invalid value.")

    return f


@click.command()
@click.argument("folder_path")
def find_open_folder(folder_path):
    body_path = Path(folder_path).resolve()
    click.echo("Ctrl+C to abort")
    while True:
        try:
            name = click.prompt("enter bms song title to open folder")
        except click.Abort:
            break

        with sqlite3.connect(body_path / "songdata.db") as con:
            res = con.execute(
                "select `title`, `path` from `song` where `title` like ?;",
                (name + "%",),
            )
            rows = res.fetchall()

        candidate = {}
        for t, p in rows:
            path = Path(p).resolve()
            folder = path.parent
            if folder not in candidate:
                candidate[folder] = []
            candidate[folder].append(t)

        if (cand_len := len(candidate)) == 0:
            click.secho("matching song not found", fg="yellow")
            continue

        lines = ""
        for i, (p, titles) in enumerate(candidate.items()):
            repr = titles[0]

            lines += (
                f"[{i:>2}] {repr}"
                + (f" and {n - 1} other chart" if (n := len(titles)) > 1 else "")
                + ("s" if n > 2 else "")
                + f" -> {p}\n"
            )

        # is it possible to encode cp932 via pager?
        click.echo(lines)

        index = 0
        pathlist = list(candidate.keys())
        if cand_len > 1:
            try:
                index = click.prompt(
                    "choose song to open (ctrl+c to cancel)",
                    default=0,
                    show_default=False,
                    value_proc=validate_func(cand_len),
                )
            except click.Abort:
                continue
        else:
            if not click.confirm(f"open folder {pathlist[index]}?", default=True):
                continue

        click.launch(str(pathlist[index]))


if __name__ == "__main__":
    find_open_folder()
