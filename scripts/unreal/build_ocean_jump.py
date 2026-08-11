"""Build the Ocean Jump test map for Unreal Engine 5.8.

The map uses only engine/Water-plugin assets: a Gerstner-wave ocean surface,
two rotating platforms, a lightweight generic humanoid and three cameras.
Run from Tools > Execute Python Script inside Unreal Editor.
"""

import unreal


MAP_PATH = "/Game/OrbitalGlassLab/Maps/L_OceanJump"
MATERIAL_ROOT = "/Game/OrbitalGlassLab/Materials"
PREFIX = "OJ_"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def log(message):
    unreal.log(f"[OceanJump] {message}")


def warn(message):
    unreal.log_warning(f"[OceanJump] {message}")


def set_prop(obj, name, value):
    if obj is None:
        return False
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception as exc:
        warn(f"{obj.get_class().get_name()}.{name} skipped: {exc}")
        return False


def load(path):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError(f"Missing asset: {path}")
    return asset


def mesh(name):
    return load(f"/Engine/BasicShapes/{name}.{name}")


def make_material(name, color, roughness, metallic=0.0, emissive=None):
    path = f"{MATERIAL_ROOT}/{name}"
    existing = unreal.load_asset(path)
    if existing:
        return existing
    material = asset_tools.create_asset(
        name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError(f"Could not create {path}")

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

    base = vector_parameter("BaseColor", color, -520, -100)
    rough = scalar_parameter("Roughness", roughness, -520, 80)
    metal = scalar_parameter("Metallic", metallic, -520, 180)
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(
        metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        glow = vector_parameter("EmissiveColor", emissive, -520, 300)
        unreal.MaterialEditingLibrary.connect_material_property(
            glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return material


def make_ocean_material():
    """Create a self-contained animated ocean material for any static mesh.

    The stock Water_Material_Ocean expects a complete WaterBody/Landscape
    render-data setup. This material keeps the Water plugin's authored normal
    map and pans it in real time, so it also renders correctly in MRQ.
    """
    name = "M_OJ_AnimatedOceanV2"
    path = f"{MATERIAL_ROOT}/{name}"
    existing = unreal.load_asset(path)
    if existing:
        return existing
    material = asset_tools.create_asset(
        name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError(f"Could not create {path}")

    def scalar(parameter_name, value, x, y):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionScalarParameter, x, y)
        set_prop(node, "parameter_name", parameter_name)
        set_prop(node, "default_value", float(value))
        return node

    color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -700, -180)
    set_prop(color, "parameter_name", "DeepWaterColor")
    set_prop(color, "default_value", unreal.LinearColor(0.004, 0.055, 0.16, 1.0))
    rough = scalar("Roughness", 0.08, -700, 0)
    metal = scalar("Metallic", 0.08, -700, 100)
    unreal.MaterialEditingLibrary.connect_material_property(
        color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(
        metal, "", unreal.MaterialProperty.MP_METALLIC)
    ambient = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -700, 200)
    set_prop(ambient, "parameter_name", "WaterAmbient")
    set_prop(ambient, "default_value", unreal.LinearColor(0.0, 0.012, 0.035, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        ambient, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    normal_texture = load(
        "/Water/Textures/Normals/T_Water_TilingNormal_Waves_02."
        "T_Water_TilingNormal_Waves_02")
    coordinates = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -900, 260)
    set_prop(coordinates, "u_tiling", 18.0)
    set_prop(coordinates, "v_tiling", 18.0)
    panner = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionPanner, -660, 260)
    set_prop(panner, "speed_x", 0.025)
    set_prop(panner, "speed_y", -0.014)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -380, 260)
    set_prop(sample, "parameter_name", "WaveNormal")
    set_prop(sample, "texture", normal_texture)
    try:
        set_prop(sample, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    except Exception:
        pass
    unreal.MaterialEditingLibrary.connect_material_expressions(
        coordinates, "", panner, "Coordinate")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        panner, "", sample, "Coordinates")
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_NORMAL)

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return material


def make_sunset_material():
    name = "M_OJ_SunsetGradient"
    path = f"{MATERIAL_ROOT}/{name}"
    material = unreal.load_asset(path)
    if material:
        # Rebuild the graph so script fixes also update an existing project.
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    else:
        material = asset_tools.create_asset(
            name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError(f"Could not create {path}")
    try:
        set_prop(material, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    except Exception:
        pass
    set_prop(material, "two_sided", True)

    bottom = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -650, -100)
    top = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -650, 40)
    set_prop(bottom, "parameter_name", "HorizonColor")
    set_prop(bottom, "default_value", unreal.LinearColor(0.48, 0.055, 0.008, 1.0))
    set_prop(top, "parameter_name", "ZenithColor")
    set_prop(top, "default_value", unreal.LinearColor(0.012, 0.008, 0.085, 1.0))
    texcoord = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -650, 210)
    green = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionComponentMask, -430, 210)
    set_prop(green, "g", True)
    lerp = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, -180, 20)
    unreal.MaterialEditingLibrary.connect_material_expressions(
        bottom, "", lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        top, "", lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        texcoord, "", green, "")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        green, "", lerp, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(
        lerp, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return material


def label(actor, name, folder):
    actor.set_actor_label(f"{PREFIX}{name}")
    try:
        actor.set_folder_path(folder)
    except Exception:
        pass
    return actor


def spawn_actor(name, actor_class, location, rotation=None, folder="OceanJump"):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = actors.spawn_actor_from_class(actor_class, location, rotation)
    if not actor:
        raise RuntimeError(f"Could not spawn {name}")
    return label(actor, name, folder)


def spawn_mesh(name, static_mesh, location, scale, material=None,
               rotation=None, folder="OceanJump/Geometry", movable=False):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = actors.spawn_actor_from_object(static_mesh, location, rotation)
    if not actor:
        raise RuntimeError(f"Could not spawn mesh {name}")
    label(actor, name, folder)
    actor.set_actor_scale3d(scale)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component:
        if material:
            component.set_material(0, material)
        if movable:
            set_prop(component, "mobility", unreal.ComponentMobility.MOVABLE)
    return actor


def component(actor, cls):
    return actor.get_component_by_class(cls)


def open_level():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not levels.load_level(MAP_PATH):
            raise RuntimeError(f"Could not load {MAP_PATH}")
    else:
        if not levels.new_level(MAP_PATH, False):
            raise RuntimeError(f"Could not create {MAP_PATH}")
    for actor in list(actors.get_all_level_actors()):
        try:
            if actor.get_actor_label().startswith(PREFIX):
                actors.destroy_actor(actor)
        except Exception:
            pass


def build_environment():
    sun = spawn_actor(
        "Sun", unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 4500.0),
        unreal.Rotator(-35.0, -70.0, 0.0), "OceanJump/Lighting")
    sun_component = component(sun, unreal.DirectionalLightComponent)
    set_prop(sun_component, "mobility", unreal.ComponentMobility.MOVABLE)
    set_prop(sun_component, "intensity", 7.0)
    set_prop(sun_component, "use_temperature", True)
    set_prop(sun_component, "temperature", 5100.0)
    set_prop(sun_component, "cast_cloud_shadows", True)

    atmosphere = spawn_actor(
        "SkyAtmosphere", unreal.SkyAtmosphere, unreal.Vector(),
        folder="OceanJump/Environment")
    set_prop(component(atmosphere, unreal.SkyAtmosphereComponent),
             "transform_mode",
             unreal.SkyAtmosphereTransformMode.PLANET_TOP_AT_ABSOLUTE_WORLD_ORIGIN)

    sky = spawn_actor("SkyLight", unreal.SkyLight,
                      unreal.Vector(0.0, 0.0, 2200.0),
                      folder="OceanJump/Lighting")
    sky_component = component(sky, unreal.SkyLightComponent)
    set_prop(sky_component, "mobility", unreal.ComponentMobility.MOVABLE)
    set_prop(sky_component, "real_time_capture", True)
    set_prop(sky_component, "intensity", 1.0)

    try:
        cloud = spawn_actor("VolumetricCloud", unreal.VolumetricCloud,
                            unreal.Vector(), folder="OceanJump/Environment")
        set_prop(component(cloud, unreal.VolumetricCloudComponent),
                 "layer_bottom_altitude", 4.0)
    except Exception as exc:
        warn(f"Cloud skipped: {exc}")

    fog = spawn_actor("HeightFog", unreal.ExponentialHeightFog,
                      unreal.Vector(), folder="OceanJump/Environment")
    fog_component = component(fog, unreal.ExponentialHeightFogComponent)
    set_prop(fog_component, "fog_density", 0.0012)
    set_prop(fog_component, "fog_height_falloff", 0.11)
    set_prop(fog_component, "volumetric_fog", True)
    set_prop(fog_component, "volumetric_fog_extinction_scale", 0.35)

    post = spawn_actor("PostProcess", unreal.PostProcessVolume,
                       unreal.Vector(0.0, 0.0, 1000.0),
                       folder="OceanJump/Lighting")
    set_prop(post, "unbound", True)
    settings = post.get_editor_property("settings")
    set_prop(settings, "override_bloom_intensity", True)
    set_prop(settings, "bloom_intensity", 0.18)
    set_prop(settings, "override_motion_blur_amount", True)
    set_prop(settings, "motion_blur_amount", 0.05)
    set_prop(settings, "override_auto_exposure_min_brightness", True)
    set_prop(settings, "override_auto_exposure_max_brightness", True)
    set_prop(settings, "auto_exposure_min_brightness", 1.0)
    set_prop(settings, "auto_exposure_max_brightness", 1.0)
    set_prop(settings, "override_auto_exposure_bias", True)
    set_prop(settings, "auto_exposure_bias", 0.75)


def build_ocean(ocean_material):
    water_mesh = load("/Water/Meshes/S_WaterPlane_256.S_WaterPlane_256")
    ocean = spawn_mesh(
        "OceanSurface", water_mesh, unreal.Vector(0.0, 0.0, 0.0),
        unreal.Vector(16.0, 16.0, 16.0), ocean_material,
        folder="OceanJump/Ocean", movable=False)
    try:
        ocean.set_editor_property("tags", [unreal.Name("GerstnerOcean")])
    except Exception:
        pass

    # A WaterZone supplies the scene-view water buffers used by the stock
    # ocean material. The direct mesh remains visible even without landscape.
    try:
        zone = spawn_actor("WaterZone", unreal.WaterZone, unreal.Vector(),
                           folder="OceanJump/Ocean")
        set_prop(zone, "zone_extent", unreal.Vector2D(20000.0, 20000.0))
        set_prop(zone, "render_target_resolution", unreal.IntPoint(1024, 1024))
    except Exception as exc:
        warn(f"WaterZone skipped: {exc}")


def build_sunset_backdrops(material):
    # A two-sided sphere avoids seams and uncovered angles as the camera orbits.
    dome = spawn_mesh(
        "SunsetDome", mesh("Sphere"), unreal.Vector(0.0, 0.0, 800.0),
        unreal.Vector(100.0, 100.0, 100.0), material,
        unreal.Rotator(0.0, 0.0, 0.0),
        "OceanJump/Environment", movable=True)
    dome_component = component(dome, unreal.StaticMeshComponent)
    set_prop(dome_component, "cast_shadow", False)


def build_platforms(materials):
    cube = mesh("Cube")
    specs = [
        ("PlatformA", unreal.Vector(-750.0, 0.0, 500.0),
         unreal.Vector(5.5, 6.5, 1.0), materials["platform_a"]),
        ("PlatformB", unreal.Vector(750.0, 0.0, 500.0),
         unreal.Vector(5.5, 6.5, 1.0), materials["platform_b"]),
    ]
    for name, position, scale, material in specs:
        spawn_mesh(name, cube, position, scale, material,
                   folder="OceanJump/Platforms", movable=True)

    # Low edge lights make the landing geometry readable against the ocean.
    for index, x in enumerate((-980.0, -520.0, 520.0, 980.0), start=1):
        light = spawn_actor(f"EdgeLight_{index:02d}", unreal.PointLight,
                            unreal.Vector(x, -260.0, 650.0),
                            folder="OceanJump/Lighting")
        light_component = component(light, unreal.PointLightComponent)
        set_prop(light_component, "mobility", unreal.ComponentMobility.MOVABLE)
        set_prop(light_component, "intensity", 750.0)
        set_prop(light_component, "attenuation_radius", 850.0)
        try:
            light_component.set_light_color(
                unreal.LinearColor(0.03, 0.25, 1.0, 1.0), True)
        except Exception:
            pass

    sunset_fill = spawn_actor(
        "SunsetFill", unreal.PointLight, unreal.Vector(0.0, -900.0, 2100.0),
        folder="OceanJump/Lighting")
    fill_component = component(sunset_fill, unreal.PointLightComponent)
    set_prop(fill_component, "mobility", unreal.ComponentMobility.MOVABLE)
    set_prop(fill_component, "intensity", 4800.0)
    set_prop(fill_component, "attenuation_radius", 5200.0)
    try:
        fill_component.set_light_color(
            unreal.LinearColor(1.0, 0.18, 0.035, 1.0), True)
    except Exception:
        pass


def build_player(material):
    """Assemble an asset-free humanoid from engine primitives."""
    cube = mesh("Cube")
    sphere = mesh("Sphere")
    cylinder = mesh("Cylinder")
    origin = unreal.Vector(-680.0, 0.0, 690.0)
    parts = [
        ("Player_Pelvis", cube, (0, 0, 0), (.28, .22, .22), (0, 0, 0)),
        ("Player_Torso", cube, (0, 0, 48), (.38, .24, .52), (0, 0, 0)),
        ("Player_Head", sphere, (0, 0, 112), (.22, .22, .24), (0, 0, 0)),
        ("Player_ArmL", cylinder, (0, -34, 50), (.10, .10, .45), (-18, 0, -12)),
        ("Player_ArmR", cylinder, (0, 34, 50), (.10, .10, .45), (18, 0, 12)),
        ("Player_LegL", cylinder, (0, -15, -48), (.13, .13, .52), (6, 0, -3)),
        ("Player_LegR", cylinder, (0, 15, -48), (.13, .13, .52), (-6, 0, 3)),
        ("Player_FootL", cube, (18, -15, -104), (.28, .14, .11), (0, 0, 0)),
        ("Player_FootR", cube, (18, 15, -104), (.28, .14, .11), (0, 0, 0)),
    ]
    for name, static_mesh, offset, scale, rotation in parts:
        spawn_mesh(
            name, static_mesh,
            origin + unreal.Vector(*offset), unreal.Vector(*scale), material,
            unreal.Rotator(*rotation), "OceanJump/Player", movable=True)


def build_cameras():
    target = unreal.Vector(-600.0, 0.0, 760.0)
    specs = [
        ("CameraThird", unreal.Vector(-1500.0, -950.0, 1050.0), 35.0),
        ("CameraFirst", unreal.Vector(-600.0, 0.0, 810.0), 24.0),
        ("CameraJump", unreal.Vector(0.0, -1800.0, 1050.0), 38.0),
        ("CameraLanding", unreal.Vector(900.0, 1000.0, 1050.0), 38.0),
    ]
    for name, location, focal in specs:
        rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
        camera = spawn_actor(name, unreal.CineCameraActor, location, rotation,
                             "OceanJump/Cameras")
        camera_component = component(camera, unreal.CineCameraComponent)
        set_prop(camera_component, "current_focal_length", focal)
        set_prop(camera_component, "current_aperture", 4.0)


def build():
    log("Build started")
    open_level()
    materials = {
        "platform_a": make_material(
            "M_OJ_PlatformA", (0.015, 0.06, 0.12, 1.0), 0.22, 0.72),
        "platform_b": make_material(
            "M_OJ_PlatformB", (0.12, 0.035, 0.018, 1.0), 0.27, 0.62),
        "player": make_material(
            "M_OJ_Player", (0.04, 0.22, 0.48, 1.0), 0.32, 0.24,
            emissive=(0.0, 0.018, 0.055, 1.0)),
        "ocean": make_ocean_material(),
        "sunset": make_sunset_material(),
    }
    build_environment()
    build_ocean(materials["ocean"])
    build_sunset_backdrops(materials["sunset"])
    build_platforms(materials)
    build_player(materials["player"])
    build_cameras()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    log("Build complete: L_OceanJump saved")


try:
    build()
except Exception as exc:
    unreal.log_error(f"[OceanJump] Build failed: {exc}")
    raise
