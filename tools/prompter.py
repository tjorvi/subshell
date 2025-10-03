from termrec import terminal

async def capture_session(user, shell, script, env_vars=None):
    output = []

    if shell == 'fish':
        shellArgs = [
            '-e', 'SHELL=fish',
            '--entrypoint', '/usr/bin/fish'
        ]
    else:
        shellArgs = []

    # use docker instead of container because container adds startup noise. We'd have to run the capture
    # from within the container to avoid that.
    CONTAINER = 'docker'
    PROJECT_ROOT = '/tmp/subshell-demo'
    cmd = [
        CONTAINER, 'run', '--rm', '-it',
        '--user', user,
        # '-v', './dist/bin:/dbin',
        # '-e', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/dbin',
        '-e', f'SUBSHELL_ROOT={PROJECT_ROOT}',
        '-w', PROJECT_ROOT,
        '-h', 'demo',
        *shellArgs,
    ]
    
    # Add environment variables if provided
    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(['-e', f'{key}={value}'])
    
    cmd.append('subshell-demo-tools')

    smBracketedPaste = b'\x1b[?2004h'  # Bracketed paste mode enable

    def record(c):
        output.append(c)

    async with terminal(cmd, onOutput=record) as term:
        if not await term.waitForOutput(smBracketedPaste):  # Enable bracketed paste mode - indicates shell waiting for input
            raise ValueError("Timeout waiting for initial prompt (bracketed paste enable sequence)", b''.join(output))
        if not await term.waitForStability(0.7):
            raise ValueError("Timeout waiting for stable output", b''.join(output))

        for command in script:
            await term.send(command)
            if not await term.waitForOutput(smBracketedPaste):
                raise ValueError("Timeout waiting for initial prompt (bracketed paste enable sequence)", b''.join(output))
            if not await term.waitForStability(0.7):
                raise ValueError("Timeout waiting for stable output", b''.join(output))

    return b''.join(output)


if __name__ == "__main__":
    # user = 'demo-oh-my-zsh-p10k'
    user = 'demo-blankline'
    shell = 'fish'
    test_script = [
        'subshell',
        'cd demo-subdir',
        'cd /tmp/outside',
    ]
    import asyncio
    output = asyncio.run(capture_session(user, shell, test_script))

    print(output.decode('utf-8'))
