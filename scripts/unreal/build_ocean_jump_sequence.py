"""Create the 15-second Ocean Jump cinematic sequence."""

import math
import unreal


SEQUENCE_PATH = "/Game/OrbitalGlassLab/Cinematics/LS_OceanJump"
FPS = 30
END_FRAME = FPS * 15

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def log(message):
    unreal.log(f"[OceanJumpSequence] {message}")


def find(label):
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    raise RuntimeError(f"Missing actor: {label}")


def add_key(channel, frame, value):
    key = channel.add_key(unreal.FrameNumber(int(frame)), float(value))
    try:
        key.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)
    except Exception:
        pass


def add_transform(sequence, actor, samples):
    binding = sequence.add_possessable(actor)
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    section.set_range(0, END_FRAME)
    channels = unreal.MovieSceneSectionExtensions.get_all_channels(section)
    for frame, location, rotation, scale in samples:
        values = (location.x, location.y, location.z,
                  rotation.roll, rotation.pitch, rotation.yaw,
                  scale.x, scale.y, scale.z)
        for channel, value in zip(channels[:9], values):
            add_key(channel, frame, value)
    return binding


def add_float_property(sequence, obj, property_name, samples):
    binding = sequence.add_possessable(obj)
    track = binding.add_track(unreal.MovieSceneFloatTrack)
    track.set_property_name_and_path(property_name, property_name)
    section = track.add_section()
    section.set_range(0, END_FRAME)
    channel = unreal.MovieSceneSectionExtensions.get_all_channels(section)[0]
    for frame, value in samples:
        add_key(channel, frame, value)
    return binding


def make_sequence():
    if unreal.EditorAssetLibrary.does_asset_exist(SEQUENCE_PATH):
        unreal.EditorAssetLibrary.delete_asset(SEQUENCE_PATH)
    sequence = asset_tools.create_asset(
        "LS_OceanJump", "/Game/OrbitalGlassLab/Cinematics",
        unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    if not sequence:
        raise RuntimeError("Could not create LS_OceanJump")
    sequence.set_display_rate(unreal.FrameRate(FPS, 1))
    sequence.set_tick_resolution_directly(unreal.FrameRate(24000, 1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(END_FRAME)
    return sequence


def player_position(frame):
    time = frame / float(FPS)
    z = 690.0
    if time <= 4.0:
        alpha = time / 4.0
        return unreal.Vector(-680.0 + 190.0 * alpha, 0.0, z)
    if time <= 6.0:
        alpha = (time - 4.0) / 2.0
        return unreal.Vector(-490.0 + 15.0 * alpha, 0.0, z)
    if time <= 10.0:
        alpha = (time - 6.0) / 4.0
        return unreal.Vector(-475.0 + 950.0 * alpha, 0.0,
                             z + 500.0 * math.sin(math.pi * alpha))
    alpha = min(1.0, (time - 10.0) / 5.0)
    return unreal.Vector(475.0 + 250.0 * alpha, 0.0, z)


def animate_platforms(sequence):
    scale = unreal.Vector(5.5, 6.5, 1.0)
    samples_a = []
    samples_b = []
    for second in range(16):
        frame = second * FPS
        roll = 10.0 * math.sin(second * math.pi / 3.5)
        samples_a.append((frame, unreal.Vector(-750.0, 0.0, 500.0),
                          unreal.Rotator(roll=roll, pitch=0.0, yaw=0.0), scale))
        samples_b.append((frame, unreal.Vector(750.0, 0.0, 500.0),
                          unreal.Rotator(roll=-roll, pitch=0.0, yaw=0.0), scale))
    add_transform(sequence, find("OJ_PlatformA"), samples_a)
    add_transform(sequence, find("OJ_PlatformB"), samples_b)


def pose_rotation(label, jump_alpha):
    if "ArmL" in label:
        return unreal.Rotator(roll=-18.0, pitch=-75.0 * jump_alpha, yaw=-12.0)
    if "ArmR" in label:
        return unreal.Rotator(roll=18.0, pitch=75.0 * jump_alpha, yaw=12.0)
    if "LegL" in label:
        return unreal.Rotator(roll=6.0, pitch=42.0 * jump_alpha, yaw=-3.0)
    if "LegR" in label:
        return unreal.Rotator(roll=-6.0, pitch=-38.0 * jump_alpha, yaw=3.0)
    return unreal.Rotator(0.0, 0.0, 0.0)


def animate_player(sequence):
    labels = [
        "OJ_Player_Pelvis", "OJ_Player_Torso", "OJ_Player_Head",
        "OJ_Player_ArmL", "OJ_Player_ArmR", "OJ_Player_LegL",
        "OJ_Player_LegR", "OJ_Player_FootL", "OJ_Player_FootR",
    ]
    origin = unreal.Vector(-680.0, 0.0, 690.0)
    sample_frames = [0, 60, 120, 180, 210, 240, 270, 300, 360, 450]
    for label in labels:
        actor = find(label)
        offset = actor.get_actor_location() - origin
        scale = actor.get_actor_scale3d()
        samples = []
        for frame in sample_frames:
            position = player_position(frame) + offset
            if 180 <= frame <= 300:
                jump_alpha = math.sin(math.pi * (frame - 180) / 120.0)
            else:
                jump_alpha = 0.0
            rotation = pose_rotation(label, jump_alpha)
            samples.append((frame, position, rotation, scale))
        add_transform(sequence, actor, samples)


def animate_sun(sequence):
    location = unreal.Vector(0.0, 0.0, 4500.0)
    scale = unreal.Vector(1.0, 1.0, 1.0)
    samples = [
        (0, location, unreal.Rotator(-38.0, -75.0, 0.0), scale),
        (5 * FPS, location, unreal.Rotator(-36.0, -25.0, 0.0), scale),
        (8 * FPS, location, unreal.Rotator(-34.0, 12.0, 0.0), scale),
        (11 * FPS, location, unreal.Rotator(-32.0, 38.0, 0.0), scale),
        (END_FRAME, location, unreal.Rotator(-31.0, 64.0, 0.0), scale),
    ]
    sun = find("OJ_Sun")
    add_transform(sequence, sun, samples)
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if sun_component:
        add_float_property(sequence, sun_component, "Temperature", [
            (0, 5600.0), (5 * FPS, 4700.0), (8 * FPS, 3400.0),
            (11 * FPS, 2900.0), (END_FRAME, 2600.0),
        ])
        add_float_property(sequence, sun_component, "Intensity", [
            (0, 7.0), (5 * FPS, 6.0), (8 * FPS, 4.8),
            (11 * FPS, 4.0), (END_FRAME, 3.5),
        ])


def animate_sunset_backdrops(sequence):
    visible_location = unreal.Vector(0.0, 0.0, 800.0)
    hidden_location = unreal.Vector(0.0, 0.0, -10000.0)
    rotation = unreal.Rotator(0.0, 0.0, 0.0)
    scale = unreal.Vector(100.0, 100.0, 100.0)
    add_transform(sequence, find("OJ_SunsetDome"), [
        (0, hidden_location, rotation, scale),
        (194, hidden_location, rotation, scale),
        (195, visible_location, rotation, scale),
        (END_FRAME, visible_location, rotation, scale),
    ])


def unwrap(samples):
    result = []
    previous = None
    for frame, location, rotation, scale in samples:
        values = [rotation.roll, rotation.pitch, rotation.yaw]
        if previous:
            for index in range(3):
                while values[index] - previous[index] > 180.0:
                    values[index] -= 360.0
                while values[index] - previous[index] < -180.0:
                    values[index] += 360.0
        result.append((frame, location,
                       unreal.Rotator(roll=values[0], pitch=values[1], yaw=values[2]),
                       scale))
        previous = values
    return result


def camera_samples(start, end, mode):
    samples = []
    step = 15
    for frame in range(start, end + 1, step):
        player = player_position(frame)
        if mode == "third":
            location = player + unreal.Vector(-1000.0, -1300.0, 500.0)
            target = player + unreal.Vector(150.0, 0.0, 35.0)
        elif mode == "first":
            location = player + unreal.Vector(52.0, 0.0, 112.0)
            target = unreal.Vector(600.0, 0.0, 720.0)
        elif mode == "jump":
            location = unreal.Vector(player.x * 0.18, -1800.0, 1050.0)
            target = player + unreal.Vector(0.0, 0.0, 45.0)
        else:
            location = player + unreal.Vector(-620.0, 1000.0, 390.0)
            target = player + unreal.Vector(170.0, 0.0, 55.0)
        rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
        samples.append((frame, location, rotation, unreal.Vector(1.0, 1.0, 1.0)))
    if samples[-1][0] != end:
        player = player_position(end)
        if mode == "third":
            location = player + unreal.Vector(-1000.0, -1300.0, 500.0)
            target = player + unreal.Vector(150.0, 0.0, 35.0)
        elif mode == "first":
            location = player + unreal.Vector(52.0, 0.0, 112.0)
            target = unreal.Vector(600.0, 0.0, 720.0)
        elif mode == "jump":
            location = unreal.Vector(player.x * 0.18, -1800.0, 1050.0)
            target = player + unreal.Vector(0.0, 0.0, 45.0)
        else:
            location = player + unreal.Vector(-620.0, 1000.0, 390.0)
            target = player + unreal.Vector(170.0, 0.0, 55.0)
        samples.append((end, location,
                        unreal.MathLibrary.find_look_at_rotation(location, target),
                        unreal.Vector(1.0, 1.0, 1.0)))
    return unwrap(samples)


def add_camera_cuts(sequence, cuts):
    try:
        track = sequence.add_track(unreal.MovieSceneCameraCutTrack)
    except Exception:
        track = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)
    for start, end, binding in cuts:
        section = track.add_section()
        section.set_range(start, end)
        try:
            section.set_camera_binding_id(binding.get_id())
        except Exception:
            binding_id = unreal.MovieSceneObjectBindingID()
            binding_id.set_editor_property("guid", binding.get_id())
            section.set_camera_binding_id(binding_id)


def animate_cameras(sequence):
    cuts = []
    specs = [
        ("OJ_CameraThird", 0, 4 * FPS, "third"),
        ("OJ_CameraFirst", 4 * FPS, 13 * FPS // 2, "first"),
        ("OJ_CameraJump", 13 * FPS // 2, 25 * FPS // 2, "jump"),
        ("OJ_CameraLanding", 25 * FPS // 2, END_FRAME, "landing"),
    ]
    for label, start, end, mode in specs:
        binding = add_transform(sequence, find(label), camera_samples(start, end, mode))
        cuts.append((start, end, binding))
    add_camera_cuts(sequence, cuts)


def add_sequence_actor(sequence):
    for actor in list(actors.get_all_level_actors()):
        if actor.get_actor_label() == "OJ_LS_OceanJump":
            actors.destroy_actor(actor)
    actor = actors.spawn_actor_from_class(
        unreal.LevelSequenceActor, unreal.Vector(), unreal.Rotator())
    actor.set_actor_label("OJ_LS_OceanJump")
    try:
        actor.set_sequence(sequence)
    except Exception:
        actor.set_editor_property(
            "level_sequence", unreal.SoftObjectPath(SEQUENCE_PATH + ".LS_OceanJump"))


def build():
    sequence = make_sequence()
    animate_platforms(sequence)
    animate_player(sequence)
    animate_sun(sequence)
    animate_sunset_backdrops(sequence)
    animate_cameras(sequence)
    add_sequence_actor(sequence)
    unreal.EditorAssetLibrary.save_asset(SEQUENCE_PATH, only_if_is_dirty=False)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    log("Sequence complete: 450 frames at 30 fps")


try:
    build()
except Exception as exc:
    unreal.log_error(f"[OceanJumpSequence] Build failed: {exc}")
    raise
