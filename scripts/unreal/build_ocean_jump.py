"""Build the Ocean Jump v3 test map for Unreal Engine 5.8.

The map uses the bundled third-person template assets: a displaced ocean,
two rotating platforms, Manny and four cinematic cameras.
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


def make_textured_material(name, tint, roughness, metallic, color_path,
                           normal_path=None, tiling=6.0):
    """Create a textured material using assets bundled with Unreal Engine."""
    path = f"{MATERIAL_ROOT}/{name}"
    material = unreal.load_asset(path)
    if material:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    else:
        material = asset_tools.create_asset(
            name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError(f"Could not create {path}")

    color_texture = load(color_path)
    coordinates = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -900, -120)
    set_prop(coordinates, "u_tiling", float(tiling))
    set_prop(coordinates, "v_tiling", float(tiling))
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -650, -120)
    set_prop(sample, "parameter_name", "SurfaceColor")
    set_prop(sample, "texture", color_texture)
    tint_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -650, 80)
    set_prop(tint_node, "parameter_name", "Tint")
    set_prop(tint_node, "default_value", unreal.LinearColor(*tint))
    tinted = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -360, -70)
    unreal.MaterialEditingLibrary.connect_material_expressions(
        coordinates, "", sample, "Coordinates")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        sample, "RGB", tinted, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        tint_node, "", tinted, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        tinted, "", unreal.MaterialProperty.MP_BASE_COLOR)

    for parameter_name, value, y, target in (
            ("Roughness", roughness, 220, unreal.MaterialProperty.MP_ROUGHNESS),
            ("Metallic", metallic, 340, unreal.MaterialProperty.MP_METALLIC)):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionScalarParameter, -360, y)
        set_prop(node, "parameter_name", parameter_name)
        set_prop(node, "default_value", float(value))
        unreal.MaterialEditingLibrary.connect_material_property(node, "", target)

    if normal_path:
        normal_sample = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSampleParameter2D,
            -360, 470)
        set_prop(normal_sample, "parameter_name", "SurfaceNormal")
        set_prop(normal_sample, "texture", load(normal_path))
        set_prop(normal_sample, "sampler_type",
                 unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        unreal.MaterialEditingLibrary.connect_material_expressions(
            coordinates, "", normal_sample, "Coordinates")
        unreal.MaterialEditingLibrary.connect_material_property(
            normal_sample, "RGB", unreal.MaterialProperty.MP_NORMAL)

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return material


def make_ocean_material():
    """Create a self-contained animated ocean material for any static mesh.

    The stock Water_Material_Ocean expects a complete WaterBody/Landscape
    render-data setup. This material combines the Water plugin normal map with
    two procedural vertex waves, so it also renders correctly in MRQ.
    """
    name = "M_OJ_AnimatedOceanV4"
    path = f"{MATERIAL_ROOT}/{name}"
    existing = unreal.load_asset(path)
    if existing:
        material = existing
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    else:
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

    deep_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -920, -220)
    set_prop(deep_color, "parameter_name", "DeepWaterColor")
    set_prop(deep_color, "default_value",
             unreal.LinearColor(0.002, 0.026, 0.075, 1.0))
    crest_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -920, -100)
    set_prop(crest_color, "parameter_name", "CrestColor")
    set_prop(crest_color, "default_value",
             unreal.LinearColor(0.008, 0.085, 0.14, 1.0))
    foam_coordinates = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -920, 20)
    set_prop(foam_coordinates, "u_tiling", 10.0)
    set_prop(foam_coordinates, "v_tiling", 10.0)
    foam_panner = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionPanner, -700, 20)
    set_prop(foam_panner, "speed_x", -0.018)
    set_prop(foam_panner, "speed_y", 0.026)
    foam_sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -480, 20)
    set_prop(foam_sample, "parameter_name", "FoamTexture")
    set_prop(foam_sample, "texture", load(
        "/Water/Textures/Foam/T_WaterFlow_03_Foam_Tiled."
        "T_WaterFlow_03_Foam_Tiled"))
    foam_strength = scalar("FoamStrength", 0.04, -480, 170)
    foam_mask = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -220, 30)
    water_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, 20, -100)
    unreal.MaterialEditingLibrary.connect_material_expressions(
        foam_coordinates, "", foam_panner, "Coordinate")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        foam_panner, "", foam_sample, "Coordinates")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        foam_sample, "R", foam_mask, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        foam_strength, "", foam_mask, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        deep_color, "", water_color, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        crest_color, "", water_color, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        foam_mask, "", water_color, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(
        water_color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = scalar("Roughness", 0.20, -700, 260)
    metal = scalar("Metallic", 0.04, -700, 360)
    specular = scalar("Specular", 0.22, -700, 420)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(
        metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.connect_material_property(
        specular, "", unreal.MaterialProperty.MP_SPECULAR)
    ambient = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -700, 460)
    set_prop(ambient, "parameter_name", "WaterAmbient")
    set_prop(ambient, "default_value", unreal.LinearColor(0.0, 0.018, 0.055, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        ambient, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    normal_texture = load(
        "/Water/Textures/Normals/T_Water_TilingNormal_Waves_02."
        "T_Water_TilingNormal_Waves_02")
    coordinates = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -900, 260)
    set_prop(coordinates, "u_tiling", 24.0)
    set_prop(coordinates, "v_tiling", 24.0)
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
    coordinates_b = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -900, 420)
    set_prop(coordinates_b, "u_tiling", 37.0)
    set_prop(coordinates_b, "v_tiling", 37.0)
    panner_b = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionPanner, -660, 420)
    set_prop(panner_b, "speed_x", -0.019)
    set_prop(panner_b, "speed_y", 0.031)
    sample_b = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -380, 470)
    set_prop(sample_b, "parameter_name", "WaveNormalSecondary")
    set_prop(sample_b, "texture", normal_texture)
    set_prop(sample_b, "sampler_type",
             unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    normal_mix = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, -120, 270)
    normal_mix_amount = scalar("SecondaryNormalBlend", 0.46, -360, 620)
    unreal.MaterialEditingLibrary.connect_material_expressions(
        coordinates_b, "", panner_b, "Coordinate")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        panner_b, "", sample_b, "Coordinates")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        sample, "RGB", normal_mix, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        sample_b, "RGB", normal_mix, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        normal_mix_amount, "", normal_mix, "Alpha")
    flat_normal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -160, 360)
    set_prop(flat_normal, "parameter_name", "FlatNormal")
    set_prop(flat_normal, "default_value", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    normal_strength = scalar("NormalStrength", 0.24, -160, 500)
    normal_blend = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, 80, 380)
    unreal.MaterialEditingLibrary.connect_material_expressions(
        flat_normal, "", normal_blend, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        normal_mix, "", normal_blend, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        normal_strength, "", normal_blend, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(
        normal_blend, "", unreal.MaterialProperty.MP_NORMAL)

    # Displace the high-density Water plane with two crossing waves. Their
    # different headings and periods prevent the flat marbled look of v1.
    displacement_uv = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -1180, 560)
    mask_x = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionComponentMask, -980, 500)
    mask_y = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionComponentMask, -980, 620)
    for channel in ("r", "g", "b", "a"):
        set_prop(mask_x, channel, channel == "r")
        set_prop(mask_y, channel, channel == "g")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        displacement_uv, "", mask_x, "")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        displacement_uv, "", mask_y, "")
    time_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTime, -980, 780)

    def multiply(a, b, x, y):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, x, y)
        unreal.MaterialEditingLibrary.connect_material_expressions(a, "", node, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(b, "", node, "B")
        return node

    def add(a, b, x, y):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionAdd, x, y)
        unreal.MaterialEditingLibrary.connect_material_expressions(a, "", node, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(b, "", node, "B")
        return node

    def wave(label, x_input, y_input, direction_y, frequency, speed,
             amplitude, x, y):
        direction = scalar(f"{label}DirectionY", direction_y, x, y + 80)
        y_directed = multiply(y_input, direction, x + 180, y + 70)
        spatial = add(x_input, y_directed, x + 360, y)
        frequency_node = scalar(f"{label}Frequency", frequency, x, y + 180)
        phase_space = multiply(spatial, frequency_node, x + 540, y)
        speed_node = scalar(f"{label}Speed", speed, x, y + 280)
        phase_time = multiply(time_node, speed_node, x + 540, y + 130)
        phase = add(phase_space, phase_time, x + 720, y + 50)
        sine = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionSine, x + 900, y + 50)
        set_prop(sine, "period", 1.0)
        unreal.MaterialEditingLibrary.connect_material_expressions(
            phase, "", sine, "")
        amplitude_node = scalar(f"{label}Amplitude", amplitude, x + 720, y + 210)
        return multiply(sine, amplitude_node, x + 1080, y + 80)

    wave_a = wave("WaveA", mask_x, mask_y, 0.55, 2.2, 0.085,
                  30.0, -860, 960)
    wave_b = wave("WaveB", mask_y, mask_x, -0.42, 3.7, -0.13,
                  14.0, -860, 1320)
    combined_waves = add(wave_a, wave_b, 420, 1160)
    up_axis = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, 420, 1320)
    set_prop(up_axis, "parameter_name", "DisplacementAxis")
    set_prop(up_axis, "default_value", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    displacement = multiply(combined_waves, up_axis, 660, 1220)
    unreal.MaterialEditingLibrary.connect_material_property(
        displacement, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

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
        unreal.Rotator(roll=0.0, pitch=-35.0, yaw=-70.0),
        "OceanJump/Lighting")
    sun_component = component(sun, unreal.DirectionalLightComponent)
    set_prop(sun_component, "mobility", unreal.ComponentMobility.MOVABLE)
    set_prop(sun_component, "intensity", 7.0)
    set_prop(sun_component, "use_temperature", True)
    set_prop(sun_component, "temperature", 5100.0)
    set_prop(sun_component, "cast_cloud_shadows", True)
    set_prop(sun_component, "atmosphere_sun_light", True)
    set_prop(sun_component, "atmosphere_sun_light_index", 0)

    atmosphere = spawn_actor(
        "SkyAtmosphere", unreal.SkyAtmosphere, unreal.Vector(),
        folder="OceanJump/Environment")
    atmosphere_component = component(atmosphere, unreal.SkyAtmosphereComponent)
    set_prop(atmosphere_component, "transform_mode",
             unreal.SkyAtmosphereTransformMode.PLANET_TOP_AT_ABSOLUTE_WORLD_ORIGIN)

    sky = spawn_actor("SkyLight", unreal.SkyLight,
                      unreal.Vector(0.0, 0.0, 2200.0),
                      folder="OceanJump/Lighting")
    sky_component = component(sky, unreal.SkyLightComponent)
    set_prop(sky_component, "mobility", unreal.ComponentMobility.MOVABLE)
    set_prop(sky_component, "real_time_capture", True)
    set_prop(sky_component, "intensity", 1.35)

    try:
        cloud = spawn_actor("VolumetricCloud", unreal.VolumetricCloud,
                            unreal.Vector(), folder="OceanJump/Environment")
        cloud_component = component(cloud, unreal.VolumetricCloudComponent)
        set_prop(cloud_component, "layer_bottom_altitude", 4.0)
    except Exception as exc:
        warn(f"Cloud skipped: {exc}")

    fog = spawn_actor("HeightFog", unreal.ExponentialHeightFog,
                      unreal.Vector(), folder="OceanJump/Environment")
    fog_component = component(fog, unreal.ExponentialHeightFogComponent)
    set_prop(fog_component, "fog_density", 0.00075)
    set_prop(fog_component, "fog_height_falloff", 0.095)
    set_prop(fog_component, "start_distance", 10000.0)
    set_prop(fog_component, "volumetric_fog", True)
    set_prop(fog_component, "volumetric_fog_extinction_scale", 0.2)

    post = spawn_actor("PostProcess", unreal.PostProcessVolume,
                       unreal.Vector(0.0, 0.0, 1000.0),
                       folder="OceanJump/Lighting")
    set_prop(post, "unbound", True)
    settings = post.get_editor_property("settings")
    set_prop(settings, "override_bloom_intensity", True)
    set_prop(settings, "bloom_intensity", 0.24)
    set_prop(settings, "override_motion_blur_amount", True)
    set_prop(settings, "motion_blur_amount", 0.0)
    set_prop(settings, "override_auto_exposure_min_brightness", True)
    set_prop(settings, "override_auto_exposure_max_brightness", True)
    set_prop(settings, "auto_exposure_min_brightness", 1.0)
    set_prop(settings, "auto_exposure_max_brightness", 1.0)
    set_prop(settings, "override_auto_exposure_bias", True)
    set_prop(settings, "auto_exposure_bias", 0.55)

    try:
        reflection = spawn_actor(
            "ReflectionCapture", unreal.SphereReflectionCapture,
            unreal.Vector(0.0, 0.0, 900.0), folder="OceanJump/Lighting")
        set_prop(component(reflection, unreal.SphereReflectionCaptureComponent),
                 "influence_radius", 9000.0)
    except Exception as exc:
        warn(f"Reflection capture skipped: {exc}")


def build_ocean(ocean_material, far_material):
    water_mesh = load("/Water/Meshes/S_WaterPlane_256.S_WaterPlane_256")
    ocean = spawn_mesh(
        "OceanSurface", water_mesh, unreal.Vector(0.0, 0.0, 0.0),
        unreal.Vector(36.0, 36.0, 36.0), ocean_material,
        folder="OceanJump/Ocean", movable=False)
    try:
        ocean.set_editor_property("tags", [unreal.Name("GerstnerOcean")])
    except Exception:
        pass

    # A low-cost far surface hides the detailed mesh edge and continues well
    # past every camera frustum, like Unreal's own ocean far-distance mesh.
    far_ocean = spawn_mesh(
        "OceanFarSurface", mesh("Plane"), unreal.Vector(0.0, 0.0, -90.0),
        unreal.Vector(5000.0, 5000.0, 5000.0), far_material,
        folder="OceanJump/Ocean", movable=False)
    far_component = component(far_ocean, unreal.StaticMeshComponent)
    set_prop(far_component, "cast_shadow", False)

    # WaterZone supplies view buffers and its native far mesh when available.
    try:
        zone = spawn_actor("WaterZone", unreal.WaterZone, unreal.Vector(),
                           folder="OceanJump/Ocean")
        set_prop(zone, "zone_extent", unreal.Vector2D(120000.0, 120000.0))
        set_prop(zone, "render_target_resolution", unreal.IntPoint(1024, 1024))
        water_component = component(zone, unreal.WaterMeshComponent)
        set_prop(water_component, "far_distance_mesh_extent", 250000.0)
        set_prop(water_component, "far_distance_material", far_material)
        set_prop(water_component, "use_far_mesh_without_ocean", True)
        set_prop(water_component, "far_distance_mesh_height_without_ocean", -90.0)
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
    cube = unreal.load_asset(
        "/Game/LevelPrototyping/Meshes/SM_ChamferCube.SM_ChamferCube") or mesh("Cube")
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
        set_prop(light_component, "intensity", 400.0)
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
    set_prop(fill_component, "intensity", 900.0)
    set_prop(fill_component, "attenuation_radius", 5200.0)
    try:
        fill_component.set_light_color(
            unreal.LinearColor(1.0, 0.18, 0.035, 1.0), True)
    except Exception:
        pass


def build_player():
    """Spawn the bundled UE mannequin as a movable cinematic performer."""
    skeletal_mesh = load(
        "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple."
        "SKM_Manny_Simple")
    player = spawn_actor(
        "Player", unreal.SkeletalMeshActor,
        unreal.Vector(-850.0, 0.0, 560.0),
        unreal.Rotator(0.0, 0.0, 0.0), "OceanJump/Player")
    skeletal_component = component(player, unreal.SkeletalMeshComponent)
    if not skeletal_component:
        raise RuntimeError("Manny SkeletalMeshComponent is missing")
    try:
        skeletal_component.set_skeletal_mesh_asset(skeletal_mesh)
    except Exception:
        set_prop(skeletal_component, "skeletal_mesh_asset", skeletal_mesh)
    set_prop(skeletal_component, "mobility", unreal.ComponentMobility.MOVABLE)
    try:
        skeletal_component.set_collision_enabled(
            unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    return player


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
        "platform_a": make_textured_material(
            "M_OJ_PlatformA_V3", (0.035, 0.12, 0.24, 1.0), 0.22, 0.72,
            "/Engine/EditorResources/TilePatine_D.TilePatine_D",
            "/Engine/EditorResources/TilePatine_N.TilePatine_N", 7.0),
        "platform_b": make_textured_material(
            "M_OJ_PlatformB_V3", (0.32, 0.055, 0.02, 1.0), 0.24, 0.68,
            "/Engine/EditorResources/TilePatine_D.TilePatine_D",
            "/Engine/EditorResources/TilePatine_N.TilePatine_N", 7.0),
        "ocean": make_ocean_material(),
        "far_ocean": make_material(
            "M_OJ_FarOcean_V5", (0.001, 0.015, 0.045, 1.0), 0.35, 0.0,
            emissive=(0.0, 0.045, 0.12, 1.0)),
    }
    build_environment()
    build_ocean(materials["ocean"], materials["far_ocean"])
    build_platforms(materials)
    build_player()
    build_cameras()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    log("Build complete: L_OceanJump saved")


try:
    build()
except Exception as exc:
    unreal.log_error(f"[OceanJump] Build failed: {exc}")
    raise
