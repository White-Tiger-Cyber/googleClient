from . import command

@command("pwd", "pwd  - print current path")
def handle(ctx, args):
    print(" / ".join(ctx.breadcrumb))
