from aws_cdk import App
from k9.config import load_stage_config
from k9.stack import K9ApiStack

app = App()

stage = app.node.try_get_context("stage") or "dev"
config = load_stage_config(app, stage)

K9ApiStack(app, f"K9Api{stage.capitalize()}Stack", config=config)

app.synth()
