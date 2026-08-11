"""Render four quick Ocean Jump validation frames."""

import unreal

SEQUENCE_PATH = "/Game/OrbitalGlassLab/Cinematics/LS_OceanJump"
MAP_PATH = "/Game/OrbitalGlassLab/Maps/L_OceanJump"
OUTPUT_DIR = "D:/UnrealRenders/OrbitalGlassLab/ocean_validation"


def render():
    if not unreal.load_asset(SEQUENCE_PATH):
        raise RuntimeError(f"Missing sequence: {SEQUENCE_PATH}")
    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    if subsystem.is_rendering():
        raise RuntimeError("Movie Render Pipeline is already rendering")
    queue = subsystem.get_queue()
    queue.delete_all_jobs()
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.set_editor_property("job_name", "Ocean Jump - validation stills")
    job.set_editor_property(
        "sequence", unreal.SoftObjectPath(SEQUENCE_PATH + ".LS_OceanJump"))
    job.set_editor_property(
        "map", unreal.SoftObjectPath(MAP_PATH + ".L_OceanJump"))
    config = job.get_configuration()
    output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    output.set_editor_property("output_directory", unreal.DirectoryPath(path=OUTPUT_DIR))
    output.set_editor_property("file_name_format", "ocean_jump_{frame_number}")
    output.set_editor_property("output_resolution", unreal.IntPoint(960, 540))
    output.set_editor_property("override_existing_output", True)
    output.set_editor_property("zero_pad_frame_numbers", 4)
    output.set_editor_property("use_custom_playback_range", True)
    output.set_editor_property("custom_start_frame", 0)
    output.set_editor_property("custom_end_frame", 449)
    # 0, 110, 220, 330 and 440 cover every cut, including the final orbit.
    output.set_editor_property("output_frame_step", 110)
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("spatial_sample_count", 1)
    aa.set_editor_property("temporal_sample_count", 1)
    executor = subsystem.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
    if not executor:
        raise RuntimeError("Unable to start validation render")


try:
    render()
except Exception as exc:
    unreal.log_error(f"[OceanJumpRender] Validation failed: {exc}")
    raise
