"""Reconstrucción de la lógica booleana de un programa S7 (AWL/STL, nemónicos alemanes).

Trabaja sobre la exportación JSON generada por el exportador .NET (bloques ya
descompilados de MC7 a AWL). Para cada bloque produce una "plantilla" de eventos
(escrituras, lecturas, llamadas, temporizadores) con operandos todavía en forma
local (#param, #static); luego `instanciar` recorre el árbol de llamadas desde
los OB y sustituye los parámetros por los operandos reales de cada CALL.
"""
import re

# ---------------------------------------------------------------- expresiones
TRUE = ('c', True)
FALSE = ('c', False)


def lit(op, neg=False):
    return ('l', op, neg)


def is_true(e):
    return e == TRUE


def is_false(e):
    return e == FALSE


def NOT(e):
    if e[0] == 'c':
        return FALSE if e[1] else TRUE
    if e[0] == 'l':
        return ('l', e[1], not e[2])
    if e[0] == 'n':
        return e[1]
    return ('n', e)


def AND(*xs):
    out = []
    for x in xs:
        if x is None:
            continue
        if is_false(x):
            return FALSE
        if is_true(x):
            continue
        if x[0] == 'a':
            out.extend(x[1])
        else:
            out.append(x)
    ded = []
    for x in out:
        if x not in ded:
            ded.append(x)
    for x in ded:
        if NOT(x) in ded:
            return FALSE
    if not ded:
        return TRUE
    if len(ded) == 1:
        return ded[0]
    return ('a', tuple(ded))


def OR(*xs):
    out = []
    for x in xs:
        if x is None:
            continue
        if is_true(x):
            return TRUE
        if is_false(x):
            continue
        if x[0] == 'o':
            out.extend(x[1])
        else:
            out.append(x)
    ded = []
    for x in out:
        if x not in ded:
            ded.append(x)
    # (A ∧ x) ∨ (A ∧ ¬x) -> A   (simplificación de caminos de salto)
    changed = True
    while changed and len(ded) > 1:
        changed = False
        for i in range(len(ded)):
            for j in range(i + 1, len(ded)):
                m = _merge(ded[i], ded[j])
                if m is not None:
                    ded = [d for k, d in enumerate(ded) if k not in (i, j)] + [m]
                    changed = True
                    break
            if changed:
                break
    for x in ded:
        if NOT(x) in ded:
            return TRUE
    if not ded:
        return FALSE
    if len(ded) == 1:
        return ded[0]
    return ('o', tuple(ded))


def _factors(e):
    return list(e[1]) if e[0] == 'a' else [e]


def _merge(a, b):
    fa, fb = _factors(a), _factors(b)
    if len(fa) != len(fb):
        # absorción: A ∨ (A ∧ B) = A
        sa, sb = set(map(repr, fa)), set(map(repr, fb))
        if sa <= sb:
            return a
        if sb <= sa:
            return b
        return None
    diff = [(x, y) for x, y in zip(sorted(fa, key=repr), sorted(fb, key=repr)) if x != y]
    if len(diff) == 1 and NOT(diff[0][0]) == diff[0][1]:
        rest = [x for x in fa if x != diff[0][0]]
        return AND(*rest) if rest else TRUE
    if not diff:
        return a
    return None


def XOR(a, b):
    return ('x', a, b)


def literals(e, acc=None):
    """Lista de (operando, negado) de una expresión."""
    if acc is None:
        acc = []
    t = e[0]
    if t == 'l':
        acc.append((e[1], e[2]))
    elif t in ('a', 'o'):
        for x in e[1]:
            literals(x, acc)
    elif t == 'n':
        sub = literals(e[1])
        acc.extend((o, not n) for o, n in sub)
    elif t == 'x':
        literals(e[1], acc)
        literals(e[2], acc)
    elif t == 'e':          # flanco
        literals(e[2], acc)
    elif t == 'k':          # comparación
        for o in e[4]:
            acc.append((o, False))
    elif t == 'q':          # condición opaca
        for o in e[2]:
            acc.append((o, False))
    return acc


def subst(e, fn):
    """Sustituye operandos de los literales con fn(op) -> op | expr."""
    t = e[0]
    if t == 'c':
        return e
    if t == 'l':
        r = fn(e[1])
        if isinstance(r, tuple):            # sustitución por expresión
            return NOT(r) if e[2] else r
        return ('l', r, e[2])
    if t == 'a':
        return AND(*[subst(x, fn) for x in e[1]])
    if t == 'o':
        return OR(*[subst(x, fn) for x in e[1]])
    if t == 'n':
        return NOT(subst(e[1], fn))
    if t == 'x':
        return XOR(subst(e[1], fn), subst(e[2], fn))
    if t == 'e':
        m = fn(e[3])
        return ('e', e[1], subst(e[2], fn), m if isinstance(m, str) else e[3])
    if t == 'k':
        a = _subst_txt(e[1], fn)
        b = _subst_txt(e[3], fn)
        ops = tuple(o if not isinstance(fn(o), str) else fn(o) for o in e[4])
        return ('k', a, e[2], b, ops)
    if t == 'q':
        return ('q', _subst_txt(e[1], fn), tuple(fn(o) if isinstance(fn(o), str) else o for o in e[2]))
    return e


def _subst_txt(txt, fn):
    def rep(m):
        r = fn(m.group(0))
        return r if isinstance(r, str) else m.group(0)
    return re.sub(r'#[\w\.\[\]]+', rep, txt or '')


def size(e):
    if e[0] in ('a', 'o'):
        return sum(size(x) for x in e[1])
    if e[0] in ('n',):
        return size(e[1])
    if e[0] == 'x':
        return size(e[1]) + size(e[2])
    if e[0] == 'e':
        return 1 + size(e[2])
    return 1


# ---------------------------------------------------------------- operandos
RE_BIT = re.compile(r'^(E|A|M|PE|PA)(\d+)\.(\d)$')
RE_BYTE = re.compile(r'^(E|A|M|PE|PA)(B|W|D)(\d+)$')
RE_TZ = re.compile(r'^(T|Z)(\d+)$')
RE_DBX = re.compile(r'^DB(\d+)\.DB(X|B|W|D)(\d+)(?:\.(\d))?$')
RE_BLK = re.compile(r'^(FB|FC|SFB|SFC|DB|DI|UDT)(\d+)$')


def norm(op):
    if op is None:
        return None
    s = op.strip()
    # "E 182.3" -> "E182.3", "DB108.DBX 16.0" -> "DB108.DBX16.0", "EB 5" -> "EB5"
    s = re.sub(r'^(PEB|PEW|PED|PAB|PAW|PAD|EB|EW|ED|AB|AW|AD|MB|MW|MD|E|A|M|T|Z|DB|FB|FC|SFC|SFB)\s+(\d)', r'\1\2', s)
    s = re.sub(r'\.(DB[XBWD])\s+', r'.\1', s)
    s = re.sub(r'^(DB\d+)\.(DB[XBWD])\s*', r'\1.\2', s)
    return s


def es_global(op):
    if not op or op.startswith('#'):
        return False
    return bool(RE_BIT.match(op) or RE_BYTE.match(op) or RE_TZ.match(op) or RE_DBX.match(op)
                or re.match(r'^DB\d+\.', op))


def bits_de(op):
    """Bits cubiertos por un operando de byte/palabra/doble palabra (E/A/M)."""
    m = RE_BYTE.match(op)
    if not m:
        return []
    area, w, n = m.group(1), m.group(2), int(m.group(3))
    nb = {'B': 1, 'W': 2, 'D': 4}[w]
    return [f'{area}{n + i}.{b}' for i in range(nb) for b in range(8)]


CONST_RE = re.compile(r"^(-?\d+|L#-?\d+|S5T#.*|T#.*|W#16#.*|DW#16#.*|B#16#.*|C#.*|P#.*|TRUE|FALSE|'.*'|\d+\.\d+e?.*|B#\(.*)$", re.I)


def es_constante(p):
    return bool(p) and bool(CONST_RE.match(p.strip()))


# ---------------------------------------------------------------- análisis de un bloque
LOGIC_OPS = {'U': ('and', False), 'UN': ('and', True), 'O': ('or', False), 'ON': ('or', True),
             'X': ('xor', False), 'XN': ('xor', True)}
NEST_OPS = {'U(': ('and', False), 'UN(': ('and', True), 'O(': ('or', False), 'ON(': ('or', True),
            'X(': ('xor', False), 'XN(': ('xor', True)}
CMP_OPS = {'==I', '<>I', '>I', '<I', '>=I', '<=I', '==D', '<>D', '>D', '<D', '>=D', '<=D',
           '==R', '<>R', '>R', '<R', '>=R', '<=R'}
TIMER_OPS = {'SE': 'SE', 'SA': 'SA', 'SI': 'SI', 'SV': 'SV', 'SS': 'SS'}
ARITH = {'+I', '-I', '*I', '/I', '+D', '-D', '*D', '/D', 'MOD', '+R', '-R', '*R', '/R', 'UW', 'OW', 'XOW',
         'UD', 'OD', 'XOD'}
COND_JUMPS_RLO = {'SPB': True, 'SPBN': False, 'SPBB': True, 'SPBNB': False}
COND_JUMPS_ACC = {'SPZ', 'SPN', 'SPP', 'SPM', 'SPPZ', 'SPMZ', 'SPO', 'SPS', 'SPU', 'SPBI', 'SPBIN'}


class Logic:
    """Estado del RLO como suma de productos con anidamiento."""

    def __init__(self):
        self.reset_all()

    def reset_all(self):
        self.terms = []
        self.first = True
        self.pending = TRUE
        self.stack = []

    def cur(self):
        if self.first:
            return self.pending
        return OR(*[AND(*t) if t else TRUE for t in self.terms]) if self.terms else TRUE

    def combine(self, kind, x):
        if kind == 'and':
            if self.first:
                self.terms = [[x]]
                self.first = False
            else:
                if not self.terms:
                    self.terms = [[]]
                self.terms[-1].append(x)
        elif kind == 'or':
            if self.first:
                self.terms = [[x]]
                self.first = False
            else:
                self.terms.append([x])
        elif kind == 'xor':
            if self.first:
                self.terms = [[x]]
                self.first = False
            else:
                self.terms = [[XOR(self.cur(), x)]]

    def or_alone(self):
        if not self.first:
            self.terms.append([])

    def push(self, kind, neg):
        self.stack.append((self.terms, self.first, self.pending, kind, neg))
        self.terms, self.first, self.pending = [], True, TRUE

    def pop(self):
        inner = self.cur()
        if not self.stack:
            return
        self.terms, self.first, self.pending, kind, neg = self.stack.pop()
        self.combine(kind, NOT(inner) if neg else inner)

    def set_value(self, e):
        """Resultado tras = / S / R o SET / CLR: el RLO se conserva, /ER = 0."""
        self.pending = e
        self.terms = []
        self.first = True


def _cap(e, limite=40):
    if size(e) > limite:
        ops = tuple(sorted({o for o, _ in literals(e)}))[:30]
        return ('q', 'condición de saltos compleja', ops)
    return e


def analizar_bloque(blk, temps=frozenset(), nombres=frozenset()):
    """Devuelve la plantilla de eventos del bloque (operandos sin resolver)."""
    ev = []
    lg = Logic()
    pc = TRUE                 # condición de camino (saltos)
    arrive = {}               # etiqueta -> [condiciones de llegada]
    bie_at = {}
    bie = TRUE
    acc1 = acc2 = None
    acc1_ops = []
    acc2_ops = []
    temp_val = {}
    indirect = False
    seen_labels = set()
    spl = None
    for net in blk.get('Networks') or []:
        nn = net['N']
        # Sin saltos pendientes, cada segmento empieza con condición de camino TRUE
        # (los saltos del código FUP/KOP son siempre locales al segmento).
        if not arrive and not is_false(pc):
            pc = TRUE
        lg.reset_all()
        for idx, r in enumerate(net['Rows']):
            cmd = (r.get('Command') or '').strip()
            par = norm(r.get('Parameter') or '')
            lab = (r.get('Label') or '').strip()
            if lab:
                seen_labels.add(lab)
                if lab in arrive:
                    pc = _cap(OR(pc, *arrive.pop(lab)))
                if lab in bie_at:
                    bie = bie_at.pop(lab)
                # tras un salto el RLO de la etiqueta es desconocido -> se toma lo actual
            if not cmd:
                continue
            if par and ('[' in par):
                indirect = True
                ev.append(('indirect', par, nn, r.get('Txt', '').strip()))
            def rd(op, how):
                if op and not es_constante(op):
                    ev.append(('read', op, how, nn, pc))

            if cmd in LOGIC_OPS:
                kind, neg = LOGIC_OPS[cmd]
                if par:
                    if par == 'BIE':
                        x = bie
                        x = NOT(x) if neg else x
                    elif par in ('==0', '<>0', '>0', '<0', '>=0', '<=0', 'OV', 'OS', 'UO'):
                        x = ('q', f'{cmd} {par} ({acc1 or "?"})', tuple(acc1_ops))
                        x = NOT(x) if neg else x
                    elif par.startswith('#') and par in temp_val and not neg:
                        x = temp_val[par]
                    elif par.startswith('#') and par in temp_val and neg:
                        x = NOT(temp_val[par])
                    else:
                        x = lit(par, neg)
                        rd(par, cmd)
                    lg.combine(kind, x)
                else:
                    if cmd == 'O':
                        lg.or_alone()
                continue
            if cmd in NEST_OPS:
                kind, neg = NEST_OPS[cmd]
                lg.push(kind, neg)
                continue
            if cmd == ')':
                lg.pop()
                continue
            if cmd == 'NOT':
                lg.set_value(NOT(lg.cur()))
                lg.first = False
                lg.terms = [[lg.pending]]
                continue
            if cmd == 'SET':
                lg.set_value(TRUE)
                continue
            if cmd == 'CLR':
                lg.set_value(FALSE)
                continue
            if cmd == 'SAVE':
                bie = lg.cur()
                continue
            if cmd in ('=', 'S', 'R'):
                val = lg.cur()
                kind = {'=': 'assign', 'S': 'set', 'R': 'reset'}[cmd]
                if par.startswith('#') and par[1:] in temps and cmd == '=' and is_true(pc):
                    temp_val[par] = val
                elif par in temp_val:
                    temp_val.pop(par, None)
                ev.append(('write', par, kind, val, pc, nn, r.get('Txt', '').strip()))
                lg.set_value(val)
                continue
            if cmd in ('FP', 'FN'):
                val = lg.cur()
                e = ('e', 'P' if cmd == 'FP' else 'N', val, par)
                ev.append(('write', par, 'edge', val, pc, nn, r.get('Txt', '').strip()))
                rd(par, cmd)
                lg.terms = [[e]]
                lg.first = False
                continue
            if cmd in TIMER_OPS:
                val = lg.cur()
                ev.append(('timer', par, TIMER_OPS[cmd], acc1, AND(pc, val), nn, r.get('Txt', '').strip()))
                ev.append(('write', par, 'timer_start', val, pc, nn, r.get('Txt', '').strip()))
                continue
            if cmd in ('ZV', 'ZR'):
                val = lg.cur()
                ev.append(('counter', par, cmd, None, AND(pc, val), nn, r.get('Txt', '').strip()))
                ev.append(('write', par, 'count_' + ('up' if cmd == 'ZV' else 'down'), val, pc, nn,
                           r.get('Txt', '').strip()))
                continue
            if cmd == 'FR':
                rd(par, cmd)
                continue
            if cmd in ('L', 'LC', 'LAR1', 'LAR2', 'L DBLG', 'L DBNO'):
                if par:
                    rd(par, cmd)
                acc2, acc2_ops = acc1, acc1_ops
                acc1 = par or cmd
                acc1_ops = [par] if par and not es_constante(par) else []
                continue
            if cmd == 'T':
                ev.append(('write', par, 'transfer', ('t', acc1, tuple(acc1_ops)), pc, nn, r.get('Txt', '').strip()))
                continue
            if cmd == 'TAK':
                acc1, acc2 = acc2, acc1
                acc1_ops, acc2_ops = acc2_ops, acc1_ops
                continue
            if cmd in CMP_OPS:
                x = ('k', acc2 or '?', cmd, acc1 or '?', tuple(acc2_ops + acc1_ops))
                lg.combine('and', x)
                continue
            if cmd in ARITH:
                if par:      # "+ 2"
                    acc1 = f'({acc1} {cmd} {par})'
                else:
                    acc1 = f'({acc2} {cmd[0] if cmd[0] in "+-*/" else cmd} {acc1})'
                    acc1_ops = acc2_ops + acc1_ops
                continue
            if cmd in ('+', 'INC', 'DEC'):
                acc1 = f'({acc1} {cmd} {par})'
                continue
            if cmd in COND_JUMPS_RLO:
                c = lg.cur()
                jump_c = c if COND_JUMPS_RLO[cmd] else NOT(c)
                if par in seen_labels:      # salto hacia atrás: no se modela
                    pass
                else:
                    arrive.setdefault(par, []).append(AND(pc, jump_c))
                    pc = _cap(AND(pc, NOT(jump_c)))
                if cmd in ('SPBB', 'SPBNB'):
                    bie_at[par] = c
                    bie = c
                lg.set_value(TRUE)
                continue
            if cmd in COND_JUMPS_ACC:
                c = ('q', f'{cmd} ({acc1 or "?"})', tuple(acc1_ops))
                if par not in seen_labels:
                    arrive.setdefault(par, []).append(AND(pc, c))
                    pc = AND(pc, NOT(c))
                continue
            if cmd == 'SPA':
                if spl is not None and not lab:
                    base, i, src, ops = spl
                    if par not in seen_labels:
                        arrive.setdefault(par, []).append(AND(base, ('q', f'{src} = {i}', ops)))
                    spl = (base, i + 1, src, ops)
                    continue
                spl = None
                if par not in seen_labels:
                    arrive.setdefault(par, []).append(pc)
                    pc = FALSE
                continue
            spl = None
            if cmd == 'SPL':
                indirect = True
                c = ('q', f'SPL ({acc1 or "?"}) fuera de rango', tuple(acc1_ops))
                if par not in seen_labels:
                    arrive.setdefault(par, []).append(AND(pc, c))
                spl = (pc, 0, acc1 or '?', tuple(acc1_ops))
                pc = FALSE
                continue
            if cmd == 'LOOP':
                continue
            if cmd == 'BEB':
                c = lg.cur()
                pc = AND(pc, NOT(c))
                lg.set_value(TRUE)
                continue
            if cmd in ('BEA', 'BE'):
                pc = FALSE
                continue
            if cmd in ('CALL', 'UC', 'CC'):
                callee = norm(par.split(',')[0].strip()) if par else ''
                inst = None
                m = re.search(r'(?:CALL|UC|CC)\s+([^,(\s]+)\s*(?:,\s*([^\s(]+))?', r.get('Txt') or '')
                if m:
                    callee = norm(m.group(1))
                    if m.group(2):
                        inst = norm(m.group(2))
                elif ',' in (par or ''):
                    inst = norm(par.split(',')[1].strip())
                cond = pc if cmd != 'CC' else AND(pc, lg.cur())
                params = {}
                pexpr = {}
                for cp in r.get('Call') or []:
                    v = norm(cp['Value']) if cp.get('Value') else None
                    if v and re.match(r'^[A-Za-z_]\w*\.(STATIC|IN|OUT|IN_OUT)\.', v):
                        v = '#' + v
                    elif v and not v.startswith('#') and v.split('.')[0] in nombres:
                        v = '#' + v
                    if v and v.startswith('#') and v in temp_val:
                        pexpr[cp['Name']] = temp_val[v]
                    params[cp['Name']] = v
                if callee.startswith('#'):          # multiinstancia: CALL #A46M2
                    inst = callee
                    callee = None
                ev.append(('call', callee, inst, params, cond, nn, r.get('Txt', '').strip()[:200], pexpr))
                lg.set_value(TRUE)
                continue
            if cmd == 'AUF':
                rd(par, cmd)
                continue
            if cmd in ('BLD', 'NOP'):
                continue
            # resto (conversiones, desplazamientos, AR...) no afectan al RLO
            if par and not es_constante(par) and not par.isdigit():
                rd(par, cmd)
    return {'events': ev, 'indirect': indirect}


# ---------------------------------------------------------------- interfaz
def interfaz(blk):
    """{'IN': [...], 'OUT': [...], 'IN_OUT': [...], 'STATIC': [...], 'TEMP': [...]}"""
    res = {}
    i = blk.get('Interface')
    if not i:
        return res
    for sec in i.get('Children') or []:
        res[sec['Name']] = [(c['Name'], c['DataType'], c.get('Comment') or '') for c in sec.get('Children') or []]
    return res


SYS_OUT_PARAMS = {'RET_VAL', 'DONE', 'BUSY', 'ERROR', 'STATUS', 'Q', 'ET', 'CV', 'QU', 'QD', 'NDR', 'CDT',
                  'RECORD_OUT', 'DSTBLK', 'BVAL', 'OUT', 'VALID', 'LEN', 'DB_LENGTH', 'WRITE_PROT'}
SYS_INOUT = {'SFC14': {'RECORD'}, 'SFC59': {'RECORD'}, 'SFC20': {'DSTBLK'}, 'SFC21': {'DSTBLK'},
             'SFB15': set(), 'SFC67': {'RD'}, 'SFC1': {'CDT'}}


def direccion_param(callee, name, ifz):
    for sec in ('IN', 'OUT', 'IN_OUT'):
        for n, _, _ in ifz.get(sec, []):
            if n == name:
                return sec
    if callee and callee.startswith('S'):
        if name in SYS_INOUT.get(callee, set()):
            return 'OUT'
        return 'OUT' if name in SYS_OUT_PARAMS else 'IN'
    return 'IN'
