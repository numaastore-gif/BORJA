"""Análisis causa-efecto de un programa S7 exportado a JSON.

Uso: python analizar.py progN.json salida.pkl
"""
import json
import pickle
import re
import sys
from collections import defaultdict

from stl_logic import (AND, NOT, OR, TRUE, FALSE, analizar_bloque, bits_de, direccion_param, es_constante,
                       es_global, interfaz, literals, norm, subst, RE_BIT, RE_BYTE, RE_DBX, RE_TZ, is_true)

SECCIONES = {'IN', 'OUT', 'IN_OUT', 'STATIC', 'TEMP'}


def cargar(path):
    return json.load(open(path, encoding='utf-8'))


def aplanar_db(row, prefix='', out=None):
    """Lista de (ruta, tipo, dirección, comentario, valor inicial)."""
    if out is None:
        out = []
    for c in row.get('Children') or []:
        name = c['Name']
        path = prefix if name in SECCIONES and not prefix else (prefix + '.' + name if prefix else name)
        if name in SECCIONES and not prefix:
            aplanar_db(c, '', out)
            continue
        out.append((path, c.get('DataType') or '', c.get('Address') or '', c.get('Comment') or '',
                    c.get('StartValue')))
        if c.get('Children') and not (c.get('DataType') or '').upper().startswith('ARRAY'):
            aplanar_db(c, path, out)
    return out


def main(src, dst):
    P = cargar(src)
    blocks = {b['Name']: b for b in P['Blocks'] if b.get('Name')}
    # ------------------------------------------------ símbolos
    sym = {}
    for s in P.get('Symbols') or []:
        op = norm(s['Operand'])
        sym[op] = {'Symbol': s['Symbol'], 'Comment': s.get('Comment') or '', 'DataType': s.get('DataType') or '',
                   'OperandIEC': s.get('OperandIEC') or ''}
    # ------------------------------------------------ DB: mapa absoluto -> simbólico
    dbvars = {}           # 'DB80' -> [(ruta, tipo, dir, comentario, inicial)]
    abs2sym = {}
    sympath_info = {}
    for n, b in blocks.items():
        if b['Type'] == 'DB' and b.get('Structure'):
            rows = aplanar_db(b['Structure'])
            dbvars[n] = rows
            for path, typ, addr, com, sv in rows:
                sympath_info[f'{n}.{path}'] = (typ, addr, com, sv)
                m = re.match(r'^(\d+)\.(\d+)$', addr or '')
                if not m:
                    continue
                by, bi = int(m.group(1)), int(m.group(2))
                t = typ.upper()
                if t == 'BOOL':
                    abs2sym[f'{n}.DBX{by}.{bi}'] = f'{n}.{path}'
                elif t in ('BYTE', 'CHAR'):
                    abs2sym[f'{n}.DBB{by}'] = f'{n}.{path}'
                elif t in ('INT', 'WORD', 'S5TIME', 'DATE'):
                    abs2sym[f'{n}.DBW{by}'] = f'{n}.{path}'
                elif t in ('DINT', 'DWORD', 'REAL', 'TIME', 'TIME_OF_DAY', 'TOD'):
                    abs2sym[f'{n}.DBD{by}'] = f'{n}.{path}'
    inst_fb = {n: f"FB{b['FB']}" for n, b in blocks.items() if b['Type'] == 'DB' and b.get('IsInstance')}

    # ------------------------------------------------ plantillas
    ifz = {n: interfaz(b) for n, b in blocks.items() if b['Type'] in ('FB', 'FC', 'OB')}
    tpl = {}
    for n, b in blocks.items():
        if b['Type'] in ('FB', 'FC', 'OB'):
            temps = frozenset(x[0] for x in ifz[n].get('TEMP', []))
            nombres = frozenset(x[0] for sec in ifz[n].values() for x in sec)
            tpl[n] = analizar_bloque(b, temps, nombres)

    # ------------------------------------------------ referencias cruzadas (nivel código, como STEP 7)
    xref = []          # (op, bloque, nw, 'R'/'W', instrucción)
    for n, t in tpl.items():
        for e in t['events']:
            if e[0] == 'read' and es_global(e[1]):
                xref.append((e[1], n, e[3], 'R', e[2]))
            elif e[0] == 'write' and es_global(e[1]):
                xref.append((e[1], n, e[5], 'W', e[6]))
            elif e[0] == 'timer' and es_global(e[1]):
                pass
            elif e[0] == 'call':
                callee, inst, params, cond, nn, txt = e[1], e[2], e[3], e[4], e[5], e[6]
                cifz = ifz.get(callee, {})
                if inst and es_global(inst) is False and re.match(r'^DB\d+$', inst or ''):
                    xref.append((inst, n, nn, 'R', f'CALL {callee}, {inst}'))
                if callee:
                    xref.append((callee, n, nn, 'R', 'CALL'))
                for pn, pv in params.items():
                    if not pv or es_constante(pv):
                        continue
                    d = direccion_param(callee, pn, cifz)
                    pv2 = pv.replace('P#', '').split(' ')[0] if pv.startswith('P#') else pv
                    if es_global(pv2):
                        rw = {'IN': 'R', 'OUT': 'W', 'IN_OUT': 'RW'}[d]
                        for x in rw:
                            xref.append((pv2, n, nn, x, f'CALL {callee or inst} ({pn} := {pv})'))
            elif e[0] == 'indirect':
                pass

    # ------------------------------------------------ instanciación desde los OB
    W = []          # escrituras instanciadas
    RD = []         # lecturas instanciadas
    TM = []         # temporizadores/contadores instanciados
    CALLS = []      # (llamante, nw, llamado, instancia)
    alias = {}
    called = set()
    visits = defaultdict(int)

    def canon(op):
        seen = 0
        while isinstance(op, str) and seen < 8:
            seen += 1
            o2 = abs2sym.get(op, op)
            o2 = alias.get(o2, o2)
            if o2 == op:
                break
            op = o2
        return op

    def make_R(block, params, prefix, caller_R):
        bi = ifz.get(block, {})
        pnames = {x[0] for s in ('IN', 'OUT', 'IN_OUT') for x in bi.get(s, [])}
        statics = {x[0] for x in bi.get('STATIC', [])}
        temps = {x[0] for x in bi.get('TEMP', [])}

        def R(op):
            if not isinstance(op, str) or not op.startswith('#'):
                return op
            parts = op[1:].split('.')
            head = parts[0]
            rest = [p for p in parts[1:] if p not in SECCIONES]
            tail = ('.' + '.'.join(rest)) if rest else ''
            if head in pnames:
                act = params.get(head)
                if act is None:
                    if prefix:
                        return prefix + head + tail
                    return f'?{block}.{head}{tail}'
                if isinstance(act, tuple):
                    return act if not tail else f'?{block}.{head}{tail}'
                if act.upper() in ('TRUE', 'FALSE') and not tail:
                    return TRUE if act.upper() == 'TRUE' else FALSE
                return act + tail
            if head in statics and prefix:
                return prefix + head + tail
            if head in temps:
                return f'~{block}.{head}{tail}'
            if prefix:
                return prefix + head + tail
            return f'~{block}.{head}{tail}'
        return R

    def inst(block, params, prefix, pc, chain, depth):
        if depth > 14 or block not in tpl:
            return
        visits[block] += 1
        called.add(block)
        R = make_R(block, params, prefix, None)

        def RR(op):
            r = R(op)
            return canon(r) if isinstance(r, str) else r
        for e in tpl[block]['events']:
            k = e[0]
            if k == 'write':
                _, op, kind, expr, epc, nn, txt = e
                op2 = R(op)
                if not isinstance(op2, str):
                    continue
                if kind == 'transfer':
                    src = expr[1]
                    srcops = tuple(R(o) if isinstance(R(o), str) else str(o) for o in expr[2])
                    ex2 = ('t', src, srcops)
                else:
                    ex2 = subst(expr, RR)
                W.append({'op': canon(op2), 'raw': op2, 'kind': kind, 'expr': ex2,
                          'pc': AND(pc, subst(epc, RR)), 'block': block, 'nw': nn, 'txt': txt,
                          'chain': chain, 'prefix': prefix})
            elif k == 'read':
                _, op, how, nn, epc = e
                op2 = R(op)
                if isinstance(op2, str):
                    RD.append({'op': canon(op2), 'block': block, 'nw': nn, 'how': how, 'chain': chain})
            elif k in ('timer', 'counter'):
                _, op, typ, preset, cond, nn, txt = e
                op2 = R(op)
                pre = preset
                if isinstance(preset, str) and preset.startswith('#'):
                    p2 = R(preset)
                    pre = p2 if isinstance(p2, str) else preset
                TM.append({'op': canon(op2) if isinstance(op2, str) else str(op2), 'type': typ, 'preset': pre,
                           'cond': AND(pc, subst(cond, RR)), 'block': block, 'nw': nn, 'txt': txt, 'chain': chain})
            elif k == 'call':
                _, callee, iname, cparams, cond, nn, txt, pexpr = e
                rp = {}
                for pn, pv in cparams.items():
                    if pn in pexpr:
                        rp[pn] = subst(pexpr[pn], RR)
                        continue
                    if pv is None:
                        rp[pn] = None
                        continue
                    if pv.startswith('#'):
                        r = R(pv)
                        rp[pn] = r if isinstance(r, str) else ('TRUE' if r == TRUE else 'FALSE')
                    else:
                        rp[pn] = pv
                    if isinstance(rp[pn], str):
                        rp[pn] = canon(rp[pn])
                CALLS_RP = {k: (v if isinstance(v, str) or v is None else '(expr)') for k, v in rp.items()}
                newpc = AND(pc, subst(cond, RR))
                if callee is None and iname:          # multiinstancia
                    ipath = R(iname)
                    fbn = None
                    # tipo del multiinstancia: en la interfaz STATIC del bloque llamante
                    for nme, typ, _ in ifz.get(block, {}).get('STATIC', []):
                        if nme == iname[1:]:
                            fbn = norm(typ)
                    callee = fbn
                    newprefix = (ipath + '.') if isinstance(ipath, str) else None
                elif iname and re.match(r'^DB\d+$', iname):
                    newprefix = iname + '.'
                else:
                    newprefix = None
                CALLS.append({'caller': block, 'nw': nn, 'callee': callee, 'inst': iname,
                              'prefix': newprefix, 'params': CALLS_RP, 'txt': txt, 'chain': chain})
                if callee in tpl:
                    cifz = ifz.get(callee, {})
                    if newprefix:
                        for pn, pv in rp.items():
                            if isinstance(pv, str) and es_global(pv):
                                alias[newprefix + pn] = pv
                    inst(callee, rp, newprefix, newpc,
                         chain + [(block, nn, f'{callee}' + (f', {iname}' if iname else ''))], depth + 1)
                else:
                    # SFC/SFB o bloque inexistente: parámetros como lectura/escritura
                    for pn, pv in rp.items():
                        if not isinstance(pv, str) or es_constante(pv):
                            continue
                        d = direccion_param(callee, pn, ifz.get(callee, {}))
                        if d in ('OUT', 'IN_OUT'):
                            W.append({'op': pv, 'raw': pv, 'kind': 'call_out', 'expr': ('t', f'{callee}.{pn}', ()),
                                      'pc': newpc, 'block': block, 'nw': nn, 'txt': txt, 'chain': chain,
                                      'prefix': prefix})
                        if d in ('IN', 'IN_OUT'):
                            RD.append({'op': pv, 'block': block, 'nw': nn, 'how': f'{callee}.{pn}', 'chain': chain})

    obs = sorted([n for n, b in blocks.items() if b['Type'] == 'OB'], key=lambda x: int(x[2:]))
    for ob in obs:
        inst(ob, {}, None, TRUE, [], 0)
    # alias de segunda vuelta para canonizar lo leído antes de su CALL
    for w in W:
        w['op'] = canon(w['op'])
    for r in RD:
        r['op'] = canon(r['op'])

    no_llamados = [n for n in tpl if n not in called]
    # bloques no llamados: se analizan de forma aislada para no perder escrituras directas
    for n in no_llamados:
        b = blocks[n]
        for e in tpl[n]['events']:
            if e[0] == 'write' and es_global(e[1]):
                W.append({'op': canon(e[1]), 'raw': e[1], 'kind': e[2], 'expr': e[3], 'pc': e[4], 'block': n,
                          'nw': e[5], 'txt': e[6], 'chain': [], 'prefix': None, 'uncalled': True})

    out = {'P': {k: v for k, v in P.items() if k != 'Blocks'}, 'blocks': blocks, 'sym': sym, 'dbvars': dbvars,
           'abs2sym': abs2sym, 'sympath_info': sympath_info, 'inst_fb': inst_fb, 'ifz': ifz, 'tpl': tpl,
           'xref': xref, 'W': W, 'RD': RD, 'TM': TM, 'CALLS': CALLS, 'alias': alias, 'no_llamados': no_llamados,
           'visits': dict(visits)}
    pickle.dump(out, open(dst, 'wb'))
    print(f'bloques={len(blocks)} plantillas={len(tpl)} escrituras={len(W)} lecturas={len(RD)} '
          f'temporizadores={len(TM)} llamadas={len(CALLS)} xref={len(xref)} no_llamados={len(no_llamados)}')


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main(sys.argv[1], sys.argv[2])
