import os
import sys
import subprocess
import re
from datetime import datetime
from sqlalchemy import create_engine, text
from configparser import ConfigParser

ALEMBIC_INI = 'alembic.ini'
VERSIONS_DIR = 'alembic/versions'
HISTORY_TABLE = 'migration'

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_db_url():
    config = ConfigParser()
    config.read(ALEMBIC_INI)
    try:
        url = config.get('alembic', 'sqlalchemy.url')
        if not url: raise ValueError
        return url
    except:
        try:
            from settings import db_url
            return db_url
        except ImportError:
            print(f"{RED}Error: DB URL not found.{RESET}")
            sys.exit(1)

def get_engine():
    return create_engine(get_db_url())

def init_history_table(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS public.{HISTORY_TABLE} (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

def get_applied_list(engine):
    init_history_table(engine)
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT filename FROM public.{HISTORY_TABLE}"))
        return {row[0] for row in res}

def get_revision_id(filename):
    path = os.path.join(VERSIONS_DIR, filename)
    if not os.path.exists(path): return None
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r"revision\s*[:=]\s*(?:str\s*=\s*)?['\"]([a-f0-9]+)['\"]", content)
    return match.group(1) if match else None

def run_command_verbose(cmd_list):
    """Запускает команду и выводит ошибки сразу"""
    process = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        return False, stdout + stderr
    return True, stdout

def run_upgrade():
    engine = get_engine()
    files = sorted([f for f in os.listdir(VERSIONS_DIR) if f.endswith('.py')])
    applied = get_applied_list(engine)
    to_apply = [f for f in files if f not in applied]

    if not to_apply:
        print(f"{GREEN}Всё актуально.{RESET}")
        return

    print(f"Будет применено миграций: {len(to_apply)}")

    for fname in to_apply:
        rev_id = get_revision_id(fname)
        if not rev_id:
            print(f"{YELLOW}Skipping {fname} (no ID){RESET}")
            continue

        print(f"--> UPGRADE: {fname} (ID: {rev_id}) ... ", end='', flush=True)

        ok, log = run_command_verbose(["alembic", "stamp", "base"])
        if not ok:
            print(f"{RED}FAIL (Stamp){RESET}\n{log}")
            sys.exit(1)

        ok, log = run_command_verbose(["alembic", "upgrade", rev_id])
        if not ok:
            print(f"{RED}FAIL (Upgrade){RESET}\n{log}")
            sys.exit(1)

        with engine.begin() as conn:
            conn.execute(
                text(f"INSERT INTO public.{HISTORY_TABLE} (filename) VALUES (:fn)"),
                {"fn": fname}
            )
        print(f"{GREEN}OK{RESET}")

def run_downgrade():
    engine = get_engine()
    applied = sorted(list(get_applied_list(engine)))

    if not applied:
        print(f"{YELLOW}Нечего откатывать.{RESET}")
        return

    last_file = applied[-1]
    rev_id = get_revision_id(last_file)

    if not rev_id:
        print(f"{RED}Не найден ID для {last_file}{RESET}")
        sys.exit(1)

    print(f"--> DOWNGRADE: {last_file} (ID: {rev_id}) ... ", end='', flush=True)

    ok, log = run_command_verbose(["alembic", "stamp", rev_id])
    if not ok:
        print(f"{RED}FAIL (Stamp){RESET}\n{log}")
        sys.exit(1)

    ok, log = run_command_verbose(["alembic", "downgrade", "base"])

    if not ok:
        print(f"{RED}FAIL (Downgrade){RESET}\n{log}")
        sys.exit(1)

    with engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM public.{HISTORY_TABLE} WHERE filename = :fn"),
            {"fn": last_file}
        )
    print(f"{GREEN}OK{RESET}")

def run_create(msg):
    if not msg:
        print("Нужно сообщение")
        return
    cmd = ["alembic", "revision", "--head=base", "-m", msg]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        match = re.search(r"Generating (.*?\.py)", res.stdout)
        if match:
            old_p = match.group(1)
            if not os.path.isabs(old_p): old_p = os.path.abspath(old_p)
            ts = datetime.now().strftime('%Y_%m_%d_%H%M%S')
            new_name = f"{ts}_{os.path.basename(old_p)}"
            os.rename(old_p, os.path.join(os.path.dirname(old_p), new_name))
            print(f"{GREEN}Created: {new_name}{RESET}")
    else:
        print(res.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db.py [upgrade | downgrade | create 'msg']")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'upgrade': run_upgrade()
    elif cmd == 'downgrade': run_downgrade()
    elif cmd == 'create': run_create(sys.argv[2] if len(sys.argv)>2 else "msg")
    else: print("Unknown command")