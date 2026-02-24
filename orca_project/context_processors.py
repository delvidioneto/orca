"""Context processors do Orca."""
from .version import get_version


def orca_version(request):
    """Injeta orca_version em todos os templates."""
    return {"orca_version": get_version()}
