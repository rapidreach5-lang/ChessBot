import os
import chess
import chess.svg
from stockfish import Stockfish
import streamlit as st

st.set_page_config(page_title="Chess Move Advisor", layout="wide")
st.title("Chess Best-Move & Analysis Bot")

# Automatically pick Linux Stockfish on Streamlit Cloud, or Windows .exe locally
if os.path.exists("/usr/games/stockfish"):
    STOCKFISH_PATH = "/usr/games/stockfish"
elif os.path.exists("/usr/bin/stockfish"):
    STOCKFISH_PATH = "/usr/bin/stockfish"
else:
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
        parameters={"Threads": 2, "Hash": 128},
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
        size=480,
    )
    st.image(board_svg)

with col2:
    st.