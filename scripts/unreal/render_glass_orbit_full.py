"""Render the complete 20-second Glass Orbit sequence at 720p/30 fps."""

import unreal


SEQUENCE_PATH = "/Game/OrbitalGlassLab/Cinematics/LS_GlassOrbit"
MAP_PATH = "/Game/OrbitalGlassLab/Maps/L_GlassOrbit"
OUTPUT_DIR = "D:/UnrealRenders/OrbitalGlassLab/final_frames"


def log(message):
    unreal.log(f"[OrbitalGlassFullRender] {message}")


def configure_job(job):
    config = job.get_configuration()

    output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    output.set_editor_property("output_directory", unreal.DirectoryPath(path=OUTPUT_DIR))
    output.set_editor_property("file_name_format", "glass_orbit_{frame_number}")
    output.set_editor_property("output_resolution", unreal.IntPoint(1280, 720))
    output.set_editor_property("override_existing_output", True)
    output.set_editor_property("zero_pad_frame_numbers", 4)
    output.set_editor_property("use_custom_playback_range", True)
    output.set_editor_property("custom_start_frame", 0)
    output.set_editor_property("custom_end_frame", 599)
    output.set_editor_property("output_frame_step", 1)

    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    png = config.find_or_add_setting_by_class(
        unreal.MoviePipelineImageSequenceOutput_PNG)
    try:
        png.set_editor_property("write_alpha", False)
    except Exception:
        pass

    aa = config.find_or_add_setting_by_class(
        unreal.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("spatial_sample_count", 1)
    aa.set_editor_property("temporal_sample_count", 1)


def render():
    if not unreal.load_asset(SEQUENCE_PATH):
        raise RuntimeError(f"Missing sequence: {SEQUENCE_PATH}")

    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    if subsystem.is_rendering():
        raise RuntimeError("Movie Render Pipeline is already rendering")

    queue = subsystem.get_queue()
    queue.delete_all_jobs()
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    if not job:
        raise RuntimeError("Unable to allocate Movie Render Pipeline job")
    job.set_editor_property("job_name", "Glass Orbit - 720p master")
    job.set_editor_property(
        "sequence", unreal.SoftObjectPath(SEQUENCE_PATH + ".LS_GlassOrbit"))
    job.set_editor_property(
        "map", unreal.SoftObjectPath(MAP_PATH + ".L_GlassOrbit"))
    configure_job(job)
    log(f"Starting 600-frame master -> {OUTPUT_DIR}")
    executor = subsystem.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
    if not executor:
        raise RuntimeError("Unable to start the PIE render executor")


try:
    render()
except Exception as exc:
    unreal.log_error(f"[OrbitalGlassFullRender] Render failed: {exc}")
    raise
