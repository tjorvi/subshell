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

def txt(buffer):
    return '\n'.join(''.join(c.char for c in line) for line in buffer).rstrip() + '\n'

def svg(buffer):
    output = ['<svg xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="16"',
    'viewBox="0 0 800 600">']

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
                attributes.append(f'fill="{char.foreground}"')
            if char.background:
                attributes.append(f'background-color="{char.background}"')
            output.append(f'<text x="{(x+1) * 10}" y="{(y+1) * 20}" {' '.join(attributes)}>{char.char}</text>')

    output.append('</svg>')
    return '\n'.join(output)

def main():
    inputBytes = sys.stdin.buffer.read()
    parsed = parse(inputBytes)

    if '--decode-only' in sys.argv:
        for item in parsed:
            print(item)
    elif '--svg' in sys.argv:
        print(svg(render(parsed)))
    else:
        print(txt(render(parsed)))


if __name__ == '__main__':
    main()