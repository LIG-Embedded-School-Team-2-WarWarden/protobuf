import unittest
from mfs.icd.v1 import mfs_pb2 as pb


class TeamWireContract(unittest.TestCase):
    def test_optional_zero_is_distinct_from_unreported(self):
        missing = pb.Point(sdk_depth_raw=964000,xyz_valid=False)
        valid = pb.Point(sdk_depth_raw=1500,xyz_valid=True,x=0,y=0,z=1.5)
        c = pb.PointCloudChunk(points=[missing,valid],width=2,height=1,total_points=2)
        decoded = pb.PointCloudChunk.FromString(c.SerializeToString())
        self.assertFalse(decoded.points[0].HasField("x"))
        self.assertTrue(decoded.points[1].HasField("x"))
        self.assertEqual(decoded.points[0].sdk_depth_raw,964000)

    def test_64_bit_sequences_and_oneof_roundtrip(self):
        e = pb.Envelope(version_major=1,version_minor=0,
            heartbeat=pb.Heartbeat(sequence=2**63+7))
        decoded = pb.Envelope.FromString(e.SerializeToString())
        self.assertEqual(decoded.WhichOneof("body"),"heartbeat")
        self.assertEqual(decoded.heartbeat.sequence,2**63+7)
        decoded.pointing_command.CopyFrom(pb.PointingCommand(
            operation=pb.PointingCommand.OPERATION_STOP,command_sequence=2**40))
        self.assertFalse(decoded.HasField("heartbeat"))
        self.assertFalse(decoded.pointing_command.HasField("pan_deg"))

    def test_removed_private_field_is_not_a_body(self):
        e = pb.Envelope.FromString(bytes([0xA2,0x06,0x00]))
        self.assertIsNone(e.WhichOneof("body"))
        self.assertNotIn(100,pb.Envelope.DESCRIPTOR.fields_by_number)



    def test_laser_command_roundtrip_and_optional_duration(self):
        command = pb.LaserCommand(
            request_id="laser-on", control_session_id="control",
            control_epoch=2**40, command_sequence=2**48,
            operation=pb.LaserCommand.OPERATION_ON,
            issued_at="2026-10-22T00:00:00Z",
            expires_at="2026-10-22T00:00:01Z",
            duration_ms=500, effector_installation_revision=3)
        envelope = pb.Envelope(version_major=1, laser_command=command)
        decoded = pb.Envelope.FromString(envelope.SerializeToString())
        self.assertEqual(decoded.WhichOneof("body"), "laser_command")
        self.assertEqual(decoded.laser_command, command)
        off = pb.LaserCommand(operation=pb.LaserCommand.OPERATION_OFF)
        self.assertFalse(off.HasField("duration_ms"))
        off.duration_ms = 0
        self.assertTrue(off.HasField("duration_ms"))

    def test_laser_feedback_does_not_imply_measured_state(self):
        result = pb.LaserResult(
            outcome=pb.Result(request_id="laser-on",
                              result=pb.REQUEST_RESULT_ACCEPTED),
            actual_laser_state=pb.LASER_STATE_UNKNOWN)
        envelope = pb.Envelope(laser_result=result)
        decoded = pb.Envelope.FromString(envelope.SerializeToString())
        self.assertEqual(decoded.laser_result, result)
        self.assertFalse(decoded.laser_result.HasField("state_observed_at"))
        status = pb.LaserStatus(
            device_id="EFF", laser_state=pb.LASER_STATE_OFF,
            reported_at="2026-10-22T00:00:01Z",
            state_observed_at="2026-10-22T00:00:01Z")
        envelope.laser_status.CopyFrom(status)
        decoded = pb.Envelope.FromString(envelope.SerializeToString())
        self.assertEqual(decoded.laser_status, status)
        self.assertFalse(decoded.HasField("laser_result"))
        self.assertFalse(decoded.laser_status.HasField("active_request_id"))
        self.assertFalse(decoded.laser_status.HasField("remaining_duration_ms"))

    def test_laser_extension_tags_and_unsupported_default(self):
        fields = pb.Envelope.DESCRIPTOR.fields_by_name
        for name, number in {
            "pointing_command": 25, "obs_motion_result": 31,
            "laser_command": 32, "laser_result": 33, "laser_status": 34
        }.items():
            self.assertEqual(fields[name].number, number)
        self.assertEqual(pb.CAPABILITY_LASER_CONTROL, 7)
        self.assertEqual(
            pb.CapabilityReport.DESCRIPTOR.fields_by_name[
                "laser_control_supported"].number, 19)
        self.assertFalse(pb.CapabilityReport().laser_control_supported)


if __name__=="__main__":
    unittest.main(verbosity=2)
