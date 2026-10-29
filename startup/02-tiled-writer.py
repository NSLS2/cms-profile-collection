import numpy
import os

from bluesky_tiled_plugins import TiledWriter
from bluesky.callbacks.buffer import BufferingWrapper
from tiled.client import from_uri


# Mapping from spec to mimetype for use in TiledWriter
# TODO: Only keep the necessary specs here
MIMETYPE_LOOKUP = {
        "AD_TIFF": "multipart/related;type=image/tiff",
        "HDF5": "application/x-hdf5",
    }


# Define document-specific patches to be applied before sending them to TiledWriter
def patch_resource(doc):

    kwargs = doc.get("resource_kwargs", {})

    # Fix the resource path
    root = doc.get("root", "")
    if not doc["resource_path"].startswith(root):
        doc["resource_path"] = os.path.join(root, doc["resource_path"])
    doc["root"] = ""
    doc["resource_path"] = doc["resource_path"].replace("/nsls2/data3/cms", "/nsls2/data/cms")

    if doc.get("spec") in ["AD_TIFF"]:
        kwargs["template"] = "/" + kwargs["template"].lstrip("/")    # Ensure leading slash
        kwargs["join_method"] = "concat"  # "stack"

    return doc


def patch_descriptor(doc):
    for desc in doc['data_keys'].values():
        if len(desc["shape"]) < 3:
            desc["shape"] = [1]*(3-len(desc["shape"])) + desc["shape"]

    if 'pilatus800_image' in doc['data_keys']:
        desc = doc['data_keys']['pilatus800_image']
        desc.setdefault("dtype_str", "<i4")
        shape = desc['shape']
        if shape[-1] == 0:
            shape[-1] = 1
            desc['shape'] = shape[::-1]

    # Ensure dtype_str has the proper numpy format (to pass the EventModel validator)
    for key, val in doc["data_keys"].items():
        if "dtype_str" in val:
            val["dtype_str"] = numpy.dtype(val["dtype_str"]).str
        val["shape"] = tuple(map(lambda x: max(x, 0), val.get("shape", [])))

    return doc


# Initialize the Tiled client and the TiledWriter
api_key = os.environ.get("TILED_BLUESKY_WRITING_API_KEY_CMS")
tiled_writing_client_sql = from_uri("https://tiled.nsls2.bnl.gov", api_key=api_key)['cms/migration']
tiled_writing_client_sql.context.http_client.headers['tiled-qos'] = 'acquisition'

tw = TiledWriter(client = tiled_writing_client_sql,
                 backup_directory=f"{TILED_BACKUP_ROOT}/sql",   # NOTE: Pick a suitable backup directory
                 patches = {"descriptor": patch_descriptor,
                            "resource": patch_resource},
                 spec_to_mimetype = MIMETYPE_LOOKUP,
                 batch_size=10000   # NOTE: Set to 1 to disable batching
                 )

# Thread-safe wrapper for TiledWriter
tw = BufferingWrapper(tw)

# Subscribe the TiledWriter
RE.md["tiled_access_tags"] = (RE.md["data_session"],)
# RE.subscribe(tw)
