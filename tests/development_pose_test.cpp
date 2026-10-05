#include <gtest/gtest.h>
#include "c2/protobuf_codec.hpp"
#include "c2/protocol_validation.hpp"
#include <limits>

namespace {
c2::DevelopmentPoseCommand command() {
    return {{c2::protocol_version, 1, 10, c2::ComponentId::command_and_control,
        c2::ComponentId::effector_asset, 42, 7}, 3,
        c2::CoordinateFrame::project_frame, -10, 20, 1.5F, 90, 100};
}
}
TEST(DevelopmentPoseContractTest, RoundTripsBothRolesAndPreservesWireKind) {
    for (const auto role : {c2::ComponentId::observation_asset, c2::ComponentId::effector_asset}) {
        auto input = command(); input.header.destination_id = role;
        ASSERT_TRUE(c2::validate(input).valid());
        const auto packet = c2::protobuf::encode(c2::Envelope{input});
        const auto result = c2::protobuf::decode(packet);
        ASSERT_TRUE(std::holds_alternative<c2::Envelope>(result));
        const auto& envelope = std::get<c2::Envelope>(result);
        ASSERT_TRUE(std::holds_alternative<c2::DevelopmentPoseCommand>(envelope.payload));
        const auto& output = std::get<c2::DevelopmentPoseCommand>(envelope.payload);
        EXPECT_EQ(c2::message_kind(envelope), c2::MessageKind::development_pose_command);
        EXPECT_EQ(static_cast<unsigned>(c2::message_kind(envelope)), 14);
        EXPECT_EQ(output.header.asset_id, 42); EXPECT_EQ(output.header.session_id, 7);
        EXPECT_EQ(output.command_id, 3); EXPECT_EQ(output.valid_until_us, 100);
        EXPECT_FLOAT_EQ(output.x_m, -10); EXPECT_FLOAT_EQ(output.azimuth_deg, 90);
        EXPECT_EQ(c2::protobuf::encode(envelope), packet);
    }
}
TEST(DevelopmentPoseContractTest, RejectsInvalidPoseAndCommandIdentity) {
    auto input = command(); input.x_m = std::numeric_limits<float>::quiet_NaN();
    EXPECT_FALSE(c2::validate(input).valid());
    input = command(); input.azimuth_deg = 360; EXPECT_FALSE(c2::validate(input).valid());
    input = command(); input.command_id = 0; EXPECT_FALSE(c2::validate(input).valid());
    input = command(); input.valid_until_us = 10; EXPECT_FALSE(c2::validate(input).valid());
    input = command(); input.header.destination_id = c2::ComponentId::command_and_control;
    EXPECT_FALSE(c2::validate(input).valid());
}
