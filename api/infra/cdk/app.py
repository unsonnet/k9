from aws_cdk import App
from k9.config import StageConfig
from k9.stack import create_stack

if __name__ == "__main__":
    app = App()
    config = StageConfig.from_context(app.node.get_all_context())
    create_stack(app, config)
    app.synth()
