"""Create the 15-second Ocean Jump cinematic sequence."""

import math
import unreal


SEQUENCE_PATH = "/Game/OrbitalGlassLab/Cinematics/LS_OceanJump"
MAP_PATH = "/Game/OrbitalGlassLab/Maps/L_OceanJump"
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
    z = 560.0
    if time <= 4.0:
        alpha = time / 4.0
        return unreal.Vector(-850.0 + 230.0 * alpha, 0.0, z)
    if time <= 5.5:
        alpha = (time - 4.0) / 1.5
        return unreal.Vector(-620.0 + 130.0 * alpha, 0.0, z)
    if time <= 10.0:
        alpha = (time - 5.5) / 4.5
        return unreal.Vector(-490.0 + 980.0 * alpha, 0.0,
                             z + 520.0 * math.sin(math.pi * alpha))
    alpha = min(1.0, (time - 10.0) / 5.0)
    return unreal.Vector(490.0 + 270.0 * alpha, 0.0, z)


def animate_platforms(sequence):
    scale = unreal.Vector(5.5, 6.5, 1.0)
    samples_a = []
    samples_b = []
    for frame in range(0, END_FRAME + 1, FPS // 2):
        second = frame / float(FPS)
        roll = 4.5 * math.sin(second * math.pi / 3.5)
        samples_a.append((frame, unreal.Vector(-750.0, 0.0, 500.0),
                          unreal.Rotator(roll=roll, pitch=0.0, yaw=0.0), scale))
        samples_b.append((frame, unreal.Vector(750.0, 0.0, 500.0),
                          unreal.Rotator(roll=-roll, pitch=0.0, yaw=0.0), scale))
    add_transform(sequence, find("OJ_PlatformA"), samples_a)
    add_transform(sequence, find("OJ_PlatformB"), samples_b)


def animate_player(sequence):
    player = find("OJ_Player")
    samples = []
    for frame in range(0, END_FRAME + 1, FPS // 2):
        samples.append((frame, player_position(frame),
                        unreal.Rotator(0.0, 0.0, 0.0),
                        unreal.Vector(1.0, 1.0, 1.0)))
    binding = add_transform(sequence, player, samples)

    animation_root = "/Game/Characters/Mannequins/Anims/Unarmed"
    clips = [
        (0, 135, f"{animation_root}/Jog/MF_Unarmed_Jog_Fwd.MF_Unarmed_Jog_Fwd"),
        (135, 165, f"{animation_root}/MM_Idle.MM_Idle"),
        (165, 225, f"{animation_root}/Jump/MM_Jump.MM_Jump"),
        (225, 300, f"{animation_root}/Jump/MM_Fall_Loop.MM_Fall_Loop"),
        (300, 345, f"{animation_root}/Jump/MM_Land.MM_Land"),
        (345, END_FRAME, f"{animation_root}/MM_Idle.MM_Idle"),
    ]
    animation_track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for start, end, path in clips:
        animation = unreal.load_asset(path)
        if not animation:
            raise RuntimeError(f"Missing mannequin animation: {path}")
        section = animation_track.add_section()
        section.set_range(start, end)
        params = section.get_editor_property("params")
        params.set_editor_property("animation", animation)


def animate_sun(sequence):
    location = unreal.Vector(0.0, 0.0, 4500.0)
    scale = unreal.Vector(1.0, 1.0, 1.0)
    samples = [
        (0, location, unreal.Rotator(roll=0.0, pitch=-32.0, yaw=-65.0), scale),
        (5 * FPS, location, unreal.Rotator(roll=0.0, pitch=-27.0, yaw=-30.0), scale),
        (8 * FPS, location, unreal.Rotator(roll=0.0, pitch=-25.0, yaw=4.0), scale),
        (11 * FPS, location, unreal.Rotator(roll=0.0, pitch=-25.0, yaw=28.0), scale),
        (END_FRAME, location, unreal.Rotator(roll=0.0, pitch=-25.0, yaw=58.0), scale),
    ]
    sun = find("OJ_Sun")
    add_transform(sequence, sun, samples)
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if sun_component:
        add_float_property(sequence, sun_component, "Temperature", [
            (0, 5800.0), (5 * FPS, 5100.0), (8 * FPS, 4100.0),
            (11 * FPS, 3300.0), (END_FRAME, 2750.0),
        ])
        add_float_property(sequence, sun_component, "Intensity", [
            (0, 7.0), (5 * FPS, 6.4), (8 * FPS, 5.5),
            (11 * FPS, 4.7), (END_FRAME, 4.0),
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
            location = player + unreal.Vector(-850.0, -1050.0, 380.0)
            target = player + unreal.Vector(170.0, 0.0, 95.0)
        elif mode == "first":
            location = player + unreal.Vector(36.0, -8.0, 165.0)
            target = unreal.Vector(650.0, 0.0, 680.0)
        elif mode == "jump":
            location = unreal.Vector(player.x * 0.22, -1500.0, 980.0)
            target = player + unreal.Vector(0.0, 0.0, 95.0)
        else:
            location = player + unreal.Vector(-520.0, 780.0, 280.0)
            target = player + unreal.Vector(170.0, 0.0, 105.0)
        rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
        samples.append((frame, location, rotation, unreal.Vector(1.0, 1.0, 1.0)))
    if samples[-1][0] != end:
        player = player_position(end)
        if mode == "third":
            location = player + unreal.Vector(-850.0, -1050.0, 380.0)
            target = player + unreal.Vector(170.0, 0.0, 95.0)
        elif mode == "first":
            location = player + unreal.Vector(36.0, -8.0, 165.0)
            target = unreal.Vector(650.0, 0.0, 680.0)
        elif mode == "jump":
            location = unreal.Vector(player.x * 0.22, -1500.0, 980.0)
            target = player + unreal.Vector(0.0, 0.0, 95.0)
        else:
            location = player + unreal.Vector(-520.0, 780.0, 280.0)
            target = player + unreal.Vector(170.0, 0.0, 105.0)
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
        ("OJ_CameraThird", 0, 9 * FPS // 2, "third"),
        ("OJ_CameraFirst", 9 * FPS // 2, 6 * FPS, "first"),
        ("OJ_CameraJump", 6 * FPS, 11 * FPS, "jump"),
        ("OJ_CameraLanding", 11 * FPS, END_FRAME, "landing"),
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
    if not unreal.get_editor_subsystem(
            unreal.LevelEditorSubsystem).load_level(MAP_PATH):
        raise RuntimeError(f"Could not load map: {MAP_PATH}")
    sequence = make_sequence()
    animate_platforms(sequence)
    animate_player(sequence)
    animate_sun(sequence)
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
