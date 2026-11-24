import chess
import chess.svg
from stockfish import Stockfish
import streamlit as st

st.set_page_config(page_title="Chess Move Advisor", layout="wide")
st.title("Chess Best-Move & Analysis Bot")

STOCKFISH_PATH = "./stockfish-windows-x86-64-universal.exe"

PIECE_NAMES = {
    chess.PAWN: "Pawn",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.ROOK: "Rook",
    chess.QUEEN: "Queen",
    chess.KING: "King",
}


def describe_move(board: chess.Board, move: chess.Move) -> str:
    san = board.san(move)
    if board.is_castling(move):
        side = "Kingside" if board.is_kingside_castling(move) else "Queenside"
        return f"Castle {side} ({san})"

    piece = board.piece_at(move.from_square)
    piece_name = PIECE_NAMES.get(piece.piece_type, "Piece") if piece else "Piece"
    target_square = chess.square_name(move.to_square)

    if board.is_capture(move):
        captured = board.piece_at(move.to_square)
        if board.is_en_passant(move):
            captured_name = "Pawn (en passant)"
        else:
            captured_name = PIECE_NAMES.get(captured.piece_type, "Piece") if captured else "Piece"
        return f"{piece_name} takes {captured_name} on {target_square} ({san})"

    return f"{piece_name} to {target_square} ({san})"


@st.cache_resource
def load_engine():
    return Stockfish(
        path=STOCKFISH_PATH,
        depth=10,
        parameters={"Threads": 4, "Hash": 128},
    )


stockfish = load_engine()

if "board" not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

with st.sidebar:
    st.header("Engine Settings")
    depth = st.slider("Analysis Depth", min_value=5, max_value=18, value=10)
    num_moves = st.slider("Top Moves to Show", min_value=1, max_value=5, value=3)

    if st.button("Reset Board"):
        st.session_state.board = chess.Board()
        st.rerun()

    st.divider()
    fen_input = st.text_input("Load custom FEN position:")
    if st.button("Load FEN") and fen_input:
        try:
            st.session_state.board = chess.Board(fen_input.strip())
            st.rerun()
        except ValueError:
            st.error("Invalid FEN string.")

# Run Stockfish analysis directly for the current board position
top_moves = []
best_move_obj = None

if not board.is_game_over():
    stockfish.set_depth(depth)
    stockfish.set_fen_position(board.fen())
    top_moves = stockfish.get_top_moves(num_moves)
    if top_moves:
        best_move_obj = chess.Move.from_uci(top_moves[0]["Move"])

col1, col2 = st.columns([1.2, 1])

with col1:
    arrows = []
    if best_move_obj is not None:
        arrows.append(
            chess.svg.Arrow(
                best_move_obj.from_square,
                best_move_obj.to_square,
                color="#00b050",
            )
        )

    last_move = board.peek() if board.move_stack else None
    board_svg = chess.svg.board(
        board=board,
        lastmove=last_move,
        arrows=arrows,
        size=479,
    )
    st.image(board_svg)

with col2:
    st.subheader("Pick & Play a Move")

    if board.is_game_over():
        st.warning(f"Game Over: {board.result()}")
    else:
        legal_moves = list(board.legal_moves)
        move_labels = {describe_move(board, m): m for m in legal_moves}
        sorted_labels = sorted(move_labels.keys())

        selected_label = st.selectbox(
            "Choose a legal move (no typing needed):",
            options=sorted_labels,
        )

        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("Play Selected", type="primary"):
                board.push(move_labels[selected_label])
                st.rerun()

        with btn_col2:
            if best_move_obj is not None and st.button("Play #1 Best"):
                board.push(best_move_obj)
                st.rerun()

        with btn_col3:
            if st.button("Undo Move") and board.move_stack:
                board.pop()
                st.rerun()

    st.divider()
    st.subheader("Best Moves Explained")

    if board.is_game_over():
        st.info("No more moves—the game has ended.")
    elif not top_moves:
        st.warning("Stockfish didn't return moves for this position. Try lowering Analysis Depth.")
    else:
        best = top_moves[0]
        if best.get("Mate") is not None:
            st.metric("Position Evaluation", f"Mate in {best['Mate']}")
        elif best.get("Centipawn") is not None:
            st.metric("Position Evaluation", f"{best['Centipawn'] / 100.0:+.2f}")

        for i, move_info in enumerate(top_moves, start=1):
            move_obj = chess.Move.from_uci(move_info["Move"])
            plain_desc = describe_move(board, move_obj)
            cp = move_info.get("Centipawn")
            mate = move_info.get("Mate")

            if mate is not None:
                score_text = f"Mate in {mate}"
            elif cp is not None:
                score_text = f"{cp / 100.0:+.2f}"
            else:
                score_text = "N/A"

            star = "⭐ " if i == 1 else ""
            st.write(f"{star}**#{i}: {plain_desc}** — Score: `{score_text}`")