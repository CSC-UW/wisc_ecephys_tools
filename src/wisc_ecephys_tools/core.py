from ecephys.wne import sglx
from wisc_ecephys_tools import projects


def get_shared_project() -> sglx.SGLXProject:
    return projects.get_sglx_project("shared")
