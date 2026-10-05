"""
ROCKFALL BREAKTHROUGH  -  human vs minimax AI

Base game (Breakthrough, 6x6):
  - Each side has 2 rows of pawns.
  - A pawn moves 1 step forward (straight, onto an empty square)
    or 1 step diagonally forward (onto an empty square OR to capture).
  - First pawn to reach the opponent's back row wins.

NEW TWIST - Rockfall:
  - Every 4th move (counting both players), a rock falls on a square.
  - The square is shown in advance as 'x' (or a lowercase pawn if a pawn
    stands there and will be crushed).
  - Rocks are permanent walls. Pawns under a rock are destroyed.
  - The schedule is fixed for the whole game, so the AI can search it
    perfectly while a human has to keep track of it.

AI: minimax + alpha-beta pruning (the rockfall is simulated inside the search).

Run:  python rockfall_breakthrough.py
Move format: "b2 b3"  (from square, to square). Columns a-f, rows 1-6.
"""

import random

N = 6
EMPTY, HUMAN, AI, ROCK = ".", "W", "B", "#"
FALL_EVERY = 4
INF = 10 ** 9


# ---------- game rules ----------

def new_board():
    b = [[EMPTY] * N for _ in range(N)]
    for c in range(N):
        b[0][c] = b[1][c] = AI
        b[N - 2][c] = b[N - 1][c] = HUMAN
    return b


def direction(p):
    return 1 if p == AI else -1


def enemy(p):
    return HUMAN if p == AI else AI


def get_moves(b, p):
    d = direction(p)
    moves = []
    for r in range(N):
        for c in range(N):
            if b[r][c] != p:
                continue
            nr = r + d
            if not 0 <= nr < N:
                continue
            if b[nr][c] == EMPTY:
                moves.append((r, c, nr, c))
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < N and b[nr][nc] in (EMPTY, enemy(p)):
                    moves.append((r, c, nr, nc))
    return moves


def make_schedule(seed):
    rng = random.Random(seed)
    squares = [(r, c) for r in range(1, N - 1) for c in range(N)]
    rng.shuffle(squares)
    return squares[:10]


def next_rock(ply, schedule):
    """Square that will be hit at the next rockfall, and moves left until then."""
    sq = schedule[(ply // FALL_EVERY) % len(schedule)]
    return sq, FALL_EVERY - ply % FALL_EVERY


def apply_move(b, m, ply, schedule):
    nb = [row[:] for row in b]
    r, c, nr, nc = m
    nb[nr][nc] = nb[r][c]
    nb[r][c] = EMPTY
    ply += 1
    if ply % FALL_EVERY == 0:
        fr, fc = schedule[(ply // FALL_EVERY - 1) % len(schedule)]
        nb[fr][fc] = ROCK
    return nb, ply


def winner(b):
    if any(b[N - 1][c] == AI for c in range(N)):
        return AI
    if any(b[0][c] == HUMAN for c in range(N)):
        return HUMAN
    flat = [x for row in b for x in row]
    if AI not in flat:
        return HUMAN
    if HUMAN not in flat:
        return AI
    return None


# ---------- AI ----------

def evaluate(b):
    """Positive = good for the AI."""
    score = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == AI:
                score += 10 + r * r
            elif b[r][c] == HUMAN:
                score -= 10 + (N - 1 - r) ** 2
    return score


def order(b, moves, p):
    # captures first -> better alpha-beta pruning
    return sorted(moves, key=lambda m: b[m[2]][m[3]] == enemy(p), reverse=True)


def alphabeta(b, ply, depth, alpha, beta, player, sch):
    w = winner(b)
    if w:
        return (10000 + depth) if w == AI else -(10000 + depth)
    if depth == 0:
        return evaluate(b)
    moves = get_moves(b, player)
    if not moves:  # no legal move = loss
        return -10000 if player == AI else 10000
    moves = order(b, moves, player)
    if player == AI:
        best = -INF
        for m in moves:
            nb, nply = apply_move(b, m, ply, sch)
            best = max(best, alphabeta(nb, nply, depth - 1, alpha, beta, HUMAN, sch))
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    best = INF
    for m in moves:
        nb, nply = apply_move(b, m, ply, sch)
        best = min(best, alphabeta(nb, nply, depth - 1, alpha, beta, AI, sch))
        beta = min(beta, best)
        if alpha >= beta:
            break
    return best


def ai_move(b, ply, depth, sch):
    best_val, best_move = -INF, None
    for m in order(b, get_moves(b, AI), AI):
        nb, nply = apply_move(b, m, ply, sch)
        v = alphabeta(nb, nply, depth - 1, -INF, INF, HUMAN, sch)
        if v > best_val:
            best_val, best_move = v, m
    return best_move


# ---------- interface ----------

def sq_name(r, c):
    return chr(97 + c) + str(N - r)


def show(b, ply, sch):
    (fr, fc), left = next_rock(ply, sch)
    print("\n    " + " ".join("abcdef"[:N]))
    for r in range(N):
        cells = []
        for c in range(N):
            ch = b[r][c]
            if (r, c) == (fr, fc):
                ch = "x" if ch == EMPTY else ch.lower()
            cells.append(ch)
        print(f" {N - r}  " + " ".join(cells))
    print(f"\nRock hits {sq_name(fr, fc)} in {left} move(s).  "
          f"(x = incoming rock, lowercase = pawn about to be crushed)")


def parse(text):
    parts = text.split()
    if len(parts) != 2:
        return None
    try:
        c1, r1 = ord(parts[0][0]) - 97, N - int(parts[0][1:])
        c2, r2 = ord(parts[1][0]) - 97, N - int(parts[1][1:])
    except ValueError:
        return None
    return (r1, c1, r2, c2)


def main():
    print(__doc__)
    levels = {"1": 2, "2": 4, "3": 5}
    choice = input("Difficulty - 1 easy, 2 medium, 3 hard: ").strip()
    depth = levels.get(choice, 4)
    sch = make_schedule(random.randint(0, 10 ** 6))

    board, ply = new_board(), 0
    turn = HUMAN  # you are W (bottom), you move first

    while True:
        w = winner(board)
        if w:
            show(board, ply, sch)
            print("\nYou win!" if w == HUMAN else "\nThe AI wins!")
            return
        if not get_moves(board, turn):
            print("\nNo legal moves left. " + ("The AI wins!" if turn == HUMAN else "You win!"))
            return

        show(board, ply, sch)
        if turn == HUMAN:
            legal = get_moves(board, HUMAN)
            m = parse(input("\nYour move (e.g. b2 b3): ").strip().lower())
            if m not in legal:
                print("Illegal move, try again.")
                continue
        else:
            print("\nAI is thinking...")
            m = ai_move(board, ply, depth, sch)
            print(f"AI plays {sq_name(m[0], m[1])} -> {sq_name(m[2], m[3])}")

        board, ply = apply_move(board, m, ply, sch)
        if ply % FALL_EVERY == 0:
            fr, fc = sch[(ply // FALL_EVERY - 1) % len(sch)]
            print(f">>> A rock fell on {sq_name(fr, fc)}!")
        turn = enemy(turn)


if __name__ == "__main__":
    main()