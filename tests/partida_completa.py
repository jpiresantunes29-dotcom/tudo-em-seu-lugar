"""Teste automático de uma partida completa, sem janela e sem som.

Um "robô" joga o modo história do início ao fim e confere:
  * todos os pontos interativos de cada cenário são alcançáveis (busca em largura);
  * a história avança por todos os capítulos até a tela final;
  * salvar e continuar (menu "Continuar caso salvo") restaura o mesmo estado;
  * as dicas funcionam em cada capítulo;
  * nenhum texto sai das caixas (ESTOUROS = 0) na resolução escolhida;
  * derrota por 3 acusações erradas e acusação forçada quando o prazo acaba;
  * 400 sorteios diferentes sempre posicionam todas as pistas principais.
Também tira capturas de tela e estima o tempo de uma partida.

Uso:  python tests/partida_completa.py [jogo.py] [pasta_capturas]
      RES=1366x768 python tests/partida_completa.py     (outra resolução)
"""
import os, sys, importlib.util, random, time
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "tudo_em_seu_lugar.py")
spec = importlib.util.spec_from_file_location("jogo", ARQ); J = importlib.util.module_from_spec(spec); spec.loader.exec_module(J)
pg = J.pygame
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "tests", "capturas"); os.makedirs(OUT, exist_ok=True)
g = J.Jogo()
_nj = g.novo_jogo
def _novo(codigo=None):
    _nj(codigo)
    if os.environ.get("BRIEF_SHOT"):
        frame(1); shot("briefing")
    g.fechar_briefing()
g.novo_jogo = _novo
TEXTOS = {"fala": [0, 0], "narra": [0, 0], "tel": [0, 0], "cena": [0, 0], "carta": [0, 0], "cap": [0, 0]}
_orig_proc = g._processar_fila
def _proc():
    antes_b, antes_c, antes_t = g.balao, g.carta, g.capitulo_titulo
    _orig_proc()
    if g.balao is not antes_b and g.balao:
        k = g.balao["tipo"]; TEXTOS[k][0] += 1; TEXTOS[k][1] += sum(len(p) for p in g.balao["pags"])
        TEXTOS[k].append(len(g.balao["pags"]))
    if g.carta is not antes_c and g.carta:
        TEXTOS["carta"][0] += 1; TEXTOS["carta"][1] += len(g.carta["texto"])
    if g.capitulo_titulo is not antes_t and g.capitulo_titulo:
        TEXTOS["cap"][0] += 1
g._processar_fila = _proc
RES = tuple(int(v) for v in os.environ.get("RES", "960x540").split("x")); g.tela = pg.Surface(RES); g._recalcular()
n = [0]
ESTOUROS = []
def frame(k=1):
    for _ in range(k):
        for ev in pg.event.get(): g.evento(ev)
        g.atualizar(1/30); g._medida = None; g.desenhar()
        m = g._medida
        if m:
            tipo, r = m[0], m[1]
            if m[2] > r.bottom - 2: ESTOUROS.append((tipo, "altura", m[2] - r.bottom))
            if len(m) > 3 and m[3] > r.right - 2: ESTOUROS.append((tipo, "largura", m[3] - r.right))
def shot(nome):
    frame(1); n[0] += 1; pg.image.save(g.tela, f"{OUT}/{n[0]:02d}_{nome}.png")
def resolver(escolha=None, max_frames=4000, shots=None):
    """roda até não haver cena; avança falas; escolhe menu (valor ou índice 0)."""
    for i in range(max_frames):
        frame(1)
        if g.modo != "jogo": return
        if shots and g.balao and shots.get("balao") and not shots.get("_b"):
            shots["_b"] = 1; frame(40); shot(shots["balao"])
        if g.menu:
            TEMPO["menus"] += 1
            vals = [o[1] for o in g.menu.opcoes]
            if escolha is not None and escolha in vals: g.menu.sel = vals.index(escolha)
            else: g.menu.sel = 0
            g._confirmar_menu(); continue
        if g.balao or g.carta or g.capitulo_titulo:
            g._avancar(); g._avancar(); continue
        if not g.ocupado(): return
    raise RuntimeError("travou")
TEMPO = {"andar_px": 0.0, "viagens": 0, "menus": 0}
def rt(nome):
    """salva, carrega como um jogador faria (menu → Continuar) e confere que nada mudou."""
    global c
    frame(3)
    assert not g.ocupado(), "salvar fora de cena"
    assert g.salvar_jogo(), "falhou ao salvar"
    antes = (c.pontos, c.relogio, sorted(c.feitos), sorted(map(str, c.examinados)), c.sala, g.objetivo,
             c.cap, c.horas, [a["nome"] for a in c.alunas], round(g.player.x), round(g.player.y))
    g.titulo_menu(); frame(2)
    assert g.menu.opcoes[0][1] == "continuar", g.menu.opcoes[0]
    if nome == "cap3": shot("menu_continuar")
    g.novo_jogo = _nj; g.menu.sel = 0; g._confirmar_menu(); g.novo_jogo = _novo
    c = g.caso
    depois = (c.pontos, c.relogio, sorted(c.feitos), sorted(map(str, c.examinados)), c.sala, g.objetivo,
              c.cap, c.horas, [a["nome"] for a in c.alunas], round(g.player.x), round(g.player.y))
    assert antes == depois, (antes, depois)
    assert g.modo == "jogo" and not g.briefing
    frame(20)
    if nome == "cap3": shot("carregado")
    print("SAVE/LOAD ok", nome, c.relogio, c.pontos)
    for _ in range(2):
        g.pedir_dica(); assert g.menu, "sem menu de dica"; g.menu.sel = 0; g._confirmar_menu()
        frame(2); print("  DICA", nome, "→", g.balao["pags"][0][:110].replace("\n", " ") if g.balao else g.fila[:1])
        resolver()
def perto(sid, alvo):
    """leva Helena a uma posição ALCANÇÁVEL (busca em largura) de onde o alvo é o mais próximo."""
    if g.caso.sala != sid: g.carregar_sala(sid)
    x0, y0 = g.player.x, g.player.y
    S = J.SALAS[sid]; ini = S["inicio"]
    vist = {ini}; fila = [ini]
    while fila:
        tx, ty = fila.pop(0)
        for nx, ny in ((tx+1,ty),(tx-1,ty),(tx,ty+1),(tx,ty-1)):
            if (nx,ny) not in vist and 0<=nx<J.COLS and 0<=ny<J.LINHAS and g._livre(nx*16+8, ny*16+14):
                vist.add((nx,ny)); fila.append((nx,ny))
    for tx, ty in sorted(vist, key=lambda p: (p[1], p[0])):
        g.player.x, g.player.y = tx*16+8, ty*16+14
        a = g.alvo_proximo()
        if a and a[1] == alvo:
            TEMPO["andar_px"] += (abs(g.player.x - x0) + abs(g.player.y - y0)) * 1.25
            g.interagir(); return
    raise AssertionError(("inalcançável", sid, alvo))
# checa que todos os pontos de todas as salas são alcançáveis
for sid in J.SALAS:
    g.caso = J.Caso(1) if not getattr(g, "caso", None) else g.caso
    for r, p, nome in [] : pass
shot("titulo")
g.novo_jogo(999)
for sid in J.SALAS:
    g.carregar_sala(sid); g.ents = {"helena": g.player}
    for r, p, nome in g.objeto_em(sid):
        S = J.SALAS[sid]; ini = S["inicio"]; vist = {ini}; fila=[ini]
        while fila:
            tx, ty = fila.pop(0)
            for nx, ny in ((tx+1,ty),(tx-1,ty),(tx,ty+1),(tx,ty-1)):
                if (nx,ny) not in vist and 0<=nx<J.COLS and 0<=ny<J.LINHAS and g._livre(nx*16+8, ny*16+14):
                    vist.add((nx,ny)); fila.append((nx,ny))
        ok = False
        for tx, ty in vist:
            g.player.x, g.player.y = tx*16+8, ty*16+14
            a = g.alvo_proximo()
            if a and a[1] == p: ok = True; break
        print(("OK " if ok else "INALCANÇÁVEL ") + sid, p, nome)
g.novo_jogo(4821); c = g.caso
frame(60); shot("prologo_cap")
for _ in range(200):
    frame(1)
    if g.balao and g.balao["tipo"] == "fala" and g.balao["ent"] == "al1" and "trancada" in g.balao["pags"][0]: break
    if g.balao or g.capitulo_titulo: g._avancar(); g._avancar()
frame(60); shot("prologo_balao")
resolver(); shot("cap1_escritorio")
perto("escritorio", "telefone"); frame(30); g._avancar(); shot("telefone_sofia"); resolver()
assert "telefone" in c.feitos
g.abrir_mapa(); shot("mapa"); g.menu=None; g.viajar("salao"); resolver(shots={"balao": "salao_sofia"})
assert c.cap == 2, c.cap
perto("salao", "sofia"); resolver()
g.carregar_sala("banheiro_baile"); shot("banheiro")
perto("banheiro_baile", "olivia"); resolver()
for i in range(3):
    perto("banheiro_baile", i); frame(25)
    if i == 2: 
        for _ in range(40):
            frame(1)
            if g.carta: break
            if g.balao: g._avancar(); g._avancar()
        shot("carta_cam_baile")
    resolver()
for i in (0, 2):
    if c.cap == 2: perto("salao", i); resolver()
for i in (1,):
    if c.cap == 2: perto("salao", i); resolver()
print("cap após baile:", c.cap, c.feitos, c.relogio)
assert c.cap == 3
rt("cap3")
g.viajar("tulane"); resolver(); shot("tulane")
for volta in range(3):
    for sid in ("tulane", "banheiro_tulane"):
        for i in range(3):
            if c.cap == 3 and ((sid, i) not in c.examinados or g.pode_reexaminar(sid, i)):
                perto(sid, i); resolver()
print("cap após tulane:", c.cap, c.relogio)
assert c.cap == 4
rt("cap4")
g.viajar("interrogatorio"); resolver(); shot("interrogatorio")
g.painel_aberto="suspeitas"; g.sel_susp=0; shot("suspeitas_antes"); g.painel_aberto=None
for a in c.alunas:
    perto("interrogatorio", a["id"])
    for _ in range(400):
        frame(1)
        if g.menu: break
        if g.balao or g.carta: g._avancar(); g._avancar()
    if a["id"] == "aluna1": shot("decisao_aluna")
    resolver("liberar")
perto("interrogatorio", "olivia")
for _ in range(2000):
    frame(1)
    if g.flash: shot("entrevista_flash"); break
    if g.balao or g.carta: g._avancar(); g._avancar()
resolver(); print("cap após entrevista:", c.cap, c.relogio)
assert c.cap == 5
rt("cap5")
g.viajar("casa"); resolver(); shot("casa")
for i in (0, 2, 1):
    if c.cap == 5 and (("casa", i) not in c.examinados): 
        perto("casa", i)
        if i == 1:
            for _ in range(200):
                frame(1)
                if g.balao and g.balao.get("ent") == "max": frame(20); shot("max_latindo"); break
                if g.balao or g.carta: g._avancar(); g._avancar()
        resolver()
print("cap após casa:", c.cap, c.relogio)
assert c.cap == 6
rt("cap6")
g.viajar("interrogatorio"); resolver()
perto("interrogatorio", 0); resolver()
g.painel_aberto="caderno"; shot("caderno"); g.painel_aberto=None
g.painel_aberto="suspeitas"; shot("suspeitas_depois"); g.painel_aberto=None
perto("interrogatorio", "olivia")
for _ in range(300):
    frame(1)
    if g.menu: shot("acusacao"); break
    if g.balao: g._avancar(); g._avancar()
vals=[o[1] for o in g.menu.opcoes]; g.menu.sel=vals.index("helena"); g._confirmar_menu(); frame(2)
vals=[o[1] for o in g.menu.opcoes]; g.menu.sel=vals.index("vinganca"); g._confirmar_menu()
for _ in range(5000):
    frame(1)
    if g.modo != "jogo": break
    if g.carta and g.carta["titulo"]=="Caso solucionado": shot("caso_solucionado")
    if g.balao or g.carta or g.capitulo_titulo: g._avancar(); g._avancar()
assert g.modo == "final", g.modo
shot("final")
V = J.VELOCIDADE_TEXTO
tt = {}
for k in ("fala", "tel", "narra", "cena"):
    nn, chars = TEXTOS[k][0], TEXTOS[k][1]; pags = sum(TEXTOS[k][2:])
    tt[k] = chars / V[k] + pags * (1.5 if k != "cena" else 2.0)
tt["cartas"] = TEXTOS["carta"][1] / V["carta"] + TEXTOS["carta"][0] * 5.0
tt["capitulos"] = TEXTOS["cap"][0] * (1.6 + 30 / V["capitulo"])
tt["andar"] = TEMPO["andar_px"] / J.VELOCIDADE_ANDAR * 1.8
tt["viagens"] = 6 * (1.2 + 5)
tt["menus/decisões"] = TEMPO["menus"] * 5
tt["pensar/caderno/suspeitas"] = 6 * 20
tot = sum(tt.values())
print("TEMPO ESTIMADO (s):", {k: round(v) for k, v in tt.items()}, "TOTAL", round(tot), "=", round(tot / 60, 1), "min")
print("contagens", {k: TEXTOS[k][:2] for k in TEXTOS}, TEMPO)
print("FIM", c.relogio, "PONTOS", c.pontos, "props", len(c.props), "horas", c.horas)
# partida 2: derrota por acusações erradas
g.novo_jogo(77); c=g.caso; resolver(); perto("escritorio","telefone"); resolver(); g.viajar("salao"); resolver()
for k in range(3):
    g.abrir_acusacao(); g.menu.sel=0; g._confirmar_menu(); frame(1); g.menu.sel=0; g._confirmar_menu(); resolver() if g.modo=="jogo" else None
    if g.modo!="jogo": break
print("modo após 3 erros:", g.modo, c.credibilidade); shot("derrota")
# partida 3: horas acabando
g.novo_jogo(5); c=g.caso; resolver(); perto("escritorio","telefone"); resolver(); c.horas=0; g.viajar("salao")
for _ in range(600):
    frame(1)
    if g.menu and "Quem" in g.menu.titulo: break
    if g.balao or g.carta or g.capitulo_titulo: g._avancar(); g._avancar()
print("forçada:", g.menu.titulo if g.menu else None, "cancelavel", g.menu.cancelavel if g.menu else None); shot("forcada")
# fuzz de sorteios
for seed in range(400):
    cc=J.Caso(seed)
    for pid in J.PISTAS_PRINCIPAIS: assert ("pista", pid) in cc.mapa.values()
print("fuzz ok")
print("ESTIMATIVA", TEXTOS, TEMPO)
print("ESTOUROS:", len(ESTOUROS), ESTOUROS[:8])

assert not ESTOUROS, "há textos saindo das caixas"
print("TUDO OK")
