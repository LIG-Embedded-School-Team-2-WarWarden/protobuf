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

## Optional EFF laser control extension (schema only)

This local extension adds low-power demonstration laser ON/OFF control to ICD
1.0. It is an additive proposal, not evidence of team approval or device support.
It does not implement C2 CLI/sending, EFF GPIO/UART output control, or physical
output feedback. Existing field numbers and envelope version remain unchanged.
Do not send these bodies until EFF advertises both CAPABILITY_LASER_CONTROL
and CapabilityReport.laser_control_supported=true. Older consumers reject
unknown bodies. Publish the shared protocol commit and pin both consumers
before integration.

### Messages and fields

All messages use the existing Envelope, connection session, and Result types.
Envelope body tags are laser_command=32, laser_result=33, laser_status=34.
Capability enum value 7 and CapabilityReport field 19 advertise support.

| Direction / body | Fields (number: type) |
|---|---|
| C2 -> EFF / LaserCommand | request_id (1: string), control_session_id (2: string), control_epoch (3: uint64), command_sequence (4: uint64), operation (5: Operation), issued_at (6: string), expires_at (7: optional string), duration_ms (8: optional uint32), effector_installation_revision (9: uint32) |
| EFF -> C2 / LaserResult | outcome (1: Result), control_session_id (2: string), control_epoch (3: uint64), command_sequence (4: uint64), actual_laser_state (5: LaserState), state_observed_at (6: optional string) |
| EFF -> C2 / LaserStatus | device_id (1: string), control_session_id (2: optional string), control_epoch (3: uint64), last_accepted_sequence (4: uint64), active_request_id (5: optional string), laser_state (6: LaserState), reported_at (7: string), state_observed_at (8: optional string), remaining_duration_ms (9: optional uint32), fault_code (10: optional ReasonCode) |

Operation: UNSPECIFIED=0, ON=1, OFF=2, GET_STATUS=3.
LaserState: UNSPECIFIED=0, OFF=1, ON=2, UNKNOWN=3.
Timestamps follow the existing ICD UTC timestamp convention.

### EFF implementation contract

- This contract is EFF-only. OBS rejects these commands as UNSUPPORTED_TYPE.
  A device without laser support must not advertise the capability.
- Validate the existing connection/control session, control epoch, installation
  revision, request identity, and sequence before applying a command.
  Laser command sequences are independent of pointing command sequences.
  They increase within a control epoch and reset on a new control epoch.
  A duplicate identical request returns its cached result without re-enabling
  output or extending its timer. Conflicting reuse is ID_CONFLICT; an older
  sequence is STALE_COMMAND.
- ON requires a valid future expires_at and positive duration_ms. Missing or
  zero duration is INVALID_ARGUMENT, expired requests are EXPIRED_COMMAND,
  and a duration exceeding the device's supported limit is OUT_OF_RANGE.
  The device must reject ON if its clock cannot validate expiry (CLOCK_UNTRUSTED),
  an emergency stop is latched (ESTOP_LATCHED), or its control gate is closed
  (BUSY). The duration is a device-local monotonic timer starting when output
  becomes enabled; expires_at only limits command acceptance.
- OFF and GET_STATUS omit duration_ms. expires_at is optional for these
  operations. OFF remains allowed while output is already off, while an
  emergency stop is latched, or while the control gate is closed. Session,
  identity and sequence validation still apply.
- A fresh ON while already ON is rejected as BUSY; it does not extend the
  existing output window. OFF explicitly disables output. GET_STATUS does
  not change output and returns LaserStatus as well as LaserResult.
- ACCEPTED acknowledges receipt only. COMPLETED means the requested state
  transition has been verified (ON means enabled, not that duration elapsed).
  GET_STATUS completion means the query was handled, and may report UNKNOWN.
  If output cannot be observed, report UNKNOWN and omit state_observed_at;
  never infer physical OFF or ON from a sent driver command. An unverified
  ON/OFF must not be reported as COMPLETED.
- Publish LaserStatus on output changes and in response to GET_STATUS.
  active_request_id identifies the active ON request; clear it when OFF.
  Report remaining_duration_ms only while output is ON and the timer is known.
  Automatic timer expiry reports OFF through LaserStatus; it does not change
  an already terminal ON result.
- The device must disable output on duration expiry, control/connection
  session loss or replacement, emergency stop, and device fault; start OFF
  after boot. Existing pointing STOP/DRAIN must also disable laser output.
  Do not claim OFF until verified; report UNKNOWN/fault if verification fails.
  These are implementation requirements for the EFF owner, not functionality
  supplied by this schema change.

C2 integration must wait for the matching result/status before displaying a
verified output state. No power/intensity adjustment is defined by this extension.
