
import chess, chess.engine
def analyse_chunk(args):
    path, depth, chunk = args
    eng = chess.engine.SimpleEngine.popen_uci(path)
    try:
        eng.configure({"Threads": 1, "Hash": 64})
    except Exception:
        pass
    lim = chess.engine.Limit(depth=depth)
    out = []
    for idx, fen, hm, mm in chunk:
        b = chess.Board(fen)
        try:
            info = eng.analyse(b, lim, multipv=2)
            sc = [i["score"].pov(b.turn).score(mate_score=10000) for i in info]
            roots = [chess.Move.from_uci(m) for m in sorted({hm, mm})]
            info2 = eng.analyse(b, lim, root_moves=roots, multipv=len(roots))
            vals = {i["pv"][0].uci(): i["score"].pov(b.turn).score(mate_score=10000) for i in info2}
            out.append((idx, sc[0], sc[1] if len(sc) > 1 else None, vals.get(hm), vals.get(mm)))
        except Exception:
            out.append((idx, None, None, None, None))
    eng.quit()
    return out
