from aws_cdk import App
from k9.config import StageConfig
from k9.stack import create_stack

if __name__ == "__main__":
    app = App()
    stage = str(app.node.get_context("stage"))
    config = StageConfig.model_validate(app.node.get_context(stage) | {"stage": stage})
    create_stack(app, config)
    app.synth()
