# Team ICD 1.0 — console MVP shared schema

Source: [team ICD v0.21, page version 33](https://ligproject2team.atlassian.net/wiki/spaces/MFS/pages/360475/03+ICD)
and [processing rules, page version 7](https://ligproject2team.atlassian.net/wiki/spaces/MFS/pages/29917185/ICD).

`proto/mfs/icd/v1/mfs.proto` defines the device-network subset needed by the
fixed-OBS console MVP. This is the shared field-number definition for that subset; existing
`mfs/icd/v3/mfs.proto` remains a different, incompatible legacy protocol.
Consumers must pin the shared commit used by C2. Publishing this schema does not
mean that device firmware or the complete ICD has been implemented or validated.

Envelope version is 1.0. IDs are strings/UUIDs; connection sessions are C2-issued.
Logical uppercase message names map to snake_case Envelope bodies and PascalCase
message types. ICD common result fields are nested in `outcome: Result`.
Enum symbols follow the repository lint convention, for example ICD COMPLETED
maps to `REQUEST_RESULT_COMPLETED` and POINT to `PointingCommand.OPERATION_POINT`.
Installation's rotation is a row-major device-to-project 3×3 matrix.
Optional scalar presence is preserved; unmeasured angles/invalid XYZ are absent.
Messages do not encode C2's local confirmation state as device completion.

The schema includes registration, capabilities, installation, measurement,
organized raw cloud, frame pose, control sessions, pointing/result/status, and
OBS mode/motion messages. GUI/IPC, persistence, emergency-latch release, and the
full OBS follow-mode state contract are outside this MVP subset. Unknown bodies
must be rejected, not interpreted through legacy tags. Reserved field 100
prevents reuse of the removed private C2 raw envelope extension.

Generate Python bindings from this repository root:

```sh
python -m pip install grpcio-tools==1.76.0 protobuf==6.33.5
python -m grpc_tools.protoc -I proto --python_out=python proto/mfs/icd/v1/mfs.proto
```

The committed generated file is `python/mfs/icd/v1/mfs_pb2.py`. Consumers use it
directly or generate their language bindings from this exact schema; they must
not maintain another handwritten codec or independently select enum/tag values.
The Python runtime requirement is protobuf 6.33.5. The existing C++ library
continues to represent legacy v3 only.

Before updating a C2 submodule reference in a published branch, publish a commit
containing the new schema and generated module here, then reference that exact
commit from C2. Copying the C2 parent commit alone does not include uncommitted
submodule files.
