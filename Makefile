.PHONY: lambda-demo

lambda-demo:
	@python - <<'PY'
from pathlib import Path
import shutil
src = Path(".env.example")
dst = Path(".env")
if src.exists() and not dst.exists():
    shutil.copy(src, dst)
PY
	@python -m examples.lambda_main
