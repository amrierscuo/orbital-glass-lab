"""Create the 20-second cinematic sequence for L_GlassOrbit.

Run inside Unreal Editor after ``build_glass_orbit.py``. The generated sequence
animates the hero cube, the sun, the LED lane and the three cinematic cameras.
"""

import math
import unreal


SEQUENCE_PATH = "/Game/OrbitalGlassLab/Cinematics/LS_GlassOrbit"
FPS = 30
END_FRAME = FPS * 20

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def log(message):
    unreal.log(f"[OrbitalGlassSequence] {message}")


def warn(message):
    unreal.log_warning(f"[OrbitalGlassSequence] {message}")


def find_actor(label):
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    raise RuntimeError(f"Actor not found: {label}")


def add_key(channel, frame, value, linear=True):
    key = channel.add_key(unreal.FrameNumber(int(frame)), float(value))
    if linear:
        try:
            key.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)
        except Exception:
            pass
    return key


def add_transform_track(sequence, actor, samples):
    """Add transform samples as (frame, location, rotation, scale)."""
    binding = sequence.add_possessable(actor)
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    section.set_range(0, END_FRAME)
    # UE 5.8 exposes Sequencer scripting channels through the extension
    # library rather than directly on MovieScene3DTransformSection.
    channels = unreal.MovieSceneSectionExtensions.get_all_channels(section)
    if len(channels) < 9:
        raise RuntimeError(f"Unexpected transform channel count: {len(channels)}")

    for frame, location, rotation, scale in samples:
        values = (
            location.x, location.y, location.z,
            rotation.roll, rotation.pitch, rotation.yaw,
            scale.x, scale.y, scale.z,
        )
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


def unwrap_camera_rotations(samples):
    """Keep Euler channels continuous when a look-at yaw crosses +/-180."""
    result = []
    previous = None
    for frame, location, rotation, scale in samples:
        values = [rotation.roll, rotation.pitch, rotation.yaw]
        if previous is not None:
            for index in range(3):
                while values[index] - previous[index] > 180.0:
                    values[index] -= 360.0
                while values[index] - previous[index] < -180.0:
                    values[index] += 360.0
        adjusted = unreal.Rotator(
            roll=values[0], pitch=values[1], yaw=values[2])
        result.append((frame, location, adjusted, scale))
        previous = values
    return result


def make_sequence():
    if unreal.EditorAssetLibrary.does_asset_exist(SEQUENCE_PATH):
        log("Removing the previously generated sequence")
        unreal.EditorAssetLibrary.delete_asset(SEQUENCE_PATH)

    sequence = asset_tools.create_asset(
        "LS_GlassOrbit",
        "/Game/OrbitalGlassLab/Cinematics",
        unreal.LevelSequence,
        unreal.LevelSequenceFactoryNew(),
    )
    if not sequence:
        raise RuntimeError("Unable to create LS_GlassOrbit")
    sequence.set_display_rate(unreal.FrameRate(FPS, 1))
    sequence.set_tick_resolution_directly(unreal.FrameRate(24000, 1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(END_FRAME)
    return sequence


def animate_hero(sequence):
    hero = find_actor("OG_HeroGlassCube")
    core = find_actor("OG_HeroReflectiveCore")
    samples = []
    for second in range(21):
        alpha = second / 20.0
        angle = alpha * math.tau
        location = unreal.Vector(
            800.0 * math.cos(angle),
            800.0 * math.sin(angle),
            1000.0 + 90.0 * math.sin(angle * 2.0),
        )
        rotation = unreal.Rotator(
            18.0 + 360.0 * alpha,
            32.0 + 720.0 * alpha,
            11.0 + 240.0 * alpha,
        )
        samples.append((second * FPS, location, rotation,
                        unreal.Vector(2.8, 2.8, 2.8)))
    hero_binding = add_transform_track(sequence, hero, samples)
    add_transform_track(sequence, core, samples)
    return hero_binding


def animate_sun(sequence):
    sun = find_actor("OG_Sun")
    scale = unreal.Vector(1.0, 1.0, 1.0)
    location = unreal.Vector(0.0, 0.0, 3500.0)
    samples = [
        (0, location, unreal.Rotator(-8.0, -70.0, 0.0), scale),
        (5 * FPS, location, unreal.Rotator(-55.0, -25.0, 0.0), scale),
        (10 * FPS, location, unreal.Rotator(-5.0, 35.0, 0.0), scale),
        (13 * FPS, location, unreal.Rotator(28.0, 75.0, 0.0), scale),
        (17 * FPS, location, unreal.Rotator(32.0, 105.0, 0.0), scale),
        (20 * FPS, location, unreal.Rotator(-20.0, 135.0, 0.0), scale),
    ]
    return add_transform_track(sequence, sun, samples)


def animate_leds(sequence):
    samples = [
        (0, 0.0),
        (9 * FPS, 0.0),
        (11 * FPS, 350.0),
        (17 * FPS, 350.0),
        (19 * FPS, 0.0),
        (END_FRAME, 0.0),
    ]
    count = 0
    for index in range(1, 6):
        light_actor = find_actor(f"OG_LEDLight_{index:02d}")
        component = light_actor.get_component_by_class(unreal.PointLightComponent)
        if component:
            add_float_property(sequence, component, "Intensity", samples)
            count += 1
    log(f"Animated {count} LED lights")


def camera_samples(start_frame, end_frame, radius, height, angle_a, angle_b,
                   target, scale=None):
    scale = scale or unreal.Vector(1.0, 1.0, 1.0)
    samples = []
    steps = max(2, int((end_frame - start_frame) / FPS) + 1)
    for step in range(steps):
        alpha = step / (steps - 1)
        frame = round(start_frame + (end_frame - start_frame) * alpha)
        angle = math.radians(angle_a + (angle_b - angle_a) * alpha)
        location = unreal.Vector(
            radius * math.cos(angle),
            radius * math.sin(angle),
            height + 120.0 * math.sin(alpha * math.pi),
        )
        rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
        samples.append((frame, location, rotation, scale))
    return samples


def hero_location_at(frame):
    alpha = frame / float(END_FRAME)
    angle = alpha * math.tau
    return unreal.Vector(
        800.0 * math.cos(angle),
        800.0 * math.sin(angle),
        1000.0 + 90.0 * math.sin(angle * 2.0),
    )


def wide_camera_samples(start_frame, end_frame):
    samples = []
    steps = max(2, int((end_frame - start_frame) / FPS) + 1)
    for step in range(steps):
        alpha = step / (steps - 1)
        frame = round(start_frame + (end_frame - start_frame) * alpha)
        hero = hero_location_at(frame)
        # Aim between the orbital pivot and the moving hero so both remain in
        # the composition while the camera performs its own broad arc.
        target = unreal.Vector(hero.x * 0.58, hero.y * 0.58, 880.0)
        angle = math.radians(-50.0 + 78.0 * alpha)
        location = unreal.Vector(
            2900.0 * math.cos(angle), 2900.0 * math.sin(angle),
            1450.0 + 180.0 * math.sin(alpha * math.pi))
        rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
        samples.append((frame, location, rotation, unreal.Vector(1.0, 1.0, 1.0)))
    return samples


def close_camera_samples(start_frame, end_frame):
    samples = []
    steps = max(2, int((end_frame - start_frame) / FPS) + 1)
    for step in range(steps):
        alpha = step / (steps - 1)
        frame = round(start_frame + (end_frame - start_frame) * alpha)
        hero = hero_location_at(frame)
        hero_angle = math.atan2(hero.y, hero.x)
        camera_angle = hero_angle - math.radians(58.0 - 26.0 * alpha)
        location = hero + unreal.Vector(
            1800.0 * math.cos(camera_angle),
            1800.0 * math.sin(camera_angle),
            560.0 + 100.0 * math.sin(alpha * math.pi),
        )
        target = hero + unreal.Vector(0.0, 0.0, -35.0)
        rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
        samples.append((frame, location, rotation, unreal.Vector(1.0, 1.0, 1.0)))
    return samples


def led_camera_samples(start_frame, end_frame):
    target = unreal.Vector(0.0, -420.0, 175.0)
    return camera_samples(
        start_frame, end_frame, 1450.0, 470.0, -118.0, -42.0, target)


def add_camera_cut_track(sequence, cuts):
    try:
        track = sequence.add_track(unreal.MovieSceneCameraCutTrack)
    except Exception:
        track = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)

    for start_frame, end_frame, binding in cuts:
        section = track.add_section()
        section.set_range(start_frame, end_frame)
        try:
            section.set_camera_binding_id(binding.get_id())
        except Exception:
            binding_id = unreal.MovieSceneObjectBindingID()
            binding_id.set_editor_property("guid", binding.get_id())
            section.set_camera_binding_id(binding_id)


def animate_cameras(sequence):
    specs = [
        ("OG_Camera_OrbitWide", 0, 9 * FPS, wide_camera_samples),
        ("OG_Camera_GlassClose", 9 * FPS, 16 * FPS, close_camera_samples),
        ("OG_Camera_LEDLow", 16 * FPS, END_FRAME, led_camera_samples),
    ]
    cuts = []
    for label, start, end, sample_builder in specs:
        camera = find_actor(label)
        samples = unwrap_camera_rotations(sample_builder(start, end))
        binding = add_transform_track(sequence, camera, samples)
        cuts.append((start, end, binding))
    add_camera_cut_track(sequence, cuts)


def add_sequence_actor(sequence):
    for actor in list(actors.get_all_level_actors()):
        if actor.get_actor_label() == "OG_LS_GlassOrbit":
            actors.destroy_actor(actor)
    sequence_actor = actors.spawn_actor_from_class(
        unreal.LevelSequenceActor, unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    sequence_actor.set_actor_label("OG_LS_GlassOrbit")
    try:
        sequence_actor.set_sequence(sequence)
    except Exception:
        sequence_actor.set_editor_property(
            "level_sequence", unreal.SoftObjectPath(SEQUENCE_PATH + ".LS_GlassOrbit"))
    return sequence_actor


def build():
    log("Sequence build started")
    sequence = make_sequence()
    animate_hero(sequence)
    animate_sun(sequence)
    animate_leds(sequence)
    animate_cameras(sequence)
    add_sequence_actor(sequence)
    unreal.EditorAssetLibrary.save_asset(SEQUENCE_PATH, only_if_is_dirty=False)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    log("Sequence build complete: 600 frames at 30 fps")


try:
    build()
except Exception as exc:
    unreal.log_error(f"[OrbitalGlassSequence] Build failed: {exc}")
    raise
