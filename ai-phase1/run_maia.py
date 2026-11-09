"""Run Maia 2 on the human only pair's dataset and save moves_maia_2024-06.parquet into ai-phase1/data/.
Code copied from non-ai-phase1/code-phase1.ipynb so both pairs use identical predictions.
Run: python ai-phase1/run_maia.py
"""
import sys
import numpy as np
import pandas as pd
import torch
import chess
from pathlib import Path
from tqdm.auto import tqdm
from maia2 import model as maia_model
from maia2.inference import prepare
from maia2.utils import mirror_move, board_to_tensor, map_to_category

MONTH = "2024-06"
IN_FILE = Path(__file__).resolve().parent.parent / "non-ai-phase1" / "data" / f"moves_{MONTH}.parquet"
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
BATCH_SIZE = 512
NUM_WORKERS = 0
MAX_POSITIONS = int(sys.argv[1]) if len(sys.argv) > 1 else None
SEED = 42

moves = pd.read_parquet(IN_FILE)
if MAX_POSITIONS is not None and len(moves) > MAX_POSITIONS:
    gids = moves["game_id"].drop_duplicates().sample(frac=1, random_state=SEED)
    sizes = moves.groupby("game_id").size().loc[gids].cumsum()
    moves = moves[moves["game_id"].isin(sizes[sizes <= MAX_POSITIONS].index)].reset_index(drop=True)
print(moves.shape)

device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
nets = {tc: maia_model.from_pretrained(type=tc, device=device) for tc in ("blitz", "rapid")}
all_moves_dict, elo_dict, all_moves_dict_reversed = prepare()
print(device, len(all_moves_dict), list(elo_dict.keys()))


class MaiaPositions(torch.utils.data.Dataset):
    def __init__(self, fens, elo_self, elo_oppo):
        self.fens = list(fens)
        self.elo_self = [int(e) for e in elo_self]
        self.elo_oppo = [int(e) for e in elo_oppo]

    def __len__(self):
        return len(self.fens)

    def __getitem__(self, i):
        board = chess.Board(self.fens[i])
        if board.turn == chess.BLACK:
            board = board.mirror()
        legal = torch.zeros(len(all_moves_dict))
        legal[[all_moves_dict[m.uci()] for m in board.legal_moves]] = 1
        return (board_to_tensor(board), map_to_category(self.elo_self[i], elo_dict),
                map_to_category(self.elo_oppo[i], elo_dict), legal)


def run_maia(df, net, batch_size=BATCH_SIZE):
    data = df[["fen", "move", "elo_self", "elo_oppo"]].reset_index(drop=True)
    is_black = data["fen"].str.split(" ").str[1].eq("b").to_numpy()
    true_moves = [mirror_move(m) if b else m for m, b in zip(data["move"], is_black)]
    true_idx = np.array([all_moves_dict.get(m, -1) for m in true_moves])
    if (true_idx < 0).any():
        raise ValueError(f"{(true_idx < 0).sum()} moves not in Maia vocabulary")
    loader = torch.utils.data.DataLoader(MaiaPositions(data["fen"], data["elo_self"], data["elo_oppo"]),
                                         batch_size=batch_size, shuffle=False, num_workers=NUM_WORKERS)
    dev = next(net.parameters()).device
    net.eval()
    buf = {key: [] for key in ("topk_idx", "topk_p", "p_true", "rank", "entropy", "n_legal", "value")}
    offset = 0
    with torch.no_grad():
        for boards, e_self, e_oppo, legal in tqdm(loader):
            boards, e_self, e_oppo = boards.to(dev), e_self.to(dev), e_oppo.to(dev)
            legal = legal.to(dev).bool()
            logits, _, value = net(boards, e_self, e_oppo)
            probs = logits.masked_fill(~legal, float("-inf")).softmax(-1)
            n = probs.shape[0]
            t = torch.as_tensor(true_idx[offset:offset + n], device=dev).unsqueeze(1)
            p_true = probs.gather(1, t).squeeze(1)
            topk_p, topk_idx = probs.topk(5, dim=1)
            buf["topk_idx"].append(topk_idx.cpu().numpy())
            buf["topk_p"].append(topk_p.cpu().numpy())
            buf["p_true"].append(p_true.cpu().numpy())
            buf["rank"].append(((probs > p_true.unsqueeze(1)).sum(1) + 1).cpu().numpy())
            buf["entropy"].append((-(probs * torch.log(probs.clamp_min(1e-12))).sum(1)).cpu().numpy())
            buf["n_legal"].append(legal.sum(1).cpu().numpy())
            buf["value"].append((value.reshape(-1) / 2 + 0.5).clamp(0, 1).cpu().numpy())
            offset += n
    r = {key: np.concatenate(v) for key, v in buf.items()}
    rev = all_moves_dict_reversed
    top_moves, top_probs = [], []
    for row_i, row_p, b in zip(r["topk_idx"], r["topk_p"], is_black):
        mv = [mirror_move(rev[i]) if b else rev[i] for i, p in zip(row_i, row_p) if p > 0]
        top_moves.append(mv)
        top_probs.append(row_p[:len(mv)].round(5).tolist())
    n_legal = r["n_legal"]
    out = pd.DataFrame({
        "maia_move": [m[0] for m in top_moves],
        "maia_p_top1": r["topk_p"][:, 0],
        "maia_p_true": r["p_true"],
        "maia_rank_true": r["rank"],
        "maia_entropy": r["entropy"],
        "maia_entropy_norm": np.where(n_legal > 1, r["entropy"] / np.log(np.maximum(n_legal, 2)), 0.0),
        "maia_value_mover": r["value"],
        "maia_top5_moves": top_moves,
        "maia_top5_probs": top_probs,
    }, index=df.index)
    out["maia_correct"] = out["maia_move"].to_numpy() == df["move"].to_numpy()
    out["maia_top3_hit"] = out["maia_rank_true"] <= 3
    out["maia_top5_hit"] = out["maia_rank_true"] <= 5
    return out


parts = [run_maia(moves[moves["time_control_type"] == tc], net)
         for tc, net in nets.items() if (moves["time_control_type"] == tc).any()]
preds = pd.concat(parts).sort_index()
moves = moves.drop(columns=[c for c in preds.columns if c in moves.columns]).join(preds)
print(moves.shape)

elo_bins = [-np.inf] + list(range(1100, 2001, 100)) + [np.inf]
elo_labels = list(elo_dict.keys())
moves["maia_elo_cat_self"] = pd.cut(moves["elo_self"], elo_bins, right=False, labels=elo_labels).astype(str)
moves["maia_elo_cat_oppo"] = pd.cut(moves["elo_oppo"], elo_bins, right=False, labels=elo_labels).astype(str)
moves["maia_failed"] = ~moves["maia_correct"]
moves.to_parquet(DATA_DIR / f"moves_maia_{MONTH}.parquet", index=False)
print("saved", DATA_DIR / f"moves_maia_{MONTH}.parquet")
