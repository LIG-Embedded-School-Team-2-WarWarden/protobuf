"""Fail when checked-in bindings differ from the shared schema/toolchain."""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="team-proto-") as temporary:
    subprocess.run([sys.executable,"-m","grpc_tools.protoc","-I",str(root/"proto"),
        "--python_out="+temporary,str(root/"proto/mfs/icd/v1/mfs.proto")],check=True)
    relative = Path("mfs/icd/v1/mfs_pb2.py")
    if (Path(temporary)/relative).read_bytes() != (root/"python"/relative).read_bytes():
        raise SystemExit("Generated bindings are stale; regenerate using TEAM_ICD.md.")
print("Shared ICD 1.0 generated bindings match the schema.")
