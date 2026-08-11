"""Build the first Orbital Glass Lab scene in Unreal Engine 5.8.

Run inside Unreal Editor with Tools > Execute Python Script.
The script is intentionally repeatable: it only replaces actors whose label starts
with ``OG_`` inside the generated level.
"""

import math
import unreal


MAP_PATH = "/Game/OrbitalGlassLab/Maps/L_GlassOrbit"
MATERIAL_ROOT = "/Game/OrbitalGlassLab/Materials"
GENERATED_PREFIX = "OG_"

editor_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def log(message):
    unreal.log(f"[OrbitalGlassLab] {message}")


def warn(message):
    unreal.log_warning(f"[OrbitalGlassLab] {message}")


def set_prop(obj, name, value):
    """Set an editor property while allowing minor API differences."""
    if obj is None:
        return False
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception as exc:
        warn(f"Property {obj.get_class().get_name()}.{name} skipped: {exc}")
        return False


def load_engine_mesh(name):
    mesh = unreal.load_asset(f"/Engine/BasicShapes/{name}.{name}")
    if not mesh:
        raise RuntimeError(f"Engine mesh not found: {name}")
    return mesh


def create_material(asset_name, base_color, roughness, metallic=0.0,
                    emissive=None, opacity=None, refraction=None):
    """Create a small, editable PBR material asset if it does not exist."""
    asset_path = f"{MATERIAL_ROOT}/{asset_name}"
    existing = unreal.load_asset(asset_path)
    if existing:
        return existing

    factory = unreal.MaterialFactoryNew()
    material = asset_tools.create_asset(asset_name, MATERIAL_ROOT,
                                        unreal.Material, factory)
    if not material:
        raise RuntimeError(f"Could not create material {asset_path}")

    set_prop(material, "two_sided", opacity is not None)
    if opacity is not None:
        set_prop(material, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        # This remains guarded because Substrate-enabled projects can expose a
        # slightly different property set between engine point releases.
        if hasattr(unreal, "TranslucencyLightingMode"):
            set_prop(material, "translucency_lighting_mode",
                     unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)

    def vector_parameter(parameter_name, value, x, y):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionVectorParameter, x, y)
        set_prop(node, "parameter_name", parameter_name)
        set_prop(node, "default_value", unreal.LinearColor(*value))
        return node

    def scalar_parameter(parameter_name, value, x, y):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionScalarParameter, x, y)
        set_prop(node, "parameter_name", parameter_name)
        set_prop(node, "default_value", float(value))
        return node

    color_node = vector_parameter("BaseColor", base_color, -640, -120)
    rough_node = scalar_parameter("Roughness", roughness, -640, 80)
    metal_node = scalar_parameter("Metallic", metallic, -640, 200)
    unreal.MaterialEditingLibrary.connect_material_property(
        color_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough_node, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(
        metal_node, "", unreal.MaterialProperty.MP_METALLIC)

    if emissive is not None:
        emissive_node = vector_parameter("EmissiveColor", emissive, -640, 340)
        unreal.MaterialEditingLibrary.connect_material_property(
            emissive_node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if opacity is not None:
        opacity_node = scalar_parameter("Opacity", opacity, -640, 460)
        unreal.MaterialEditingLibrary.connect_material_property(
            opacity_node, "", unreal.MaterialProperty.MP_OPACITY)
    if refraction is not None:
        refraction_node = scalar_parameter("IOR", refraction, -640, 580)
        unreal.MaterialEditingLibrary.connect_material_property(
            refraction_node, "", unreal.MaterialProperty.MP_REFRACTION)

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    return material


def tag_actor(actor, label, folder):
    actor.set_actor_label(f"{GENERATED_PREFIX}{label}")
    try:
        actor.set_folder_path(folder)
    except Exception:
        pass
    return actor


def spawn_mesh(label, mesh, location, scale, rotation=None, material=None,
               folder="OrbitalGlassLab/Geometry", movable=False):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = editor_actors.spawn_actor_from_object(mesh, location, rotation)
    if not actor:
        raise RuntimeError(f"Failed to spawn mesh actor {label}")
    tag_actor(actor, label, folder)
    actor.set_actor_scale3d(scale)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component:
        if material:
            component.set_material(0, material)
        if movable:
            set_prop(component, "mobility", unreal.ComponentMobility.MOVABLE)
    return actor


def spawn_actor(label, actor_class, location, rotation=None,
                folder="OrbitalGlassLab/Environment"):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = editor_actors.spawn_actor_from_class(actor_class, location, rotation)
    if not actor:
        raise RuntimeError(f"Failed to spawn actor {label}")
    return tag_actor(actor, label, folder)


def component(actor, component_class):
    return actor.get_component_by_class(component_class)


def look_at(origin, target):
    return unreal.MathLibrary.find_look_at_rotation(origin, target)


def open_generated_level():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        log(f"Loading existing level {MAP_PATH}")
        if not level_editor.load_level(MAP_PATH):
            raise RuntimeError(f"Could not load level {MAP_PATH}")
    else:
        log(f"Creating level {MAP_PATH}")
        if not level_editor.new_level(MAP_PATH, False):
            raise RuntimeError(f"Could not create level {MAP_PATH}")

    removed = 0
    for actor in list(editor_actors.get_all_level_actors()):
        try:
            if actor.get_actor_label().startswith(GENERATED_PREFIX):
                editor_actors.destroy_actor(actor)
                removed += 1
        except Exception:
            continue
    if removed:
        log(f"Removed {removed} previously generated actors")


def build_environment(materials):
    sun = spawn_actor(
        "Sun", unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 3500.0),
        unreal.Rotator(-28.0, -35.0, 0.0))
    sun_component = component(sun, unreal.DirectionalLightComponent)
    set_prop(sun_component, "mobility", unreal.ComponentMobility.MOVABLE)
    set_prop(sun_component, "intensity", 8.0)
    set_prop(sun_component, "use_temperature", True)
    set_prop(sun_component, "temperature", 5600.0)
    set_prop(sun_component, "cast_cloud_shadows", True)

    sky_atmosphere = spawn_actor(
        "SkyAtmosphere", unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0))
    set_prop(component(sky_atmosphere, unreal.SkyAtmosphereComponent),
             "transform_mode", unreal.SkyAtmosphereTransformMode.PLANET_TOP_AT_ABSOLUTE_WORLD_ORIGIN)

    skylight = spawn_actor(
        "SkyLight", unreal.SkyLight, unreal.Vector(0.0, 0.0, 1800.0))
    skylight_component = component(skylight, unreal.SkyLightComponent)
    set_prop(skylight_component, "mobility", unreal.ComponentMobility.MOVABLE)
    set_prop(skylight_component, "real_time_capture", True)
    set_prop(skylight_component, "intensity", 0.85)

    fog = spawn_actor(
        "HeightFog", unreal.ExponentialHeightFog, unreal.Vector(0.0, 0.0, 0.0))
    fog_component = component(fog, unreal.ExponentialHeightFogComponent)
    set_prop(fog_component, "fog_density", 0.00025)
    set_prop(fog_component, "fog_height_falloff", 0.18)
    # Volumetric scattering made the low LED lane fill the entire frame in
    # MRQ. The thin height fog still separates planes without blooming.
    set_prop(fog_component, "volumetric_fog", False)
    set_prop(fog_component, "volumetric_fog_scattering_distribution", 0.2)

    try:
        cloud = spawn_actor(
            "VolumetricCloud", unreal.VolumetricCloud, unreal.Vector(0.0, 0.0, 0.0))
        set_prop(component(cloud, unreal.VolumetricCloudComponent),
                 "layer_bottom_altitude", 5.0)
    except Exception as exc:
        warn(f"Volumetric cloud skipped: {exc}")

    post = spawn_actor(
        "PostProcess", unreal.PostProcessVolume, unreal.Vector(0.0, 0.0, 1000.0))
    set_prop(post, "unbound", True)
    settings = post.get_editor_property("settings")
    set_prop(settings, "override_bloom_intensity", True)
    set_prop(settings, "bloom_intensity", 0.03)
    set_prop(settings, "override_auto_exposure_min_brightness", True)
    set_prop(settings, "override_auto_exposure_max_brightness", True)
    # Lock exposure so camera cuts cannot pump from daylight to black and
    # back. In the project's extended-luminance mode these values are EV100.
    set_prop(settings, "auto_exposure_min_brightness", 2.0)
    set_prop(settings, "auto_exposure_max_brightness", 2.0)
    set_prop(settings, "override_auto_exposure_bias", True)
    set_prop(settings, "auto_exposure_bias", 0.35)

    # The sphere gives the map a physical visual boundary. It is intentionally
    # translucent and two-sided, while Sky Atmosphere supplies the actual sky.
    spawn_mesh(
        "WorldBoundary", load_engine_mesh("Sphere"),
        unreal.Vector(0.0, 0.0, 0.0), unreal.Vector(120.0, 120.0, 120.0),
        material=materials["dome"], folder="OrbitalGlassLab/Boundary")


def build_stage(materials):
    plane = load_engine_mesh("Plane")
    cylinder = load_engine_mesh("Cylinder")
    cube = load_engine_mesh("Cube")
    sphere = load_engine_mesh("Sphere")

    spawn_mesh(
        "Ground", plane, unreal.Vector(0.0, 0.0, 0.0),
        unreal.Vector(90.0, 90.0, 90.0), material=materials["ground"])
    spawn_mesh(
        "CentralPlinth", cylinder, unreal.Vector(0.0, 0.0, 80.0),
        unreal.Vector(12.0, 12.0, 0.8), material=materials["plinth"])

    # The design pivot requested by the user is (0, 0, 1000 cm). The hero cube
    # starts 800 cm from it and will receive orbital animation in the next pass.
    pivot = unreal.Vector(0.0, 0.0, 1000.0)
    spawn_mesh(
        "OrbitPivot", sphere, pivot, unreal.Vector(0.18, 0.18, 0.18),
        material=materials["pivot"], folder="OrbitalGlassLab/Rig")
    hero = spawn_mesh(
        "HeroGlassCube", cube, unreal.Vector(800.0, 0.0, 1000.0),
        unreal.Vector(2.8, 2.8, 2.8), unreal.Rotator(18.0, 32.0, 11.0),
        materials["glass"], "OrbitalGlassLab/Hero", movable=True)
    try:
        hero.set_editor_property("tags", [unreal.Name("OrbitalHero")])
    except Exception:
        pass

    # A smaller reflective core gives the translucent shell readable edges
    # and layered reflections even before final path-traced polishing.
    core = spawn_mesh(
        "HeroReflectiveCore", cube, unreal.Vector(800.0, 0.0, 1000.0),
        unreal.Vector(2.18, 2.18, 2.18), unreal.Rotator(18.0, 32.0, 11.0),
        materials["core"], "OrbitalGlassLab/Hero", movable=True)
    try:
        core.set_editor_property("tags", [unreal.Name("OrbitalHeroCore")])
    except Exception:
        pass

    # Two restrained studio fills keep the glass readable after sunset.
    fill_specs = [
        ("HeroFillCool", unreal.Vector(0.0, -1150.0, 1550.0),
         2200.0, unreal.Color(55, 155, 255, 255)),
        ("HeroFillWarm", unreal.Vector(0.0, 1200.0, 1250.0),
         1200.0, unreal.Color(255, 125, 70, 255)),
    ]
    for label, position, intensity, color in fill_specs:
        fill = spawn_actor(label, unreal.PointLight, position,
                           folder="OrbitalGlassLab/Lighting")
        fill_component = component(fill, unreal.PointLightComponent)
        set_prop(fill_component, "mobility", unreal.ComponentMobility.MOVABLE)
        set_prop(fill_component, "intensity", intensity)
        set_prop(fill_component, "attenuation_radius", 2300.0)
        set_prop(fill_component, "light_color", color)
        set_prop(fill_component, "use_inverse_squared_falloff", True)

    try:
        reflection = spawn_actor(
            "ReflectionCapture", unreal.SphereReflectionCapture,
            unreal.Vector(0.0, 0.0, 1000.0),
            folder="OrbitalGlassLab/Lighting")
        reflection_component = component(
            reflection, unreal.SphereReflectionCaptureComponent)
        set_prop(reflection_component, "influence_radius", 5200.0)
    except Exception as exc:
        warn(f"Reflection capture skipped: {exc}")

    # A compact LED lane near the plinth. Point lights are movable so they can
    # later be keyed on at night by a Level Sequence or Day Sequence controller.
    led_positions = [
        (-520.0, -420.0, 145.0), (-260.0, -420.0, 145.0),
        (0.0, -420.0, 145.0), (260.0, -420.0, 145.0),
        (520.0, -420.0, 145.0),
    ]
    for index, coords in enumerate(led_positions, start=1):
        position = unreal.Vector(*coords)
        spawn_mesh(
            f"LEDMesh_{index:02d}", sphere, position,
            unreal.Vector(0.22, 0.22, 0.08), material=materials["led"],
            folder="OrbitalGlassLab/LEDs")
        light = spawn_actor(
            f"LEDLight_{index:02d}", unreal.PointLight,
            unreal.Vector(coords[0], coords[1], coords[2] + 40.0),
            folder="OrbitalGlassLab/LEDs")
        light_component = component(light, unreal.PointLightComponent)
        set_prop(light_component, "mobility", unreal.ComponentMobility.MOVABLE)
        set_prop(light_component, "intensity", 0.0)
        set_prop(light_component, "attenuation_radius", 520.0)
        set_prop(light_component, "light_color", unreal.Color(40, 175, 255, 255))
        try:
            light_component.set_light_color(
                unreal.LinearColor(0.02, 0.32, 1.0, 1.0), True)
        except Exception:
            pass
        set_prop(light_component, "use_inverse_squared_falloff", True)


def build_cameras():
    target = unreal.Vector(0.0, 0.0, 850.0)
    camera_specs = [
        ("Camera_OrbitWide", unreal.Vector(2600.0, -2600.0, 1750.0), 35.0),
        ("Camera_GlassClose", unreal.Vector(1500.0, -900.0, 1250.0), 55.0),
        ("Camera_LEDLow", unreal.Vector(1000.0, -1800.0, 310.0), 40.0),
    ]
    for label, location, focal_length in camera_specs:
        camera = spawn_actor(
            label, unreal.CineCameraActor, location, look_at(location, target),
            folder="OrbitalGlassLab/Cameras")
        camera_component = component(camera, unreal.CineCameraComponent)
        set_prop(camera_component, "current_focal_length", focal_length)
        set_prop(camera_component, "current_aperture", 4.0)
        focus = camera_component.get_editor_property("focus_settings")
        if hasattr(unreal, "CameraFocusMethod"):
            set_prop(focus, "focus_method", unreal.CameraFocusMethod.MANUAL)
        set_prop(focus, "manual_focus_distance", (target - location).length())


def build_scene():
    log("Build started")
    open_generated_level()

    materials = {
        "ground": create_material(
            "M_GroundDarkV2", (0.012, 0.022, 0.035, 1.0), 0.68, 0.05),
        "plinth": create_material(
            "M_PlatformStone", (0.09, 0.11, 0.14, 1.0), 0.72, 0.05),
        "glass": create_material(
            "M_HeroRoughGlassV4", (0.02, 0.28, 0.48, 1.0), 0.14, 0.0,
            opacity=0.52, refraction=1.45),
        "core": create_material(
            "M_HeroReflectiveCoreV4", (0.025, 0.12, 0.2, 1.0),
            0.2, 0.55),
        "led": create_material(
            "M_LEDFixtureV2", (0.01, 0.12, 0.18, 1.0), 0.22, 0.0,
            emissive=(0.0, 0.35, 0.8, 1.0)),
        "pivot": create_material(
            "M_PivotDark", (0.008, 0.012, 0.018, 1.0), 0.85, 0.0),
        "dome": create_material(
            "M_WorldBoundaryV2", (0.004, 0.012, 0.025, 1.0), 0.55, 0.0,
            opacity=0.008),
    }

    build_environment(materials)
    build_stage(materials)
    build_cameras()

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    log("Build complete: L_GlassOrbit saved")


try:
    build_scene()
except Exception as error:
    unreal.log_error(f"[OrbitalGlassLab] Build failed: {error}")
    raise
