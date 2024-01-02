# bms_fix_duplicate

for beatoraja.
fixes duplicated bms files/folders by merging them.

### requirements

- Python 3.10
  - click 8.1.7
  - colorama 0.4.6
  - tqdm 4.66.1

install dependencies by
```
$ pip install -r requirements.txt
```

### Usage

provide folder path which contains beatoraja body (`beatoraja.jar`).

```
$ python fix_duplicate.py path/to/folder
```
#### Options
- `-d`, `--dry-run` do not perform operation actually
- `-q`, `--quiet` suppress info/warn output (default)
- `-v`, `--verbose` show all output
- `--help` display help


### Notice
- It often happens that this tool cannot perform operation for some folders due to `PermissionDenied` error. You need to handle such folders manually.
- As this tool copy/overwrite all files in tree, it will take much time to complete all tasks (especially on HDD).