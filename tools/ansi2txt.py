import sys


class Text:
    __match_args__ = ('text',)
    
    def __init__(self, text: str):
        self.text = text

    def __repr__(self):
        return f'Text({self.text!r})'
        
modes = {
    1: 'application cursor keys',
    25: 'show cursor',
    2004: 'bracketed paste',
}

sgrAttributes = {
    0: 'reset',
    1: 'bold',
    2: 'faint',
    3: 'italic',
    4: 'underline',
    5: 'blink slow',
    6: 'blink rapid',
    7: 'reverse',
    8: 'conceal',
    9: 'strikethrough',
}
sgrColors = {
    0: 'black',
    1: 'red',
    2: 'green',
    3: 'yellow', 
    4: 'blue',
    5: 'magenta',
    6: 'cyan',
    7: 'white',
}

def CSI(params: list[int]):
    [*ps, final] = params

    if False: pass

    elif final == 0x41:
        x = bytes(ps).decode('utf-8')
        if x == '':
            return ('cursor up', 1)
        else:
            return ('cursor up', int(x))

    elif final == 0x42:
        x = bytes(ps).decode('utf-8')
        if x == '':
            return ('cursor down', 1)
        else:
            return ('cursor down', int(x))

    elif final == 0x43:
        x = bytes(ps).decode('utf-8')
        if x == '':
            return ('cursor forward', 1)
        else:
            return ('cursor forward', int(x))

    elif final == 0x44:
        x = bytes(ps).decode('utf-8')
        if x == '':
            return ('cursor backward', 1)
        else:
            return ('cursor backward', int(x))
        
    elif final == 0x48:
        x = bytes(ps).decode('utf-8').split(';')
        if x == ['']:
            return ('cursor position', 1, 1)
        elif len(x) == 2:
            row = int(x[0]) if x[0] != '' else 1
            col = int(x[1]) if x[1] != '' else 1
            return ('cursor position', row, col)
        else:
            raise ValueError('Grokking', ps, x)

    elif final == 0x4a:
        x = bytes(ps).decode('utf-8')
        if x == '' or x == '0':
            return ('CSI', 'erase screen', 'to end')
        elif x == '1':
            return ('CSI', 'erase screen', 'to start')
        elif x == '2':
            return ('CSI', 'erase screen', 'to all')
        elif x == '3':
            return ('CSI', 'erase screen', 'to all and scrollback')
        else:
            raise ValueError('Grokking', ps, x)
        
    elif final == 0x4b:
        x = bytes(ps).decode('utf-8')
        if x == '' or x == '0':
            return ('CSI', 'erase line', 'to end')
        elif x == '1':
            return ('CSI', 'erase line', 'to start')
        elif x == '2':
            return ('CSI', 'erase line', 'to all')
        else:
            raise ValueError('Grokking', ps, x)

    elif final == 0x68:  # 'h' SM
        x = bytes(ps).decode('utf-8')
        if x.startswith('?'):
            n = int(x[1:])
            if n not in modes:
                raise ValueError('Grokking', ps, x)
            mode = modes[n]
            return ('CSI', 'SM', 'DEC Private Mode', mode)
        else:
            raise ValueError('Grokking', ps, x)
    if final == 0x6c:  # 'l' RM
        x = bytes(ps).decode('utf-8')
        if x.startswith('?'):
            mode = modes[int(x[1:])]
            return ('CSI', 'RM', 'DEC Private Mode', mode)
        else:
            raise ValueError('Grokking', ps, x)

    elif final == 0x6d:  # 'm' SGR
        xs = bytes(ps).decode('utf-8').split(';')
        bits = []
        if not xs:
            bits.append('reset')

        while xs:
            x = xs.pop(0)
            if x == '':
                bits.append('reset')
            elif x == '>4':
                bits.append('xterm set key-modifier option')
            elif len(x) == 1 or (len(x) == 2 and x.startswith('0')):
                attribute = sgrAttributes[int(x)]
                bits.append(('set', attribute))
            elif int(x) >= 20 and int(x) <= 29:
                attribute = sgrAttributes[int(x) % 10]
                bits.append(('cancel', attribute))
            elif int(x) >= 30 and int(x) <= 37:
                bits.append(('foreground', sgrColors[int(x) % 10]))
            elif x == '38':
                pcount = xs.pop(0)
                if pcount == '2':
                    r = xs.pop(0)
                    g = xs.pop(0)
                    b = xs.pop(0)
                    bits.append(('true colour foreground', (r,g,b)))
                elif pcount == '5':
                    index = xs.pop(0)
                    bits.append(('true colour foreground', index))
                else:
                    raise ValueError('Grokking', ps, x, pcount)
            elif x == '39':
                bits.append('default foreground')
            elif int(x) >= 40 and int(x) <= 47:
                bits.append((f'background', sgrColors[int(x) % 10]))
            elif x == '48':
                pcount = xs.pop(0)
                if pcount == '2':
                    r = xs.pop(0)
                    g = xs.pop(0)
                    b = xs.pop(0)
                    bits.append(('true colour background', (r,g,b)))
                elif pcount == '5':
                    index = xs.pop(0)
                    bits.append(('true colour background', index))
                else:
                    raise ValueError('Grokking', ps, x, pcount)
            elif x == '49':
                bits.append('default background')
            elif int(x) >= 90 and int(x) <= 97:
                bits.append(('bright foreground', sgrColors[int(x) % 10]))
            elif int(x) >= 100 and int(x) <= 107:
                bits.append(('bright background', sgrColors[int(x) % 10]))
            else:
                raise ValueError('Grokking', ps, x)
        return ('CSI', 'SGR', bits)
        
    elif final == 0x75:
        x = bytes(ps).decode('utf-8')
        if x == '':
            return ('CSI', 'save cursor')
        elif x == '=0':
            return ('CSI', 'keyboard transmit mode [linux]', 'normal')
        elif x == '=1':
            return ('CSI', 'keyboard transmit mode [linux]', 'application')
        elif x == '=2':
            return ('CSI', 'keyboard transmit mode [linux]', 'vt')
        elif x == '=5':
            return ('CSI', 'set F5 string')
        raise ValueError(f'Unexpected CSI u params: {ps}', x)
        
    raise ValueError(f'Unexpected CSI final: {final:02x}')

def OSC(params: list[int]):
    x = bytes(params).decode('utf-8')
    [ps, *pt] = x.split(';')

    if False: pass
    elif ps == '0' and len(pt) == 1: return ('icon+title', pt)
    elif ps == '1' and len(pt) == 1: return ('icon', pt)
    elif ps == '2' and len(pt) == 1: return ('title', pt)
    elif ps == '7' and len(pt) == 1: return ('cwd', pt)
    elif ps == '133' and pt[0] == 'A': return ('new-command and prompt-mode', pt[1:])
    elif ps == '133' and pt[0] == 'B': return ('end-prompt, start-input', pt[1:])
    elif ps == '133' and pt[0] == 'C': return ('end-input, start-output', pt[1:])
    elif ps == '133' and pt[0] == 'D': return ('end-current-command', pt[1:])
    
    raise ValueError(f'Grokking OSC {ps} {pt}')

def G(n: int):
    return f'G({n})'

def KeypadMode(mode: str):
    return f'KeypadMode({mode})'


def parse(inputBytes):
    inputBytes = list(reversed(inputBytes)) # pop(0) could be used instead
    blocks = []
    def emit(block):
        blocks.append(block)
        # print(block)

    ofs = 0
    line = 1
    col = 1
    consumed = []
    originalInput = list(reversed(inputBytes))
    def consume():
        b = inputBytes.pop()
        nonlocal ofs, line, col
        ofs += 1
        if b == 10:  # \n
            line += 1
            col = 1
        else: col += 1
        consumed.append(b)
        return b

    checkpoint_ofs = 0
    checkpoint_line = 1
    checkpoint_col = 1
    def checkpoint():
        nonlocal checkpoint_ofs, checkpoint_line, checkpoint_col
        checkpoint_ofs = ofs
        checkpoint_line = line
        checkpoint_col = col

    def position():
        return f'line {line}, col {col}, byte {ofs}, from {checkpoint_ofs} (line {checkpoint_line}, col {checkpoint_col}), text {bytes(originalInput[checkpoint_ofs:ofs]).decode("utf-8", errors="replace").replace('\x1b', '<ESC>')!r}'

    while inputBytes:
        checkpoint()
        b = consume()

        if b == 0x1b:
            try:
                e = consume()

                if e == 0x5b:
                    csi = []
                    while True:
                        c = consume()
                        csi.append(c)
                        if 0x40 <= c <= 0x7e:
                            break

                    emit(CSI(csi))

                elif e == 0x5d:
                    # OSC (Operating System Command)
                    osc = []
                    while True:
                        c = consume()
                        osc.append(c)
                        if c == 0x07:  # BEL
                            break
                        if len(osc) >= 2 and osc[-2] == 0x1b and osc[-1] == 0x5c:  # ST
                            break
                    emit(OSC(osc))

                elif e == 0x28:
                    p = consume()
                    if p == 0x42:
                        emit(G(0))  # ASCII
                    elif p == 0x4d:
                        emit(G(1))  # DEC Special Character and Line Drawing Set
                    else:
                        raise ValueError(f'Unexpected byte after ESC (: {p:02x}')
                    
                elif e == 0x3d:
                    emit(KeypadMode('application'))

                elif e == 0x3e:
                    emit(KeypadMode('numeric'))

                else:
                    raise ValueError(f'Unexpected byte after ESC: {e:02x}')
            except:
                print(f'Error parsing at {position()}', file=sys.stderr)
                raise
        else:
            text = [b]
            while inputBytes and inputBytes[-1] != 0x1b:
                text.append(consume())
            emit(Text(bytearray(text).decode('utf-8')))


    return blocks

class Pos:
    def __init__(self):
        self.row = 1
        self.col = 1

class Char:
    def __init__(self, char: str, foreground = None, background = None, attributes = None):
        self.char = char
        self.foreground = foreground
        self.background = background
        self.attributes = attributes or set()

    def __repr__(self):
        if not self.char:
            return '(nil)'
        if self.char and self.char[0] < ' ':
            return f'\\x{ord(self.char):02x}'
        else:
            return self.char

def render(blocks):
    p = Pos()

    lines = [[Char('')]]
    foreground = None
    background = None
    attributes = set()

    def setCursor(row: int, col: int):
        p.row = row
        p.col = col
        if p.row < 1: p.row = 1
        if p.col < 1: p.col = 1
        while len(lines) < p.row:
            lines.append([Char('')])
        while len(lines[p.row - 1]) < p.col:
            lines[p.row - 1].append(Char(' '))

    def addText(text: str):
        for char in text:
            if char == '\n':
                setCursor(p.row + 1, 1)
            elif char == '\r':
                setCursor(p.row, 1)
            elif char == '\t':
                while (p.col - 1) % 8 != 7:
                    addText(' ')
            elif char == '\b':
                setCursor(p.row, p.col - 1)
            else:
                setCursor(p.row, p.col + 1)
                # we call setCursor first to make sure the buffers are big enough
                # but then we have to subtract 2, 1 for the 1-based indexing and
                # 1 for the fact that we already advanced the cursor
                lines[p.row - 1][p.col - 2] = Char(char, foreground, background, attributes)

    def eraseLineToEnd():
        if p.row - 1 < len(lines):
            lines[p.row - 1] = lines[p.row - 1][:p.col - 1]

    def eraseScreenToEnd():
        eraseLineToEnd()
        del lines[p.row:]

    def eraseScreen():
        del lines[:]
        lines.append([''])
        setCursor(1, 1)

    def handleSGR(bits):
        nonlocal foreground, background, attributes
        for bit in bits:
            match bit:
                case 'reset': 
                    foreground = None
                    background = None
                    attributes.clear()
                case ('set', 'reset'): 
                    foreground = None
                    background = None
                    attributes.clear()
                case 'default foreground': attributes.add('bright'); foreground = None
                case 'default background': attributes.add('bright'); background = None
                case ('true colour foreground', n): attributes.add('bright'); foreground = n
                case ('foreground', color): attributes.discard('bright'); foreground = color
                case ('background', color): attributes.discard('bright'); background = color
                case ('bright foreground', color): attributes.add('bright'); foreground = color
                case ('bright background', color): attributes.add('bright'); background = color
                case ('set', attribute): attributes.add(attribute)
                case ('cancel', attribute): attributes.discard(attribute)

                case 'xterm set key-modifier option': pass
                case _: raise ValueError('Grokking SGR bit', bit)

    for block in blocks:
        match block:
            case ('icon', _): pass
            case ('icon+title', _): pass
            case ('title', _): pass
            case ('CSI', 'RM', *_): pass
            case ('CSI', 'SM', *_): pass
            case ('CSI', 'SGR', bits): handleSGR(bits)
            case ('CSI', 'keyboard transmit mode [linux]', *_): pass
            case ('CSI', 'erase line', 'to end'): eraseLineToEnd()
            case ('CSI', 'erase line', 'x'): pass
            case ('CSI', 'erase screen', 'to end'): eraseScreenToEnd()
            case ('CSI', 'erase screen', 'to all'): eraseScreen()
            case ('CSI', 'erase screen', 'to all and scrollback'): eraseScreen()
            case ('CSI', 'set F5 string', *_): pass
            case ('cursor position', row, col): setCursor(row, col)
            case ('cursor up', n): setCursor(p.row - n, p.col)
            case ('cursor down', n): setCursor(p.row + n, p.col)
            case ('cursor forward', n): setCursor(p.row, p.col + n)
            case ('cursor backward', n): setCursor(p.row, p.col - n)
            case ('cwd', *_): pass
            case 'G(0)': pass
            case 'KeypadMode(numeric)': pass
            case 'KeypadMode(application)': pass
            case Text(text):
                addText(text)
            case ('new-command and prompt-mode', _): pass
            case ('end-prompt, start-input', _): pass
            case ('end-input, start-output', _): pass
            case ('end-current-command', _): pass
            case _: raise NotImplementedError(block)
    
    return lines

# Aesthetic color themes for SVG rendering
COLOR_THEMES = {
    'dracula': {
        'background': '#282a36',
        'foreground': '#f8f8f2',
        'black': '#21222c',
        'red': '#ff5555',
        'green': '#50fa7b',
        'yellow': '#f1fa8c',
        'blue': '#bd93f9',
        'magenta': '#ff79c6',
        'cyan': '#8be9fd',
        'white': '#f8f8f2',
    },
    'nord': {
        'background': '#2e3440',
        'foreground': '#d8dee9',
        'black': '#3b4252',
        'red': '#bf616a',
        'green': '#a3be8c',
        'yellow': '#ebcb8b',
        'blue': '#81a1c1',
        'magenta': '#b48ead',
        'cyan': '#88c0d0',
        'white': '#e5e9f0',
    },
    'github-dark': {
        'background': '#0d1117',
        'foreground': '#c9d1d9',
        'black': '#21262d',
        'red': '#f85149',
        'green': '#7ee787',
        'yellow': '#f2cc60',
        'blue': '#79c0ff',
        'magenta': '#d2a8ff',
        'cyan': '#39d0d6',
        'white': '#f0f6fc',
    },
    'catppuccin-mocha': {
        'background': '#1e1e2e',
        'foreground': '#cdd6f4',
        'black': '#45475a',
        'red': '#f38ba8',
        'green': '#a6e3a1',
        'yellow': '#f9e2af',
        'blue': '#89b4fa',
        'magenta': '#cba6f7',
        'cyan': '#94e2d5',
        'white': '#f5e0dc',
    }
}

def ansi_256_to_rgb(index):
    """Convert ANSI 256 color index to RGB tuple"""
    index = int(index)
    
    if index < 16:
        # Standard 16 colors - these should use theme colors
        basic_colors = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
        if index < 8:
            return basic_colors[index]
        else:
            # Bright colors (8-15)
            return basic_colors[index - 8]
    
    elif index < 232:
        # 216 color cube (16-231)
        index -= 16
        r = index // 36
        g = (index % 36) // 6
        b = index % 6
        
        # Convert to RGB values: 0→0x00, 1→0x5f, 2→0x87, 3→0xaf, 4→0xd7, 5→0xff
        rgb_values = [0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff]
        return (rgb_values[r], rgb_values[g], rgb_values[b])
    
    else:
        # Grayscale colors (232-255)
        gray_level = (index - 232) * 10 + 8
        return (gray_level, gray_level, gray_level)

def get_themed_color(color, theme='dracula'):
    """Convert basic color names to themed hex colors"""
    if not color:
        return None
    
    color_map = COLOR_THEMES.get(theme, COLOR_THEMES['dracula'])
    
    # Handle RGB tuples for true color
    if isinstance(color, tuple) and len(color) == 3:
        r, g, b = color
        return f'rgb({r},{g},{b})'
    
    # Handle ANSI 256 color indices
    if isinstance(color, str) and color.isdigit():
        ansi_color = ansi_256_to_rgb(color)
        
        # If it's a basic color name, use theme color
        if isinstance(ansi_color, str):
            return color_map.get(ansi_color.lower(), ansi_color)
        
        # If it's an RGB tuple, convert to CSS rgb()
        if isinstance(ansi_color, tuple):
            r, g, b = ansi_color
            return f'rgb({r},{g},{b})'
    
    # Handle basic color names
    if isinstance(color, str):
        return color_map.get(color.lower(), color)
    
    return color

def txt(buffer):
    return '\n'.join(''.join(c.char for c in line) for line in buffer).rstrip() + '\n'

def svg(buffer, theme='dracula'):
    # Calculate dimensions based on buffer content
    max_width = max(len(line) for line in buffer) if buffer else 0
    max_height = len(buffer)
    
    char_width = 10
    char_height = 20
    svg_width = max_width * char_width + char_width * 2  # Add padding
    svg_height = max_height * char_height + char_height * 2  # Add padding
    
    # Get theme colors
    theme_colors = COLOR_THEMES.get(theme, COLOR_THEMES['dracula'])
    bg_color = theme_colors['background']
    default_fg_color = theme_colors['foreground']
    
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="JetBrains Mono, Fira Code, SF Mono, Monaco, Consolas, monospace" font-size="16"',
        f'viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">'
    ]
    
    # Add themed background fill for the entire SVG
    output.append(f'<rect x="0" y="0" width="{svg_width}" height="{svg_height}" fill="{bg_color}"/>')

    # First pass: draw background rectangles
    for y, line in enumerate(buffer):
        for x, char in enumerate(line):
            if char.background:
                themed_bg = get_themed_color(char.background, theme)
                rect_x = (x + 1) * char_width
                rect_y = y * char_height + char_height // 4  # Align with text baseline
                output.append(f'<rect x="{rect_x}" y="{rect_y}" width="{char_width}" height="{char_height}" fill="{themed_bg}"/>')

    # Second pass: draw text characters
    for y, line in enumerate(buffer):
        for x, char in enumerate(line):
            attributes = []
            if 'bold' in char.attributes:
                attributes.append('font-weight="bold"')
            if 'italic' in char.attributes:
                attributes.append('font-style="italic"')
            if 'underline' in char.attributes:
                attributes.append('text-decoration="underline"')
            if char.foreground:
                themed_fg = get_themed_color(char.foreground, theme)
                attributes.append(f'fill="{themed_fg}"')
            else:
                attributes.append(f'fill="{default_fg_color}"')  # Use themed default text color
                
            text_x = (x + 1) * char_width
            text_y = (y + 1) * char_height
            
            # Escape special XML characters
            escaped_char = char.char.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            output.append(f'<text x="{text_x}" y="{text_y}" {' '.join(attributes)}>{escaped_char}</text>')

    output.append('</svg>')
    return '\n'.join(output)

def main():
    # Check for help or list themes
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: ansi2txt.py [--svg [--theme=<theme>]] [--decode-only] [--list-themes]")
        print("Convert ANSI escape sequences to plain text or SVG")
        print("")
        print("Options:")
        print("  --svg              Output as SVG")
        print("  --theme=<theme>    Use specified color theme for SVG (default: dracula)")
        print("  --decode-only      Only decode escape sequences")
        print("  --list-themes      List available color themes")
        print("  --help, -h         Show this help message")
        return
    
    if '--list-themes' in sys.argv:
        print("Available color themes:")
        for theme_name in COLOR_THEMES.keys():
            print(f"  {theme_name}")
        return

    inputBytes = sys.stdin.buffer.read()
    parsed = parse(inputBytes)

    if '--decode-only' in sys.argv:
        for item in parsed:
            print(item)
    elif '--svg' in sys.argv:
        # Check for theme argument
        theme = 'dracula'  # default theme
        for i, arg in enumerate(sys.argv):
            if arg.startswith('--theme='):
                theme = arg.split('=', 1)[1]
            elif arg == '--theme' and i + 1 < len(sys.argv):
                theme = sys.argv[i + 1]
        
        # Validate theme
        if theme not in COLOR_THEMES:
            print(f"Error: Unknown theme '{theme}'. Available themes: {', '.join(COLOR_THEMES.keys())}", file=sys.stderr)
            print("Use --list-themes to see all available themes.", file=sys.stderr)
            sys.exit(1)
            
        print(svg(render(parsed), theme))
    else:
        print(txt(render(parsed)))


if __name__ == '__main__':
    main()