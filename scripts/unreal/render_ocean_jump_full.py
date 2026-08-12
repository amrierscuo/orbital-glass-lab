"""Render the complete 15-second Ocean Jump sequence at 720p/30 fps."""

import unreal

SEQUENCE_PATH = "/Game/OrbitalGlassLab/Cinematics/LS_OceanJump"
MAP_PATH = "/Game/OrbitalGlassLab/Maps/L_OceanJump"
OUTPUT_DIR = "D:/UnrealRenders/OrbitalGlassLab/ocean_final_frames_v2"
_executor = None


def log(message):
    unreal.log(f"[OceanJumpRender] {message}")


def on_render_finished(executor, success):
    log(f"Master finished; success={success}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def render():
    global _executor
    if not unreal.load_asset(SEQUENCE_PATH):
        raise RuntimeError(f"Missing sequence: {SEQUENCE_PATH}")
    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    if subsystem.is_rendering():
        raise RuntimeError("Movie Render Pipeline is already rendering")
    queue = subsystem.get_queue()
    queue.delete_all_jobs()
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.set_editor_property("job_name", "Ocean Jump - 720p master")
    job.set_editor_property(
        "sequence", unreal.SoftObjectPath(SEQUENCE_PATH + ".LS_OceanJump"))
    job.set_editor_property(
        "map", unreal.SoftObjectPath(MAP_PATH + ".L_OceanJump"))
    config = job.get_configuration()
    output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    output.set_editor_property("output_directory", unreal.DirectoryPath(path=OUTPUT_DIR))
    output.set_editor_property("file_name_format", "ocean_jump_v2_{frame_number}")
    output.set_editor_property("output_resolution", unreal.IntPoint(1280, 720))
    output.set_editor_property("override_existing_output", True)
    output.set_editor_property("zero_pad_frame_numbers", 4)
    output.set_editor_property("use_custom_playback_range", True)
    output.set_editor_property("custom_start_frame", 0)
    output.set_editor_property("custom_end_frame", 450)
    output.set_editor_property("output_frame_step", 1)
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("spatial_sample_count", 1)
    aa.set_editor_property("temporal_sample_count", 1)
    log(f"Starting 450-frame master -> {OUTPUT_DIR}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    _executor = subsystem.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
    if not _executor:
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        raise RuntimeError("Unable to start full render")
    _executor.on_executor_finished_delegate.add_callable(on_render_finished)


try:
    render()
except Exception as exc:
    unreal.log_error(f"[OceanJumpRender] Full render failed: {exc}")
    raise
