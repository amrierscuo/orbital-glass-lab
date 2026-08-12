"""Render four fast validation frames from LS_GlassOrbit with UE 5.8 MRQ.

The contact frames validate camera cuts and the day/night lighting before the
full 600-frame render. Output is written to D:/UnrealRenders/OrbitalGlassLab.
"""

import unreal


SEQUENCE_PATH = "/Game/OrbitalGlassLab/Cinematics/LS_GlassOrbit"
MAP_PATH = "/Game/OrbitalGlassLab/Maps/L_GlassOrbit"
OUTPUT_DIR = "D:/UnrealRenders/OrbitalGlassLab/validation_v2"
_executor = None


def log(message):
    unreal.log(f"[OrbitalGlassRender] {message}")


def on_render_finished(executor, success):
    log(f"Validation render finished; success={success}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def configure_job(job):
    config = job.get_configuration()

    output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    output.set_editor_property("output_directory", unreal.DirectoryPath(path=OUTPUT_DIR))
    output.set_editor_property("file_name_format", "glass_orbit_v2_{frame_number}")
    output.set_editor_property("output_resolution", unreal.IntPoint(1280, 720))
    output.set_editor_property("override_existing_output", True)
    output.set_editor_property("zero_pad_frame_numbers", 4)
    output.set_editor_property("use_custom_playback_range", True)
    output.set_editor_property("custom_start_frame", 0)
    output.set_editor_property("custom_end_frame", 599)
    # UE 5.8 can directly skip source frames. 150 produces frames near
    # 0 s, 5 s, 10 s and 15 s from the 20-second sequence.
    output.set_editor_property("output_frame_step", 120)

    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    png = config.find_or_add_setting_by_class(
        unreal.MoviePipelineImageSequenceOutput_PNG)
    try:
        png.set_editor_property("write_alpha", False)
    except Exception:
        pass

    # Keep the validation pass deliberately fast. The final render will use
    # more samples once the framing has been approved.
    aa = config.find_or_add_setting_by_class(
        unreal.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("spatial_sample_count", 1)
    aa.set_editor_property("temporal_sample_count", 1)


def render():
    global _executor
    sequence = unreal.load_asset(SEQUENCE_PATH)
    if not sequence:
        raise RuntimeError(f"Missing sequence: {SEQUENCE_PATH}")

    # The editor queue uses a PIE executor. Unlike the runtime subsystem, this
    # launches the temporary game world required by MRQ while the editor is
    # open and then returns to the current level automatically.
    subsystem = unreal.get_editor_subsystem(
        unreal.MoviePipelineQueueSubsystem)
    if subsystem.is_rendering():
        raise RuntimeError("Movie Render Pipeline is already rendering")

    queue = subsystem.get_queue()
    queue.delete_all_jobs()
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    if not job:
        raise RuntimeError("Unable to allocate Movie Render Pipeline job")
    job.set_editor_property("job_name", "Glass Orbit - validation stills")
    job.set_editor_property(
        "sequence", unreal.SoftObjectPath(SEQUENCE_PATH + ".LS_GlassOrbit"))
    job.set_editor_property(
        "map", unreal.SoftObjectPath(MAP_PATH + ".L_GlassOrbit"))
    configure_job(job)
    log(f"Starting four validation frames -> {OUTPUT_DIR}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    _executor = subsystem.render_queue_with_executor(
        unreal.MoviePipelinePIEExecutor)
    if not _executor:
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        raise RuntimeError("Unable to start the PIE render executor")
    _executor.on_executor_finished_delegate.add_callable(on_render_finished)


try:
    render()
except Exception as exc:
    unreal.log_error(f"[OrbitalGlassRender] Validation render failed: {exc}")
    raise
