print(f'Loading {__file__}')

import nslsii
import os

try:
    os.environ.pop('TILED_API_KEY')
except KeyError:
    pass


from tiled.client import from_profile
from databroker import Broker
from redis_json_dict import RedisJSONDict

from IPython import get_ipython
from IPython.terminal.prompts import Prompts, Token

class ProposalIDPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [
            (
                Token.Prompt,
                f"{RE.md.get('data_session', 'N/A')} [",
            ),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, "]: "),
        ]

ip = get_ipython()
ip.prompts = ProposalIDPrompt(ip)

# Configure a Tiled writing client
tiled_writing_client = from_profile("nsls2", api_key=os.environ["TILED_BLUESKY_WRITING_API_KEY_CMS"])["cms"]["raw"]
tiled_writing_client.context.http_client.headers['tiled-qos'] = 'acquisition'

class TiledInserter:

    name = 'cms'
    def insert(self, name, doc):
        ATTEMPTS = 20
        error = None
        for _ in range(ATTEMPTS):
            try:
                tiled_writing_client.post_document(name, doc)
            except Exception as exc:
                print("Document saving failure:", repr(exc))
                error = exc
            else:
                break
            time.sleep(2)
        else:
            # Out of attempts
            raise error

tiled_inserter = TiledInserter()

nslsii.configure_base(get_ipython().user_ns,
                      tiled_inserter,
                      publish_documents_with_kafka=True,
                      redis_url="xf11bm-cms-redis1.nsls2.bnl.gov",
                      redis_port=6380,
                      redis_ssl=True)

print("Initializing Tiled reading client...\nMake sure you check for duo push.")
tiled_reading_client = cat = from_profile("nsls2", username=None)["cms"]["raw"]
tiled_reading_client.context.http_client.headers['tiled-qos'] = 'acquisition'
mig = from_profile("nsls2", username=None)["cms/migration"]

db = Broker(tiled_reading_client)  # Keep for backcompatibility with older code that uses databroker

from pyOlog.ophyd_tools import *

# Increase the timeout for EpicsSignal.get()
# This beamline was occasionally getting ReadTimeoutErrors
import ophyd
ophyd.signal.EpicsSignalBase.set_defaults(timeout=120, connection_timeout=10.0)

#this replaces RE() <
from bluesky.utils import register_transform
register_transform('RE', prefix='<')

# Setup the path to the secure assets folder for the current proposal
def proposal_path():
    return f"/nsls2/data/cms/proposals/{RE.md['cycle']}/{RE.md['data_session']}/"

def assets_path():
    return proposal_path() + "assets/"

def bluesky_path(file=None):
    if file is not None:
        return f"/nsls2/data3/cms/shared/config/bluesky/profile_collection/startup/{file}"
    else:
        return f"/nsls2/data3/cms/shared/config/bluesky/profile_collection/startup/"

#swap users 
from nslsii.sync_experiment import switch_redis_proposal
def proposal_swap(proposal_id, username=None):
    if username == None:
        username=RE.md['username']
    RE.md = switch_redis_proposal(proposal_id, beamline='cms', username=username)    
    # # Ensure tiled_access_tags is always a list
    # if tags := RE.md.get('tiled_access_tags'):
    #     if isinstance(tags, str):
    #         tags = [tags]
    #     RE.md['tiled_access_tags'] = tags