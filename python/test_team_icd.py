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


if __name__=="__main__":
    unittest.main(verbosity=2)
