list:
    just --list

run arg1="" arg2=""  arg3 = "":
    uv run src/members_files/main.py {{arg1}} {{arg2}} {{arg3}}

test:
    uv run -m pytest
