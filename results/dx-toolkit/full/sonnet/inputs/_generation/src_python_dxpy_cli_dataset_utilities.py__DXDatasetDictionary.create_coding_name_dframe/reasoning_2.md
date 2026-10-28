The function uses `pd` which is a module global in the repository's module. I need to set it on the repository's module: `import dxpy.cli.dataset_utilities as du; du.pd = pd`.

Let me add that import at module level.