"""Gera maquina.glb e maquina.usdz (máquina RE FLOW) a partir das texturas em tex/.

Uso (macOS, precisa de Pillow e numpy):  python3 textures.py && python3 build.py ../maquina
"""
import json, math, os, shutil, struct, subprocess, sys

W, D, H = 0.43, 0.58, 1.70           # largura (x), profundidade (z), altura (y)
Y_DIV = 0.88                          # altura da divisão entre gabinete e módulo superior
X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2

# ---------- materiais ----------
MATS = {}
def mat(name, color=(1, 1, 1), tex=None, metal=0.0, rough=0.6, opacity=1.0):
    MATS[name] = dict(color=color, tex=tex, metal=metal, rough=rough, opacity=opacity)

mat('preto', (0.07, 0.075, 0.085), rough=0.45, metal=0.2)
mat('borracha', (0.03, 0.03, 0.03), rough=0.9)
mat('laranja', (0.95, 0.42, 0.10), rough=0.5)
mat('copo', (0.9, 0.93, 0.95), rough=0.1, opacity=0.35)
mat('tubo', (0.05, 0.05, 0.06), rough=0.3, metal=0.3)
for t in ['frente_sup', 'frente_inf', 'lado_sup_esq', 'lado_sup_dir', 'lado_inf_esq', 'lado_inf_dir', 'maquininha', 'placa']:
    mat(t, tex=f'{t}.jpg', rough=0.55)

# ---------- geometria ----------
MESHES = []  # dict(name, mat, pos, nrm, uv, idx)

def quad(m, p0, p1, p2, p3, n):
    """p0..p3 = canto inf-esq, inf-dir, sup-dir, sup-esq vistos de fora. UV glTF (v para baixo)."""
    b = len(m['pos'])
    m['pos'] += [p0, p1, p2, p3]
    m['nrm'] += [n] * 4
    m['uv'] += [(0, 1), (1, 1), (1, 0), (0, 0)]
    m['idx'] += [b, b + 1, b + 2, b, b + 2, b + 3]

def new(name, material):
    m = dict(name=name, mat=material, pos=[], nrm=[], uv=[], idx=[])
    MESHES.append(m)
    return m

def box(name, x0, x1, y0, y1, z0, z1, faces):
    """faces: dict face->material para front,back,left,right,top,bottom (face ausente = omitida)."""
    for f, material in faces.items():
        m = new(f'{name}_{f}', material)
        if f == 'front':  quad(m, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (0, 0, 1))
        if f == 'back':   quad(m, (x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (0, 0, -1))
        if f == 'left':   quad(m, (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (-1, 0, 0))
        if f == 'right':  quad(m, (x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (1, 0, 0))
        if f == 'top':    quad(m, (x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0), (0, 1, 0))
        if f == 'bottom': quad(m, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (0, -1, 0))

def solid(name, material, x0, x1, y0, y1, z0, z1):
    box(name, x0, x1, y0, y1, z0, z1, {f: material for f in ['front', 'back', 'left', 'right', 'top', 'bottom']})

def cylinder(name, material, cx, cz, y0, y1, r0, r1, seg=28, caps=True):
    m = new(name, material)
    slope = (r0 - r1) / (y1 - y0)
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        pts = []
        for a in (a0, a1):
            c, s = math.cos(a), math.sin(a)
            l = math.hypot(1, slope)
            pts.append(((cx + r0 * c, y0, cz + r0 * s), (cx + r1 * c, y1, cz + r1 * s), (c / l, slope / l, s / l)))
        (b0, t0, n0), (b1, t1, n1) = pts
        b = len(m['pos'])
        m['pos'] += [b0, b1, t1, t0]; m['nrm'] += [n0, n1, n1, n0]
        m['uv'] += [(i / seg, 1), ((i + 1) / seg, 1), ((i + 1) / seg, 0), (i / seg, 0)]
        m['idx'] += [b, b + 2, b + 1, b, b + 3, b + 2]
        if caps:
            for y, r, n in ((y1, r1, (0, 1, 0)), (y0, r0, (0, -1, 0))):
                b = len(m['pos'])
                m['pos'] += [(cx, y, cz), (cx + r * math.cos(a0), y, cz + r * math.sin(a0)), (cx + r * math.cos(a1), y, cz + r * math.sin(a1))]
                m['nrm'] += [n] * 3; m['uv'] += [(0.5, 0.5)] * 3
                m['idx'] += [b, b + 2, b + 1] if n[1] > 0 else [b, b + 1, b + 2]

# gabinete inferior (sobre rodízios)
YR = 0.035
box('gabinete', X0, X1, YR, Y_DIV, Z0, Z1, dict(front='frente_inf', back='preto', left='lado_inf_esq', right='lado_inf_dir', bottom='preto'))
for x in (X0 + 0.04, X1 - 0.04):
    for z in (Z0 + 0.04, Z1 - 0.04):
        cylinder('rodizio', 'borracha', x, z, 0, YR, 0.025, 0.025)
# frisos de divisão entre os módulos
solid('friso', 'borracha', X0 - 0.003, X1 + 0.003, Y_DIV - 0.006, Y_DIV + 0.006, Z0 - 0.003, Z1 + 0.003)
# módulo superior
box('modulo', X0, X1, Y_DIV, H, Z0, Z1, dict(front='frente_sup', back='preto', left='lado_sup_esq', right='lado_sup_dir', top='preto'))
# dispensador de copos (lateral esquerda, perto da frente)
tx, tz = X0 - 0.042, Z1 - 0.07
cylinder('tubo_copos', 'tubo', tx, tz, H - 0.60, H - 0.04, 0.036, 0.036)
solid('suporte_tubo', 'tubo', X0 - 0.012, X0, H - 0.50, H - 0.10, tz - 0.02, tz + 0.02)
cylinder('copo', 'copo', tx, tz, H - 0.69, H - 0.60, 0.028, 0.036, caps=False)
# maquininha de cartão (canto frontal direito)
mx0, mx1, my0, my1 = X1 - 0.035, X1 + 0.065, H - 0.68, H - 0.46
box('maquininha', mx0, mx1, my0, my1, Z1, Z1 + 0.07, dict(front='maquininha', left='laranja', right='laranja', top='laranja', bottom='laranja'))
# placa acrílica (canto superior direito)
box('placa', X1 - 0.03, X1 + 0.17, H - 0.37, H - 0.01, Z1 + 0.002, Z1 + 0.014, dict(front='placa', back='preto', left='preto', right='preto', top='preto', bottom='preto'))


# ---------- exportação GLB ----------
def write_glb(path, texdir):
    bin_ = bytearray(); bviews = []; accs = []
    def add_view(data, target=None):
        while len(bin_) % 4: bin_.append(0)
        bv = dict(buffer=0, byteOffset=len(bin_), byteLength=len(data))
        if target: bv['target'] = target
        bin_.extend(data); bviews.append(bv); return len(bviews) - 1
    def add_acc(vals, typ, comp, target):
        flat = [c for v in vals for c in (v if isinstance(v, tuple) else (v,))]
        fmt = 'f' if comp == 5126 else 'I'
        bv = add_view(struct.pack(f'<{len(flat)}{fmt}', *flat), target)
        a = dict(bufferView=bv, componentType=comp, count=len(vals), type=typ)
        if typ == 'VEC3':
            a['min'] = [min(v[i] for v in vals) for i in range(3)]; a['max'] = [max(v[i] for v in vals) for i in range(3)]
        accs.append(a); return len(accs) - 1
    names = list(MATS); materials = []; images = []; textures = []
    for n in names:
        m = MATS[n]
        pbr = dict(metallicFactor=m['metal'], roughnessFactor=m['rough'], baseColorFactor=[*m['color'], m['opacity']])
        if m['tex']:
            iv = add_view(open(os.path.join(texdir, m['tex']), 'rb').read())
            images.append(dict(bufferView=iv, mimeType='image/jpeg'))
            textures.append(dict(source=len(images) - 1, sampler=0))
            pbr['baseColorTexture'] = dict(index=len(textures) - 1)
        md = dict(name=n, pbrMetallicRoughness=pbr, doubleSided=False)
        if m['opacity'] < 1: md['alphaMode'] = 'BLEND'
        materials.append(md)
    meshes = []
    for m in MESHES:
        prim = dict(attributes=dict(POSITION=add_acc(m['pos'], 'VEC3', 5126, 34962), NORMAL=add_acc(m['nrm'], 'VEC3', 5126, 34962),
                                    TEXCOORD_0=add_acc(m['uv'], 'VEC2', 5126, 34962)),
                    indices=add_acc(m['idx'], 'SCALAR', 5125, 34963), material=names.index(m['mat']), mode=4)
        meshes.append(dict(name=m['name'], primitives=[prim]))
    while len(bin_) % 4: bin_.append(0)
    gltf = dict(asset=dict(version='2.0', generator='maquina-ar build.py'), scene=0,
                scenes=[dict(name='Maquina', nodes=list(range(len(meshes))))],
                nodes=[dict(name=m['name'], mesh=i) for i, m in enumerate(meshes)], meshes=meshes,
                materials=materials, images=images, textures=textures,
                samplers=[dict(magFilter=9729, minFilter=9987, wrapS=33071, wrapT=33071)],
                accessors=accs, bufferViews=bviews, buffers=[dict(byteLength=len(bin_))])
    js = json.dumps(gltf, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
    out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<I4s', len(js), b'JSON') + js + struct.pack('<I4s', len(bin_), b'BIN\0') + bin_
    open(path, 'wb').write(out)


# ---------- exportação USDZ ----------
def f3(v): return '(' + ', '.join(f'{c:.6g}' for c in v) + ')'

def write_usdz(path, texdir, work):
    L = ['#usda 1.0', '(', '    defaultPrim = "Maquina"', '    metersPerUnit = 1', '    upAxis = "Y"', ')', '',
         'def Xform "Maquina" (', '    kind = "component"', ')', '{', '    def Scope "Mat"', '    {']
    for n, m in MATS.items():
        p = f'/Maquina/Mat/{n}'
        L += [f'        def Material "{n}"', '        {', f'            token outputs:surface.connect = <{p}/s.outputs:surface>']
        if m['tex']:
            L += [f'            def Shader "st"', '            {', '                uniform token info:id = "UsdPrimvarReader_float2"',
                  '                string inputs:varname = "st"', '                float2 outputs:result', '            }',
                  f'            def Shader "tex"', '            {', '                uniform token info:id = "UsdUVTexture"',
                  f'                asset inputs:file = @textures/{m["tex"]}@', f'                float2 inputs:st.connect = <{p}/st.outputs:result>',
                  '                token inputs:sourceColorSpace = "sRGB"', '                token inputs:wrapS = "clamp"', '                token inputs:wrapT = "clamp"',
                  '                float3 outputs:rgb', '            }']
        L += ['            def Shader "s"', '            {', '                uniform token info:id = "UsdPreviewSurface"']
        if m['tex']: L.append(f'                color3f inputs:diffuseColor.connect = <{p}/tex.outputs:rgb>')
        else: L.append(f'                color3f inputs:diffuseColor = {f3(m["color"])}')
        L += [f'                float inputs:metallic = {m["metal"]}', f'                float inputs:roughness = {m["rough"]}',
              f'                float inputs:opacity = {m["opacity"]}', '                token outputs:surface', '            }', '        }']
    L += ['    }']
    for i, m in enumerate(MESHES):
        pos = m['pos']
        ext = [f3([min(v[k] for v in pos) for k in range(3)]), f3([max(v[k] for v in pos) for k in range(3)])]
        tris = [m['idx'][j:j + 3] for j in range(0, len(m['idx']), 3)]
        L += ['', f'    def Mesh "{m["name"]}_{i}" (', '        prepend apiSchemas = ["MaterialBindingAPI"]', '    )', '    {',
              f'        float3[] extent = [{ext[0]}, {ext[1]}]',
              f'        int[] faceVertexCounts = [{", ".join("3" for _ in tris)}]',
              f'        int[] faceVertexIndices = [{", ".join(str(k) for t in tris for k in t)}]',
              f'        rel material:binding = </Maquina/Mat/{m["mat"]}>',
              f'        normal3f[] normals = [{", ".join(f3(v) for v in m["nrm"])}] (', '            interpolation = "vertex"', '        )',
              f'        point3f[] points = [{", ".join(f3(v) for v in pos)}]',
              f'        texCoord2f[] primvars:st = [{", ".join(f3((u, 1 - v)) for u, v in m["uv"])}] (', '            interpolation = "vertex"', '        )',
              '        uniform token orientation = "rightHanded"', '        uniform token subdivisionScheme = "none"', '    }']
    L += ['}', '']
    os.makedirs(work, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    open(f'{work}/{base}.usda', 'w').write('\n'.join(L))
    subprocess.run(['usdcat', f'{base}.usda', '-o', f'{base}.usdc'], cwd=work, check=True)
    shutil.rmtree(f'{work}/textures', ignore_errors=True); shutil.copytree(texdir, f'{work}/textures')
    if os.path.exists(path): os.remove(path)
    texs = sorted(f'textures/{m["tex"]}' for m in MATS.values() if m['tex'])
    subprocess.run(['usdzip', os.path.abspath(path), f'{base}.usdc', *texs], cwd=work, check=True, capture_output=True)


if __name__ == '__main__':
    out = sys.argv[1]
    write_glb(f'{out}.glb', 'tex')
    write_usdz(f'{out}.usdz', 'tex', 'usdwork')
    print('ok', len(MESHES), 'malhas')
